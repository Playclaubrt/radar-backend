from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math

app = Flask(__name__)
CORS(app)

OWM_KEY = "7609a59c493758162d9b0a6af2914e1f"

# ===== ALERTAS GLOBAIS (NOAA / INMET / OWM) =====
@app.route("/alertas")
def alertas():
    alertas = []

    # ===== NOAA (EUA / CANADÁ) =====
    try:
        r = requests.get("https://api.weather.gov/alerts/active")
        data = r.json()

        for a in data.get("features", []):
            props = a.get("properties", {})
            geo = a.get("geometry")

            if geo and geo.get("coordinates"):
                lon, lat = geo["coordinates"][0][0]

                alertas.append({
                    "lat": lat,
                    "lon": lon,
                    "emoji": "🌪️" if "Tornado" in props.get("event", "") else "🚨",
                    "vento": props.get("windSpeed", "N/A"),
                    "nuvem": props.get("event", ""),
                    "descricao": props.get("headline", ""),
                    "fonte": "NOAA"
                })
    except:
        pass

    # ===== INMET (BRASIL) =====
    try:
        r = requests.get("https://apitempo.inmet.gov.br/avisos/ativos")
        data = r.json()

        for a in data:
            alertas.append({
                "lat": float(a["latitude"]),
                "lon": float(a["longitude"]),
                "emoji": "🚨",
                "vento": a.get("intensidade", "N/A"),
                "nuvem": a.get("evento", ""),
                "descricao": a.get("descricao", ""),
                "fonte": "INMET"
            })
    except:
        pass

    return jsonify(alertas)


# ===== VENTO GLOBAL (QUADRADOS) =====
@app.route("/wind")
def wind():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OWM_KEY
            }
        )
        d = r.json()
        kmh = d.get("wind", {}).get("speed", 0) * 3.6
    except:
        kmh = 0

    return jsonify({
        "wind_kmh": round(kmh, 1)
    })


@app.route("/")
def home():
    return "Radar Backend Online"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
