from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# =========================
# CONFIG
# =========================
OWM_KEY = os.environ.get("OWM_KEY")  # coloque no Render
HEADERS_NOAA = {"User-Agent": "GlobalRadar/1.0"}

# =========================
# NOAA ALERTS (EUA)
# =========================
def get_noaa_alerts():
    alerts = []
    try:
        r = requests.get(
            "https://api.weather.gov/alerts/active",
            headers=HEADERS_NOAA,
            timeout=10
        )
        data = r.json()

        for f in data.get("features", []):
            prop = f["properties"]
            geo = f.get("geometry")

            if not geo:
                continue

            lon, lat = geo["coordinates"][0][0]

            event = prop.get("event", "").lower()

            emoji = "⚠️"
            tipo = prop.get("event", "")

            if "tornado" in event:
                emoji = "🌪️"
            elif "hurricane" in event:
                emoji = "🌀"
            elif "severe thunderstorm" in event:
                emoji = "⛈️"

            alerts.append({
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "tipo": tipo,
                "fonte": "NOAA"
            })
    except:
        pass

    return alerts


# =========================
# INMET ALERTS (BRASIL)
# =========================
def get_inmet_alerts():
    alerts = []
    try:
        r = requests.get("https://apiprevmet3.inmet.gov.br/avisos", timeout=10)
        data = r.json()

        for a in data:
            area = a.get("area", {})
            lat = area.get("lat")
            lon = area.get("lon")

            if not lat or not lon:
                continue

            evento = a.get("evento", "").lower()

            emoji = "⚠️"
            if "tornado" in evento:
                emoji = "🌪️"
            elif "ciclone" in evento:
                emoji = "🌀"
            elif "tempestade" in evento:
                emoji = "⛈️"
            elif "chuva" in evento:
                emoji = "🌨️"

            alerts.append({
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "tipo": a.get("evento"),
                "fonte": "INMET"
            })
    except:
        pass

    return alerts


# =========================
# ENDPOINT: ALERTAS GLOBAIS
# =========================
@app.route("/alertas")
def alertas():
    data = []
    data.extend(get_noaa_alerts())
    data.extend(get_inmet_alerts())
    return jsonify(data)


# =========================
# ENDPOINT: VENTO GLOBAL
# =========================
@app.route("/wind")
def wind():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OWM_KEY,
                "units": "metric"
            },
            timeout=10
        )
        d = r.json()
        kmh = d.get("wind", {}).get("speed", 0) * 3.6

        return jsonify({
            "wind_kmh": round(kmh, 1)
        })
    except:
        return jsonify({"wind_kmh": 0})


# =========================
# RUN (RENDER)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
