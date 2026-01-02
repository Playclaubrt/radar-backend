from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

# =========================
# ALERTAS NOAA (CRU)
# =========================
@app.route("/alertas")
def alertas():
    url = "https://api.weather.gov/alerts/active"
    r = requests.get(url, headers={
        "User-Agent": "RadarWindyLike/1.0"
    })
    data = r.json()

    alerts = []

    for f in data.get("features", []):
        p = f["properties"]
        g = f.get("geometry")
        if not g:
            continue

        lon, lat = g["coordinates"][0][0]

        alerts.append({
            "lat": lat,
            "lon": lon,
            "event": p.get("event"),
            "headline": p.get("headline"),
            "description": p.get("description"),
            "instruction": p.get("instruction"),
            "severity": p.get("severity"),
            "effective": p.get("effective"),
            "expires": p.get("expires"),
            "source": "NOAA"
        })

    return jsonify(alerts)

# =========================
# VENTO + UMIDADE (RÁPIDO)
# =========================
@app.route("/wind")
def wind():
    lat = request.args["lat"]
    lon = request.args["lon"]

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    )
    d = r.json()

    return jsonify({
        "wind": round(d["wind"]["speed"] * 3.6, 1),
        "humidity": d["main"]["humidity"],
        "pressure": d["main"]["pressure"],
        "temp": d["main"]["temp"]
    })

# =========================
# TIMELINE (5 DIAS)
# =========================
@app.route("/timeline")
def timeline():
    lat = request.args["lat"]
    lon = request.args["lon"]

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    )
    d = r.json()

    days = []
    for i in range(0, 40, 8):
        x = d["list"][i]
        days.append({
            "temp": x["main"]["temp"],
            "humidity": x["main"]["humidity"],
            "pressure": x["main"]["pressure"],
            "wind": round(x["wind"]["speed"] * 3.6, 1),
            "icon": x["weather"][0]["icon"]
        })

    return jsonify(days)

app.run(host="0.0.0.0", port=10000)
