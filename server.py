from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, feedparser
from datetime import datetime

app = Flask(__name__)
CORS(app)

OWM = "7609a59c493758162d9b0a6af2914e1f"

# ================= ALERTAS =================
@app.route("/alertas")
def alertas():
    out = []

    # NOAA
    try:
        r = requests.get(
            "https://api.weather.gov/alerts/active",
            headers={"User-Agent": "RadarGlobal"}
        ).json()

        for f in r.get("features", []):
            g = f.get("geometry")
            if not g:
                continue
            lon, lat = g["coordinates"][0][0]
            p = f["properties"]

            evento = p.get("event","")
            emoji = "⚠️"
            if "Tornado" in evento: emoji="🌪️"
            if "Flood" in evento: emoji="🌊"
            if "Severe" in evento: emoji="🟠"

            out.append({
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "texto": evento,
                "fonte": "NOAA"
            })
    except:
        pass

    # INMET
    try:
        rss = feedparser.parse("https://alertas.inmet.gov.br/cap/rss/alertas.rss")
        for e in rss.entries:
            out.append({
                "lat": -15,
                "lon": -47,
                "emoji": "🟡",
                "texto": e.title,
                "fonte": "INMET"
            })
    except:
        pass

    return jsonify(out)

# ================= RAIOS =================
@app.route("/raios")
def raios():
    dados = []
    try:
        r = requests.get(
            "https://www.lightningmaps.org/data/strikes.json",
            timeout=10
        ).json()

        agora = datetime.utcnow().timestamp()

        for s in r:
            if agora - s["ts"] <= 120:
                dados.append({
                    "lat": s["lat"],
                    "lon": s["lon"],
                    "forca": s.get("amp", 0),
                    "hora": datetime.utcfromtimestamp(s["ts"]).strftime("%H:%M:%S")
                })
    except:
        pass

    return jsonify(dados)

# ================= VENTO =================
@app.route("/wind")
def wind():
    lat = request.args["lat"]
    lon = request.args["lon"]

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM}&units=metric"
    ).json()

    kmh = round(r["wind"]["speed"] * 3.6, 1)
    return jsonify({"kmh": kmh})

# ================= FORECAST =================
@app.route("/forecast")
def forecast():
    lat = request.args["lat"]
    lon = request.args["lon"]

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OWM}&units=metric"
    ).json()

    dias = {}
    for i in r["list"]:
        d = i["dt_txt"].split(" ")[0]
        if d not in dias:
            dias[d] = {
                "temp": round(i["main"]["temp"]),
                "hum": i["main"]["humidity"],
                "press": i["main"]["pressure"],
                "vento": round(i["wind"]["speed"] * 3.6,1),
                "icone": i["weather"][0]["icon"]
            }
    return jsonify(dias)

if __name__ == "__main__":
    app.run()
