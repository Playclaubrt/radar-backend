from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_KEY = "7609a59c493758162d9b0a6af2914e1f"

# ---------------- UTIL ----------------
def ms_to_kmh(ms):
    return round(ms * 3.6, 1)

# ---------------- ALERTAS ----------------
@app.route("/alertas")
def alertas():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        f"&exclude=minutely,hourly"
        f"&units=metric&lang=pt"
        f"&appid={API_KEY}"
    )

    if r.status_code != 200:
        return jsonify([])

    d = r.json()
    alerts = []

    for a in d.get("alerts", []):
        alerts.append({
            "evento": a.get("event"),
            "descricao": a.get("description"),
            "inicio": a.get("start"),
            "fim": a.get("end"),
            "fonte": a.get("sender_name"),
            "emoji": "⚠️"
        })

    return jsonify(alerts)

# ---------------- VENTO ----------------
@app.route("/vento")
def vento():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )

    if r.status_code != 200:
        return jsonify({"wind_kmh": 0})

    d = r.json()
    return jsonify({
        "wind_kmh": ms_to_kmh(d["wind"]["speed"])
    })

# ---------------- PREVISÃO ----------------
@app.route("/previsao")
def previsao():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        f"&exclude=current,minutely,hourly,alerts"
        f"&units=metric&lang=pt"
        f"&appid={API_KEY}"
    )

    if r.status_code != 200:
        return jsonify([])

    d = r.json()
    out = []

    for dia in d["daily"][:5]:
        out.append({
            "temp": dia["temp"]["day"],
            "vento": ms_to_kmh(dia["wind_speed"]),
            "pressao": dia["pressure"],
            "umidade": dia["humidity"],
            "nuvem": dia["weather"][0]["description"]
        })

    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
