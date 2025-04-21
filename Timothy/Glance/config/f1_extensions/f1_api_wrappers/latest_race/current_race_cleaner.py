from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.coder import JsonCoder
import httpx
from datetime import datetime, timedelta
import pytz

app = FastAPI()

MT = pytz.timezone("America/Edmonton")
UTC = pytz.utc

@app.on_event("startup")

# Initialize memory caching
async def startup():
    FastAPICache.init(InMemoryBackend())

def convert_to_mt(date_str, time_str):
    if not date_str or not time_str:
        return None
    dt_utc = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M:%SZ")
    dt_utc = UTC.localize(dt_utc)
    return dt_utc.astimezone(MT)

@app.get("/f1/last")
async def get_last_race():
    cache_key = "f1:last_race"
    cache = FastAPICache.get_backend()
    coder = JsonCoder()

    # See if cache exists
    cached = await cache.get(cache_key)

    if cached:
        # Extract race time from cache
        try:
            race_schedule = cached["race"][0]["schedule"]
            race_date = race_schedule["race"]["date"]
            race_time = race_schedule["race"]["time"]
            race_dt = convert_to_mt(race_date, race_time)

            now = datetime.now(MT)
            if now < race_dt + timedelta(hours=4):  # idk when API refreshes, 4 hours after?
                return cached
        except Exception as e:
            print(f"Cache check error, refetching: {e}")

    # If cache needs to update:
    async with httpx.AsyncClient() as client:
        r = await client.get("https://f1api.dev/api/current/next")
        data = r.json()

    for race in data.get("race", []):
        schedule = race.get("schedule", {})
        for session, val in schedule.items():
            if val["date"] and val["time"]:
                dt_mt = convert_to_mt(val["date"], val["time"])
                val["date"] = dt_mt.strftime("%Y-%m-%d")
                val["time"] = dt_mt.strftime("%H:%M:%S")
                val["datetime_rfc3339"] = dt_mt.isoformat()

        race_name = race.get("raceName")
        if race_name:
            year = data.get("season")
            race["raceName"] = race["raceName"].replace(str(year), "").strip()

        circuit = race.get("circuit", {})
        if "circuitLength" in circuit:
            try:
                raw_length = int(circuit["circuitLength"].replace("km", "").strip())
                circuit["circuitLengthKm"] = raw_length / 1000.0
            except Exception:
                circuit["circuitLengthKm"] = None

        fastest_driver_id = circuit.get("fastestLapDriverId")
        if fastest_driver_id:
            name_parts = fastest_driver_id.replace("_", " ").split(" ")
            circuit["fastestLapDriverName"] = name_parts[-1].capitalize()

        fastest_lap_time = circuit.get("lapRecord")
        if fastest_lap_time:
            circuit["lapRecord"] = fastest_lap_time.replace(":", ".", 1)

        laps = race.get("laps")
        if laps and circuit.get("circuitLengthKm") is not None:
            race["totalDistanceKm"] = round(laps * circuit["circuitLengthKm"], 2)
        else:
            race["totalDistanceKm"] = None

    # Cache the result
    # Refresh every 7 days in case something breaks cause it probably will
    await cache.set(cache_key, data, expire=604800)
    return data
