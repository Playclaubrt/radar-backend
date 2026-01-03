from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math
import os

app = Flask(__name__)
CORS(app)

OWM_KEY = os.getenv("7609a59c493758162d9b0a6af2914e1f") or "SUA_API_KEY_AQUI"

# =========================
# GRID GLOBAL DE VENTO
# =========================
@app.route("/wind-grid")
def wind_grid():
    zoom = int(request.args.get("z", 3))

    step = 20 if zoom <= 3 else 10 if zoom <= 4 else 5

    data = []
    for lat in range(-80, 80, step):
        for lon in range(-180, 180, step):
            try:
                r = requests.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": OWM_KEY,
                        "units": "metric"
                    },
                    timeout=4
                )
                d = r.json()
                wind = d.get("wind", {}).get("speed", 0) * 3.6

                data.append({
                    "lat": lat,
                    "lon": lon,
                    "step": step,
                    "wind": round(wind, 1)
                })
            except:
                pass

    return jsonify(data)

# =========================
# ALERTAS NOAA (PUROS)
# =========================
@app.route("/alertas")
def alertas():
    r = requests.get("https://api.weather.gov/alerts/active", timeout=6)
    d = r.json()

    alerts = []
    for f in d.get("features", []):
        geo = f.get("geometry")
        if not geo:
            continue

        coords = geo["coordinates"][0]
        lats = [c[1] for c in coords]
        lons = [c[0] for c in coords]

        alerts.append({
            "lat1": min(lats),
            "lon1": min(lons),
            "lat2": max(lats),
            "lon2": max(lons),
            "emoji": "⚠️",
            "description": f["properties"].get("description", "")
        })

    return jsonify(alerts)

# =========================
# PREVISÃO 5 DIAS
# =========================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "lat": lat,
            "lon": lon,
            "appid": OWM_KEY,
            "units": "metric",
            "lang": "pt"
        },
        timeout=6
    )

    d = r.json()
    days = {}

    for item in d.get("list", []):
        day = item["dt_txt"].split(" ")[0]
        if day not in days:
            days[day] = {
                "day": day,
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "wind": round(item["wind"]["speed"] * 3.6, 1),
                "weather": item["weather"][0]["description"]
            }

    return jsonify(list(days.values())[:5])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
