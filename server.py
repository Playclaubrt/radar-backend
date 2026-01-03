from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser

app = Flask(__name__)
CORS(app)

# ======================
# NOAA – EUA / CANADÁ
# ======================
NOAA_API = "https://api.weather.gov/alerts/active"

# ======================
# INMET – BRASIL (RSS)
# ======================
INMET_RSS = "https://apiprevmet.inmet.gov.br/avisos/rss"

# ======================
# EMOJIS OFICIAIS
# ======================
def definir_emoji(evento):
    e = evento.lower()

    if "tornado" in e:
        return "🌪️"
    if "hurricane" in e or "furacão" in e:
        return "🌀🔴"
    if "ciclone" in e:
        return "🌀"
    if "neve" in e or "snow" in e or "blizzard" in e:
        return "❄️"
    if "chuva" in e or "rain" in e:
        if "amarelo" in e:
            return "🌨️"
        if "laranja" in e:
            return "🌩️"
        if "vermelho" in e:
            return "⛈️"
        return "🌧️"

    return "⚠️"

# ======================
# NOAA ALERTAS
# ======================
@app.route("/noaa")
def noaa_alerts():
    r = requests.get(NOAA_API, headers={"User-Agent": "RadarGlobal"})
    data = r.json()

    alerts = []
    for f in data.get("features", []):
        p = f["properties"]
        alerts.append({
            "emoji": definir_emoji(p.get("event","")),
            "event": p.get("event"),
            "description": p.get("description"),
            "area": p.get("areaDesc"),
            "source": "NOAA"
        })

    return jsonify(alerts)

# ======================
# INMET ALERTAS (RSS)
# ======================
@app.route("/inmet")
def inmet_alerts():
    feed = feedparser.parse(INMET_RSS)
    alerts = []

    for e in feed.entries:
        alerts.append({
            "emoji": definir_emoji(e.title),
            "event": e.title,
            "description": e.summary,
            "area": None,
            "source": "INMET"
        })

    return jsonify(alerts)

# ======================
# ALERTAS UNIFICADOS
# ======================
@app.route("/alertas")
def todos_alertas():
    return jsonify({
        "noaa": noaa_alerts().json,
        "inmet": inmet_alerts().json
    })

# ======================
# START
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)