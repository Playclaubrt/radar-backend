from flask import Flask, jsonify, request
from flask_cors import CORS
import feedparser
import requests
import os

app = Flask(__name__)
CORS(app)

OWM_KEY = os.environ.get("OWM_KEY")  # coloque no Render

UF_COORDS = {
 "AC": [-9.02, -70.81], "AL": [-9.62, -36.82], "AM": [-3.07, -61.66],
 "AP": [1.41, -51.77], "BA": [-12.96, -38.51], "CE": [-3.71, -38.54],
 "DF": [-15.83, -47.86], "ES": [-20.32, -40.33], "GO": [-16.68, -49.25],
 "MA": [-2.55, -44.30], "MT": [-15.60, -56.10], "MS": [-20.45, -54.62],
 "MG": [-19.92, -43.94], "PA": [-1.45, -48.50], "PB": [-7.12, -34.86],
 "PR": [-25.43, -49.27], "PE": [-8.05, -34.90], "PI": [-5.09, -42.80],
 "RJ": [-22.90, -43.20], "RN": [-5.79, -35.21], "RS": [-30.03, -51.23],
 "RO": [-8.76, -63.90], "RR": [2.82, -60.67], "SC": [-27.59, -48.55],
 "SP": [-23.55, -46.63], "SE": [-10.90, -37.07], "TO": [-10.25, -48.32]
}

@app.route("/inmet")
def inmet():
    feed = feedparser.parse("https://apiprevmet3.inmet.gov.br/avisos/rss")
    alertas = []

    for e in feed.entries:
        alerta = {
            "titulo": e.title,
            "texto": e.summary,
            "data": e.published,
            "tipo": "textual",
            "ufs": [],
            "poligono": None
        }

        if "georss_polygon" in e:
            coords = e.georss_polygon.split()
            poly = []
            for i in range(0, len(coords), 2):
                poly.append([float(coords[i]), float(coords[i+1])])
            alerta["tipo"] = "geometrico"
            alerta["poligono"] = poly

        for uf, coord in UF_COORDS.items():
            if uf in e.summary:
                alerta["ufs"].append({
                    "uf": uf,
                    "lat": coord[0],
                    "lon": coord[1]
                })

        alertas.append(alerta)

    return jsonify(alertas)


@app.route("/noaa")
def noaa():
    url = "https://api.weather.gov/alerts/active"
    return jsonify(requests.get(url).json())


@app.route("/owm")
def owm():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}"
    return jsonify(requests.get(url).json())


@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OWM_KEY}"
    return jsonify(requests.get(url).json())


if __name__ == "__main__":
    app.run()