from fastapi import FastAPI
import requests
import pycountry

app = FastAPI()

def country_to_code(country_name: str) -> str:
    # Map non-standard names to ISO 3166
    replacements = {
        "Great Britain": "GB",
        "United States": "US",
    }
    try:
        country_name = replacements.get(country_name, country_name)
        return pycountry.countries.lookup(country_name).alpha_2.lower()
    except Exception:
        return ""  # fallback

@app.get("/constructors_championship")
def get_constructors_championship():
    url = "https://f1api.dev/api/current/constructors-championship"
    response = requests.get(url)

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

    return {"season": data.get("season"), "constructors": results}
