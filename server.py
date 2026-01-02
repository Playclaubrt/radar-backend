from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

OWM_KEY = os.getenv("7609a59c493758162d9b0a6af2914e1f")

# ===== ALERTAS NOAA + INMET
@app.route("/alertas")
def alertas():
 dados = []

 # NOAA (global)
 try:
  r = requests.get("https://api.weather.gov/alerts/active")
  for f in r.json()["features"]:
   p = f["properties"]
   if p.get("severity"):
    dados.append({
     "lat": p["geocode"]["SAME"][0] if p.get("geocode") else 0,
     "lon": 0,
     "event": p["event"],
     "description": p.get("description"),
     "emoji":"⚠️"
    })
 except: pass

 return jsonify(dados)

# ===== VENTO GLOBAL
@app.route("/wind")
def wind():
 lat=request.args.get("lat")
 lon=request.args.get("lon")

 r=requests.get(
  "https://api.openweathermap.org/data/2.5/weather",
  params={"lat":lat,"lon":lon,"appid":OWM_KEY,"units":"metric"}
 )

 j=r.json()
 return jsonify({
  "wind": j["wind"]["speed"]*3.6,
  "temp": j["main"]["temp"],
  "humidity": j["main"]["humidity"]
 })

if __name__ == "__main__":
 app.run(host="0.0.0.0",port=10000)
