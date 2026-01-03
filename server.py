from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

# ===============================
# ALERTAS NOAA (EUA / CANADÁ)
# ===============================
@app.route("/alertas")
def alertas():
    alerts = []

    try:
        r = requests.get(
            "https://api.weather.gov/alerts/active",
            headers={"User-Agent": "RadarGlobal"}
        )
        data = r.json()

        for f in data.get("features", []):
            p = f["properties"]

            alerts.append({
                "evento": p.get("event"),
                "descricao": p.get("description"),
                "inicio": p.get("effective"),
                "fim": p.get("ends"),
                "area": p.get("areaDesc"),
                "fonte": "NOAA",
                "emoji": "🌪️" if "Tornado" in p.get("event","") else "⚠️"
            })

    except Exception:
        pass

    return jsonify(alerts)

# ===============================
# VENTO GLOBAL (GRADE)
# ===============================
@app.route("/wind")
def wind():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    )

    d = r.json()
    vento = d.get("wind", {}).get("speed", 0) * 3.6

    return jsonify({
        "wind_kmh": round(vento, 1)
    })

# ===============================
# PREVISÃO 5 DIAS
# ===============================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&lang=pt_br"
    )

    d = r.json()
    dias = []

    for i in range(0, 40, 8):
        item = d["list"][i]
        dias.append({
            "temp": item["main"]["temp"],
            "umidade": item["main"]["humidity"],
            "vento": item["wind"]["speed"] * 3.6,
            "pressao": item["main"]["pressure"],
            "clima": item["weather"][0]["description"]
        })

    return jsonify(dias)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)