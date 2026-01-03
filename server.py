from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import feedparser
from datetime import datetime

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"  # coloque sua key do OpenWeatherMap

# ===============================
# NOAA ALERTS (EUA / CANADÁ)
# ===============================
@app.route("/noaa")
def noaa():
    url = "https://api.weather.gov/alerts/active"
    r = requests.get(url, headers={"User-Agent":"radar"})
    data = r.json()

    alerts = []
    for f in data.get("features", []):
        p = f["properties"]
        g = f["geometry"]
        if not g:
            continue

        coords = g["coordinates"][0]
        lats = [c[1] for c in coords]
        lons = [c[0] for c in coords]

        alerts.append({
            "title": p.get("event"),
            "description": p.get("description"),
            "severity": p.get("severity"),
            "source": "NOAA",
            "bounds": [[min(lats), min(lons)], [max(lats), max(lons)]]
        })

    return jsonify(alerts)

# ===============================
# INMET RSS (BRASIL – 100% TEXTO ORIGINAL)
# ===============================
@app.route("/inmet")
def inmet():
    feed = feedparser.parse("https://alertas.inmet.gov.br/rss")
    alerts = []

    for e in feed.entries:
        if "polygon" not in e:
            continue

        coords = []
        for p in e.polygon.split():
            lat, lon = p.split(",")
            coords.append((float(lat), float(lon)))

        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]

        alerts.append({
            "title": e.title,
            "description": e.summary,
            "severity": "INMET",
            "source": "INMET",
            "bounds": [[min(lats), min(lons)], [max(lats), max(lons)]]
        })

    return jsonify(alerts)

# ===============================
# OWM ATUAL
# ===============================
@app.route("/owm")
def owm():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}&lang=pt_br"
    r = requests.get(url).json()

    return jsonify({
        "temp": r["main"]["temp"],
        "humidity": r["main"]["humidity"],
        "pressure": r["main"]["pressure"],
        "wind": r["wind"]["speed"] * 3.6,
        "clouds": r["clouds"]["all"],
        "icon": r["weather"][0]["icon"]
    })

# ===============================
# OWM PREVISÃO 5 DIAS
# ===============================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}&lang=pt_br"
    r = requests.get(url).json()

    days = {}
    for i in r["list"]:
        d = i["dt_txt"].split(" ")[0]
        if d not in days:
            days[d] = {
                "temp": i["main"]["temp"],
                "humidity": i["main"]["humidity"],
                "pressure": i["main"]["pressure"],
                "wind": i["wind"]["speed"] * 3.6,
                "icon": i["weather"][0]["icon"]
            }

    return jsonify(list(days.values())[:5])

if __name__ == "__main__":
    app.run()