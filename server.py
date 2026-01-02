from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app)

OWM = os.getenv("7609a59c493758162d9b0a6af2914e1f")

# =====================
# VENTO GLOBAL (1 ponto = 1 resposta)
# =====================
@app.route("/wind")
def wind():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": lat, "lon": lon, "appid": OWM, "units": "metric"}
    )
    j = r.json()

    return jsonify({
        "wind": round(j["wind"]["speed"] * 3.6, 1),
        "temp": round(j["main"]["temp"], 1),
        "humidity": j["main"]["humidity"]
    })


# =====================
# PREVISÃO 5 DIAS
# =====================
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"lat": lat, "lon": lon, "appid": OWM, "units": "metric"}
    )

    dias = {}
    for item in r.json()["list"]:
        dia = item["dt_txt"].split(" ")[0]
        if dia not in dias:
            dias[dia] = {
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "weather": item["weather"][0]["main"]
            }

    return jsonify(list(dias.values())[:5])


# =====================
# ALERTAS NOAA (centro do polígono)
# =====================
@app.route("/alertas")
def alertas():
    dados = []
    r = requests.get("https://api.weather.gov/alerts/active")
    for f in r.json()["features"]:
        g = f["geometry"]
        p = f["properties"]

        if g and g["type"] == "Polygon":
            coords = g["coordinates"][0]
            lat = sum(c[1] for c in coords) / len(coords)
            lon = sum(c[0] for c in coords) / len(coords)

            dados.append({
                "lat": lat,
                "lon": lon,
                "event": p["event"],
                "description": p["headline"],
                "emoji": "🌪️" if "Tornado" in p["event"] else "⚠️"
            })

    return jsonify(dados)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
