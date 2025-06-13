from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
import httpx
import io
from datetime import datetime, timedelta
import pytz
import os

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from .map_generator import generate_track_map_svg

router = APIRouter()

LAST_RACE_API_URL = "http://localhost:4463/f1/next_race/"

MT = pytz.timezone("America/Edmonton")
UTC = pytz.utc

@router.on_event("startup")
# Initialize caching
async def startup():
    FastAPICache.init(InMemoryBackend())

@router.get("/", summary="Fetch next track map")
async def get_dynamic_track_map():
    cache_key = "track_map_svg"
    cache = FastAPICache.get_backend()

    # Try cached version
    svg_content = await cache.get(cache_key)
    if svg_content:
        return Response(content=svg_content, media_type="image/svg+xml")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(LAST_RACE_API_URL)
            resp.raise_for_status()
        except Exception as e:
            print("Fetch error:", e)
            print("URL:", LAST_RACE_API_URL)
            return PlainTextResponse(f"Failed to fetch race info: {str(e)}", status_code=502)
        

    try:
        data = resp.json()
        race = data.get("race", [{}])[0]
        year = int(data.get("season", 2024)) - 1
        circuit = race.get("circuit")
        country = circuit.get("country")
        city = circuit.get("city")
        gp = city + " " + country
        race_dt_str = race.get("schedule", {}).get("race", {}).get("datetime_rfc3339")

        if not gp or not race_dt_str:
            raise ValueError("Missing circuitId or race time in API response")

        # Parse race time and calculate cache expiry based on next race time
        try:
            if race_dt_str:
                race_dt = datetime.fromisoformat(race_dt_str)
                race_dt = race_dt.astimezone(MT)

                # Expire 4 hours after race time
                expire = int((race_dt + timedelta(hours=4) - datetime.now(MT)).total_seconds())
            else:
                expire = 60 * 5 # Fall back in case cache expired, shouldn't raise but yeah.
        except Exception as e:
            print("Error fetching race time:", e)
            print("Used URL:", LAST_RACE_API_URL)
            expire = 60 * 60  # fallback: 1 hour if can't fetch next race data

        print("Cache expired: Fetching track map for " + str(gp) + " " + str(year))
        svg_content = generate_track_map_svg(year, gp, "Q")
        svg_bytes = svg_content.encode("utf-8")
        await cache.set(cache_key, svg_content, expire=expire)

        return StreamingResponse(io.BytesIO(svg_bytes), media_type="image/svg+xml")

    except Exception as e:
        return PlainTextResponse(f"Failed to generate SVG: {str(e)}", status_code=500)
