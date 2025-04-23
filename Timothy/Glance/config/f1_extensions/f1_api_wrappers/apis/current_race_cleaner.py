from fastapi import APIRouter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import httpx
from datetime import datetime, timedelta
import pytz

router = APIRouter()

MT = pytz.timezone("America/Edmonton")
UTC = pytz.utc

# Initialize memory caching
@router.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())

def convert_to_mt(date_str, time_str):
    if not date_str or not time_str:
        return None
    dt_utc = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M:%SZ")
    dt_utc = UTC.localize(dt_utc)
    return dt_utc.astimezone(MT)

@router.get("/", summary="Fetch next race")
async def get_last_race():
    cache_key = "f1:last_race"
    cache = FastAPICache.get_backend()

    # Try cache
    cached = await cache.get(cache_key)
    if cached:
        return cached

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

    # Calculate when cache should disappear
    try:
        first_race = data.get("race", [])[0]
        schedule = first_race.get("schedule", {})
        race_dt_str = schedule.get("race", {}).get("datetime_rfc3339")
        if race_dt_str:
            race_dt = datetime.fromisoformat(race_dt_str)
            race_dt = race_dt.astimezone(MT)
            expire = int((race_dt + timedelta(hours=4) - datetime.now(MT)).total_seconds())
        else:
            expire = 3600  # fallback to 1 hour if can't fetch race date for any reason
    except Exception as e:
        print("Failed to determine cache expiry:", e)
        expire = 3600

    await cache.set(cache_key, data, expire=expire)
    return data
