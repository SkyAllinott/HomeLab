from fastapi import APIRouter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import httpx
from datetime import datetime, timedelta
import pytz
import os

router = APIRouter()

# Timezone information
TZ = os.environ.get("TIMEZONE").strip()
if TZ not in pytz.all_timezones:
    raise ValueError('Invalid time zone selection')
MT = pytz.timezone(TZ)
UTC = pytz.utc

@router.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())

# Convert to timezone function
def convert_to_mt(date_str, time_str):
    if not date_str or not time_str:
        return None
    dt_utc = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M:%SZ")
    dt_utc = UTC.localize(dt_utc)
    return dt_utc.astimezone(MT)

@router.get("/", summary="Fetch next race")
async def get_next_race():
    cache = FastAPICache.get_backend()
    cache_key = "f1:next_race"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        try:
            # Get data from current season
            response = await client.get("https://f1api.dev/api/" + str(datetime.now().year))
            if response.status_code != 200:
                return {"error": "Failed to fetch race schedule"}
            calendar_data = response.json()
        except Exception as e:
            return {"error": f"Exception while fetching: {e}"}

    now = datetime.utcnow().date()
    races = sorted(calendar_data.get("races", []), key=lambda r: r.get("schedule", {}).get("race", {}).get("date", ""))

    # Loop through list in order until find first race with date past today. 
    next_race = None
    for race in races:
        race_date_str = race.get("schedule", {}).get("race", {}).get("date")
        if not race_date_str:
            continue
        race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
        if race_date > now:
            next_race = race
            break

    if not next_race:
        return {"message": "No upcoming race found"}

    # Convert schedule times
    schedule = next_race.get("schedule", {})
    for session, val in schedule.items():
        if val["date"] and val["time"]:
            dt_mt = convert_to_mt(val["date"], val["time"])
            val["date"] = dt_mt.strftime("%Y-%m-%d")
            val["time"] = dt_mt.strftime("%H:%M:%S")
            val["datetime_rfc3339"] = dt_mt.isoformat()

    # Clean up race name
    race_name = next_race.get("raceName")
    if race_name:
        year = calendar_data.get("season")
        next_race["raceName"] = race_name.replace(str(year), "").strip()

    # Circuit processing
    circuit = next_race.get("circuit", {})
    if "circuitLength" in circuit:
        try:
            raw_length = int(circuit["circuitLength"].replace("km", "").strip())
            circuit["circuitLengthKm"] = raw_length / 1000.0
        except Exception:
            circuit["circuitLengthKm"] = None

    # Fastest driver name formatting
    fastest_driver_id = circuit.get("fastestLapDriverId")
    if fastest_driver_id:
        name_parts = fastest_driver_id.replace("_", " ").split(" ")
        circuit["fastestLapDriverName"] = name_parts[-1].capitalize()

    # Correct laptime formatting 
    fastest_lap_time = circuit.get("lapRecord")
    if fastest_lap_time:
        circuit["lapRecord"] = ".".join(fastest_lap_time.rsplit(":", 1))

    # Compute total distance
    laps = next_race.get("laps")
    if laps and circuit.get("circuitLengthKm") is not None:
        next_race["totalDistanceKm"] = round(laps * circuit["circuitLengthKm"], 2)
    else:
        next_race["totalDistanceKm"] = None

    # Cache expiry logic based on race time
    try:
        race_dt_str = schedule.get("race", {}).get("datetime_rfc3339")
        if race_dt_str:
            race_dt = datetime.fromisoformat(race_dt_str).astimezone(MT)
            expire = int((race_dt + timedelta(hours=4) - datetime.now(MT)).total_seconds())
        else:
            expire = 3600  # fallback
    except Exception as e:
        print("Cache expiry fallback due to error:", e)
        expire = 3600

    response_data = {
        "season": calendar_data.get("season"),
        "timezone": TZ,
        "race": [next_race]
    }

    await cache.set(cache_key, response_data, expire=expire)
    return response_data
