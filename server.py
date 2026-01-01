from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import feedparser

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

# ================= ALERTAS =================
@app.route("/alertas")
def alertas():
    alertas = []

    # ===== NOAA (EUA / CANADÁ) =====
    try:
        noaa = requests.get(
            "https://api.weather.gov/alerts/active",
            headers={"User-Agent": "RadarGlobal"}
        ).json()

        for f in noaa.get("features", []):
            props = f["properties"]
            event = props.get("event", "")
            desc = props.get("headline", "")
            coords = f["geometry"]

            if not coords:
                continue

            lon, lat = coords["coordinates"][0][0]

            emoji = "⚠️"
            if "Tornado" in event:
                emoji = "🌪️"
            elif "Severe" in event:
                emoji = "🟠"
            elif "Flood" in event:
                emoji = "🌊"

            alertas.append({
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "evento": event,
                "fonte": "NOAA"
            })
    except:
        pass

    # ===== INMET (BRASIL – RSS) =====
    try:
        rss = feedparser.parse(
            "https://alertas.inmet.gov.br/cap/rss/alertas.rss"
        )
        for e in rss.entries:
            titulo = e.title
            desc = e.summary

            emoji = "⚠️"
            if "Tornado" in titulo:
                emoji = "🌪️"
            elif "Tempestade" in titulo:
                emoji = "🟠"
            elif "Chuva" in titulo:
                emoji = "🌧️"

            # Coordenadas aproximadas (Brasil inteiro)
            alertas.append({
                "lat": -15,
                "lon": -47,
                "emoji": emoji,
                "evento": titulo,
                "fonte": "INMET"
            })
    except:
        pass

    return jsonify(alertas)

# ================= VENTO =================
@app.route("/wind")
def wind():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    ).json()

    return jsonify({
        "wind_kmh": r["wind"]["speed"] * 3.6
    })

# ================= FORECAST =================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    ).json()

    dias = {}
    for i in r["list"]:
        dia = i["dt_txt"].split(" ")[0]
        if dia not in dias:
            dias[dia] = {
                "temp": i["main"]["temp"],
                "vento": i["wind"]["speed"] * 3.6,
                "pressao": i["main"]["pressure"],
                "chuva": i.get("rain", {}).get("3h", 0)
            }

    return jsonify(dias)

if __name__ == "__main__":
    app.run()
