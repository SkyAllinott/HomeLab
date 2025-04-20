from fastapi import FastAPI
import requests
from datetime import datetime
import pytz

app = FastAPI()
MT = pytz.timezone("America/Denver")
UTC = pytz.utc

def convert_to_mt(date_str, time_str):
    if not date_str or not time_str:
        return None, None, None
    dt_utc = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M:%SZ")
    dt_utc = UTC.localize(dt_utc)
    dt_mt = dt_utc.astimezone(MT)
    return (
        dt_mt.strftime("%Y-%m-%d"),  # local date
        dt_mt.strftime("%H:%M:%S"),  # local time
        dt_mt.isoformat()            # rfc3339 datetime
    )

@app.get("/f1/last")
def get_last_race():
    r = requests.get("https://f1api.dev/api/current/last")
    data = r.json()

    for race in data.get("race", []):
        # Convert session times
        schedule = race.get("schedule", {})
        for session, val in schedule.items():
            if val["date"] and val["time"]:
                date, time, rfc = convert_to_mt(val["date"], val["time"])
                val["date"] = date
                val["time"] = time
                val["datetime_rfc3339"] = rfc

        # Fix circuit length from meters to kilometers
        circuit = race.get("circuit", {})
        if "circuitLength" in circuit:
            try:
                raw_length = int(circuit["circuitLength"].replace("km", "").strip())
                circuit["circuitLengthKm"] = raw_length / 1000.0
            except Exception:
                circuit["circuitLengthKm"] = None

        # Capitalize fastest lap driver's last name (if exists)
        fastest_driver_id = circuit.get("fastestLapDriverId")
        if fastest_driver_id:
            circuit["fastestLapDriverName"] = fastest_driver_id.capitalize()

        # Calculate total distance
        laps = race.get("laps")
        if laps and circuit.get("circuitLengthKm") is not None:
            race["totalDistanceKm"] = round(laps * circuit["circuitLengthKm"], 2)
        else:
            race["totalDistanceKm"] = None

    return data



