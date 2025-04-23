from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
import httpx
import io

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from .map_generator import generate_track_map_svg


router = APIRouter()

# Use the next_race router to get next race details and fetch right map
LAST_RACE_API_URL = "http://192.168.0.80:4463/f1/next_race/"

@router.on_event("startup")

# Initialize cacheing
async def startup():
    FastAPICache.init(InMemoryBackend())

@router.get("/", summary="Fetch next track map")
async def get_dynamic_track_map():
    cache_key = "track_map_svg"
    backend = FastAPICache.get_backend()

    svg_content = await backend.get(cache_key)
    if svg_content is not None:
        return Response(content=svg_content, media_type="image/svg+xml")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(LAST_RACE_API_URL)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return PlainTextResponse(f"Failed to fetch race info: {str(e)}", status_code=502)

    try:
        data = resp.json()
        race = data.get("race", [{}])[0]
        year = int(data.get("season", 2024)) - 1
        gp = race.get("circuit", {}).get("circuitId", "")

        if not gp:
            raise ValueError("Missing circuitId in API response")

        svg_content = generate_track_map_svg(year, gp, "Q")
        svg_bytes = svg_content.encode("utf-8")
        await backend.set(cache_key, svg_content, expire=60 * 60 * 6)
        return StreamingResponse(io.BytesIO(svg_bytes), media_type="image/svg+xml")

    except Exception as e:
        return PlainTextResponse(f"Failed to generate SVG: {str(e)}", status_code=500)
