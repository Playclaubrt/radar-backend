from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math
import time

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

# ======================
# ALERTAS NOAA (GLOBAL)
# ======================
@app.route("/alertas")
def alertas():
    url = "https://api.weather.gov/alerts/active"
    r = requests.get(url, headers={
        "User-Agent": "RadarGlobal/1.0"
    })

    data = r.json()
    out = []

    for f in data.get("features", []):
        p = f["properties"]
        geo = f.get("geometry")

        if not geo:
            continue

        lon, lat = geo["coordinates"][0][0]

        out.append({
            "lat": lat,
            "lon": lon,
            "tipo": p.get("event"),
            "descricao": p.get("description"),
            "inicio": p.get("effective"),
            "fonte": "NOAA",
            "emoji": "🌪️" if "Tornado" in p.get("event","") else "⚠️"
        })

    return jsonify(out)

# ======================
# VENTO (quadrados)
# ======================
@app.route("/wind")
def wind():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    )
    d = r.json()

    kmh = d.get("wind", {}).get("speed", 0) * 3.6
    kmh = min(kmh, 250)  # trava valores absurdos

    return jsonify({
        "wind_kmh": round(kmh,1)
    })

# ======================
# DETALHES AO CLICAR
# ======================
@app.route("/detalhes")
def detalhes():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&lang=pt"
    )
    d = r.json()

    dias = []
    for i in range(0,40,8):
        item = d["list"][i]
        dias.append({
            "temp": item["main"]["temp"],
            "umidade": item["main"]["humidity"],
            "pressao": item["main"]["pressure"],
            "vento": item["wind"]["speed"]*3.6,
            "icone": item["weather"][0]["icon"]
        })

    return jsonify(dias)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
