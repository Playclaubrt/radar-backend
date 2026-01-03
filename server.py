from flask import Flask, jsonify, request
from flask_cors import CORS
import feedparser
import requests

app = Flask(__name__)
CORS(app)

# ===============================
# NOAA ALERTS
# ===============================
@app.route("/noaa")
def noaa_alerts():
    url = "https://alerts.weather.gov/cap/us.php?x=0"
    feed = feedparser.parse(url)

    alerts = []

    for e in feed.entries:
        alerts.append({
            "title": e.title,
            "summary": e.summary,
            "published": e.published,
            "link": e.link,
            "source": "NOAA"
        })

    return jsonify(alerts)


# ===============================
# INMET ALERTS (RSS 100% ORIGINAL)
# ===============================
@app.route("/inmet")
def inmet_alerts():
    url = "https://apiprevmet3.inmet.gov.br/avisos/rss"
    feed = feedparser.parse(url)

    alerts = []

    for e in feed.entries:
        alerts.append({
            "title": e.title,
            "description": e.description,  # TEXTO 100% ORIGINAL
            "published": e.published,
            "link": e.link,
            "source": "INMET"
        })

    return jsonify(alerts)


# ===============================
# OWM – WEATHER DATA
# ===============================
@app.route("/owm")
def owm_data():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    api_key = "7609a59c493758162d9b0a6af2914e1f"

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&units=metric&lang=pt_br&appid={api_key}"
    )

    r = requests.get(url).json()

    forecast = []

    for item in r["list"][:40]:
        forecast.append({
            "temp": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "pressure": item["main"]["pressure"],
            "wind": item["wind"]["speed"] * 3.6,
            "weather": item["weather"][0]["description"],
            "dt": item["dt_txt"]
        })

    return jsonify(forecast)


@app.route("/")
def home():
    return "Radar Backend Online"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)