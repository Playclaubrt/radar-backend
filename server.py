from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app)

OWM_KEY = os.getenv("7609a59c493758162d9b0a6af2914e1f")

@app.route("/wind-grid")
def wind_grid():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}",
        timeout=6
    ).json()

    wind = r.get("wind",{}).get("speed",0)*3.6
    return {"wind_kmh":round(wind,1)}

@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    return requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}",
        timeout=8
    ).json()

@app.route("/alertas")
def alertas():
    r = requests.get("https://api.weather.gov/alerts/active",timeout=10).json()
    out=[]
    for a in r["features"]:
        p=a["properties"]
        out.append({
            "event":p.get("event"),
            "description":p.get("description")
        })
    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=10000)