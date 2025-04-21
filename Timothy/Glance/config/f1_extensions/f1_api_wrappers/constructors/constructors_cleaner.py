from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import pycountry
import httpx
from datetime import datetime, timedelta
import pytz

app = FastAPI()

MT = pytz.timezone("America/Edmonton")

# Initialize caching
@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())

def country_to_code(country_name: str) -> str:
    replacements = {
        "Great Britain": "GB",
        "United States": "US",
    }
    try:
        country_name = replacements.get(country_name, country_name)
        return pycountry.countries.lookup(country_name).alpha_2.lower()
    except Exception:
        return ""

async def get_next_race_end():
    async with httpx.AsyncClient() as client:
        try:
	   # Use f1_latest API to fetch race time for smart caching
            r = await client.get("http://192.168.0.80:4463/f1/last")
            data = r.json()
            race = data.get("race", [])[0]
            schedule = race.get("schedule", {})
            race_dt_str = schedule.get("race", {}).get("datetime_rfc3339")

            if race_dt_str:
                race_dt = datetime.fromisoformat(race_dt_str)
                race_dt = race_dt.astimezone(MT)
		# Refresh cache 4 hours after race start, idk when refreshes, may need adjustment
                return race_dt + timedelta(hours=4)
        except Exception as e:
            print("Error fetching race time:", e)
    return None

@app.get("/constructors_championship")
async def get_constructors_championship():
    cache = FastAPICache.get_backend()
    cache_key = "constructors_championship"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        response = await client.get("https://f1api.dev/api/current/constructors-championship")
        if response.status_code != 200:
            return {"error": "Failed to fetch data"}

        data = response.json()

    constructors = data.get("constructors_championship", [])
    results = []
    for entry in constructors:
        team = entry.get("team", {})
        country = team.get("country", "")
        results.append({
            "team": team.get("teamName"),
            "position": entry.get("position"),
            "points": entry.get("points"),
            "wins": entry.get("wins") or 0,
            "country": country,
            "flag": country_to_code(country),
            "wiki": team.get("url")
        })

    response_data = {"season": data.get("season"), "constructors": results}

    # Cache until race ends or 1 hour (in case f1/last is down or something
    race_end = await get_next_race_end()
    expire = int((race_end - datetime.now(MT)).total_seconds()) if race_end else 3600

    await cache.set(cache_key, response_data, expire=expire)
    return response_data
