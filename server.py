from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import feedparser
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================
INMET_RSS = "https://apiprevmet3.inmet.gov.br/avisos/rss"
OWM_KEY = "SUA_API_KEY_AQUI"

# Centros aproximados das UFs (usado APENAS para alertas textuais)
UF_CENTERS = {
    "AC": [-9.97, -67.81], "AL": [-9.66, -35.71], "AP": [0.03, -51.07],
    "AM": [-3.07, -61.66], "BA": [-12.97, -38.51], "CE": [-3.73, -38.52],
    "DF": [-15.78, -47.93], "ES": [-20.32, -40.33], "GO": [-16.68, -49.25],
    "MA": [-2.53, -44.30], "MT": [-15.60, -56.10], "MS": [-20.45, -54.62],
    "MG": [-19.92, -43.94], "PA": [-1.45, -48.49], "PB": [-7.12, -34.88],
    "PR": [-25.42, -49.27], "PE": [-8.05, -34.90], "PI": [-5.09, -42.80],
    "RJ": [-22.90, -43.20], "RN": [-5.79, -35.21], "RS": [-30.03, -51.23],
    "RO": [-8.76, -63.90], "RR": [2.82, -60.67], "SC": [-27.59, -48.55],
    "SP": [-23.55, -46.63], "SE": [-10.90, -37.07], "TO": [-10.18, -48.33]
}

# =========================
# UTIL
# =========================
def extract_ufs(text):
    ufs = []
    for uf in UF_CENTERS.keys():
        if re.search(rf"\b{uf}\b", text):
            ufs.append(uf)
    return list(set(ufs))

def emoji_inmet(text):
    t = text.lower()
    if "tornado" in t:
        return "🌪️"
    if "ciclone" in t:
        return "🌀"
    if "vermelho" in t:
        return "⛈️"
    if "laranja" in t:
        return "🌩️"
    if "amarelo" in t:
        return "🌨️"
    if "chuva" in t:
        return "🌧️"
    return "⚠️"

# =========================
# INMET – TEXTUAL + NÃO TEXTUAL
# =========================
@app.route("/inmet")
def inmet():
    feed = feedparser.parse(INMET_RSS)
    alerts = []

    for item in feed.entries:
        title = item.get("title", "")
        description = item.get("description", "")
        published = item.get("published", "")

        emoji = emoji_inmet(title + description)

        # NÃO TEXTUAL (tem polígono)
        if "georss_polygon" in item:
            coords = item.georss_polygon.split()
            polygon = []
            for i in range(0, len(coords), 2):
                polygon.append([float(coords[i]), float(coords[i+1])])

            alerts.append({
                "type": "geometrico",
                "emoji": emoji,
                "title": title,
                "description": description,
                "published": published,
                "polygon": polygon,
                "source": "INMET"
            })

        # TEXTUAL (SEM coordenadas)
        else:
            ufs = extract_ufs(title + description)
            if not ufs:
                ufs = ["BR"]

            for uf in ufs:
                lat, lon = UF_CENTERS.get(uf, [-14.2, -51.9])
                alerts.append({
                    "type": "textual",
                    "emoji": emoji,
                    "title": title,
                    "description": description,
                    "published": published,
                    "uf": uf,
                    "lat": lat,
                    "lon": lon,
                    "source": "INMET"
                })

    return jsonify(alerts)

# =========================
# NOAA (ativos – simples)
# =========================
@app.route("/noaa")
def noaa():
    try:
        r = requests.get("https://api.weather.gov/alerts/active", timeout=10)
        data = r.json()
        alerts = []

        for f in data.get("features", []):
            p = f["properties"]
            g = f["geometry"]

            alerts.append({
                "event": p.get("event"),
                "headline": p.get("headline"),
                "description": p.get("description"),
                "severity": p.get("severity"),
                "polygon": g["coordinates"] if g else None,
                "source": "NOAA"
            })

        return jsonify(alerts)
    except:
        return jsonify([])

# =========================
# OWM – atual
# =========================
@app.route("/owm")
def owm():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&lang=pt_br"
    )
    d = r.json()

    return jsonify({
        "temp": d["main"]["temp"],
        "humidity": d["main"]["humidity"],
        "pressure": d["main"]["pressure"],
        "wind": d["wind"]["speed"] * 3.6,
        "clouds": d["clouds"]["all"],
        "description": d["weather"][0]["description"]
    })

# =========================
# FORECAST 5 DIAS
# =========================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&lang=pt_br"
    )
    d = r.json()

    days = {}
    for item in d["list"]:
        date = item["dt_txt"].split(" ")[0]
        if date not in days:
            days[date] = {
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "pressure": item["main"]["pressure"],
                "wind": item["wind"]["speed"] * 3.6,
                "weather": item["weather"][0]["description"]
            }
        if len(days) == 5:
            break

    return jsonify(days)

# =========================
# START
# =========================
if __name__ == "__main__":
    app.run()