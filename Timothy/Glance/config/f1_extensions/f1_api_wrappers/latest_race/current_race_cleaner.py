from fastapi import FastAPI
import requests
from datetime import datetime
import pytz

app = FastAPI()
MT = pytz.timezone("America/Edmonton")
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

# Used to fix formatting issue in lap time
def replace_second_colon(text):
    first_colon_index = text.find(':')
    if first_colon_index == -1:
        return text
    second_colon_index = text.find(':', first_colon_index + 1)
    if second_colon_index == -1:
        return text
    return (text[:second_colon_index] + '.' + text[second_colon_index + 1:])

@app.get("/f1/last")
def get_last_race():
    r = requests.get("https://f1api.dev/api/current/next")
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

        race_name = race.get("raceName")
        if race_name:
            year = data.get("season")
            year_string = str(year)
            race['raceName'] = race['raceName'].replace(year_string, "").strip()

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
            # If only 1 driver in f1 history with last name, 1 last name provided, else full name
            fastest_driver_clean = fastest_driver_id.replace("_", " ").split(' ')
            driver_last_name_position = len(fastest_driver_clean)-1

            circuit['fastestLapDriverName'] = fastest_driver_clean[driver_last_name_position].capitalize()

        # European number formatting as "X:YY:ZZZ", replace with "X:YY.ZZZ" NA standard
        fastest_lap_time = circuit.get("lapRecord")
        if fastest_lap_time:
            circuit['lapRecord'] = replace_second_colon(fastest_lap_time)

        # Calculate total distance
        laps = race.get("laps")
        if laps and circuit.get("circuitLengthKm") is not None:
            race["totalDistanceKm"] = round(laps * circuit["circuitLengthKm"], 2)
        else:
            race["totalDistanceKm"] = None

    return data
