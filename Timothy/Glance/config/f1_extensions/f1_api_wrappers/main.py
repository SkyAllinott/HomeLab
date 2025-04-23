from fastapi import FastAPI
from apis.current_race_cleaner import router as current_race_cleaner
from apis.constructors_cleaner import router as constructors_cleaner
from apis.map.router import router as map_router

app = FastAPI()

# Include all routers
app.include_router(current_race_cleaner, prefix="/f1/next_race")
app.include_router(constructors_cleaner, prefix="/f1/constructors_standings")
app.include_router(map_router, prefix="/f1/next_map")
