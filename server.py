from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

HEADERS = {"User-Agent": "RadarGlobal/1.0"}

# ================= ALERTAS NOAA =================
@app.route("/alertas")
def alertas():
    alertas = []

    try:
        r = requests.get(
            "https://api.weather.gov/alerts/active",
            headers=HEADERS,
            timeout=10
        ).json()

        for f in r["features"]:
            p = f["properties"]
            g = f.get("geometry")

            if not g:
                continue

            coords = g["coordinates"][0][0]
            lon, lat = coords[0], coords[1]

            evento = p.get("event", "")
            headline = p.get("headline", "")
            desc = p.get("description", "")
            instr = p.get("instruction", "")
            inicio = p.get("effective", "")
            severidade = p.get("severity", "")
            urgencia = p.get("urgency", "")

            emoji = "⚠️"
            if "Tornado" in evento: emoji = "🌪️"
            elif "Flood" in evento: emoji = "🌊"
            elif "Hurricane" in evento: emoji = "🌀"
            elif "Severe" in evento: emoji = "⛈️"

            alertas.append({
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "evento": evento,
                "headline": headline,
                "descricao": desc,
                "instrucao": instr,
                "inicio": inicio,
                "severidade": severidade,
                "urgencia": urgencia,
                "fonte": "NOAA"
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
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric",
        timeout=10
    ).json()

    kmh = round(r["wind"]["speed"] * 3.6, 1)
    if kmh > 300:
        kmh = 300

    return jsonify({"kmh": kmh})

# ================= FORECAST 5 DIAS =================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric",
        timeout=10
    ).json()

    dias = {}

    for i in r["list"]:
        d = i["dt_txt"].split(" ")[0]
        if d not in dias:
            dias[d] = {
                "temp": round(i["main"]["temp"]),
                "vento": round(i["wind"]["speed"] * 3.6, 1),
                "pressao": i["main"]["pressure"],
                "umidade": i["main"]["humidity"],
                "icone": i["weather"][0]["icon"]
            }

    return jsonify(dias)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
