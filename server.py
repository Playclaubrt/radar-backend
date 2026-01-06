from flask import Flask, jsonify
from flask_cors import CORS
import feedparser
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://alertas2.inmet.gov.br/rss/alertas.rss"

# Centros aproximados das UFs
UF_COORDS = {
    "AC": [-9,-70], "AL": [-9.6,-36.7], "AP":[1.4,-51.7], "AM":[-3.1,-60],
    "BA":[-12.5,-41.7], "CE":[-5,-39], "DF":[-15.8,-47.9], "ES":[-19.5,-40.5],
    "GO":[-15.9,-49.8], "MA":[-5.5,-45], "MT":[-12.6,-56.1],
    "MS":[-20.5,-54.5], "MG":[-18.5,-44], "PA":[-4,-52],
    "PB":[-7.2,-36.7], "PR":[-24.8,-51.9], "PE":[-8.3,-37.8],
    "PI":[-7.1,-42.8], "RJ":[-22.9,-43.2], "RN":[-5.8,-36.5],
    "RS":[-30,-53], "RO":[-10.8,-63.9], "RR":[1.9,-61],
    "SC":[-27.3,-50], "SP":[-23.5,-46.6], "SE":[-10.6,-37.3],
    "TO":[-10.2,-48.3]
}

@app.route("/inmet")
def inmet_alerts():
    feed = feedparser.parse(INMET_RSS)
    alerts = []

    for e in feed.entries:
        title = e.get("title", "")
        desc = e.get("description", "")
        content = e.get("content", [{}])[0].get("value", "")

        texto = f"{title}\n\n{desc}\n\n{content}".strip()

        # Detecta UFs no texto
        ufs_encontradas = re.findall(r"\b(A[CLMP]|B[AE]|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO)\b", texto)

        # Se não achar UF → espalha para todas
        if not ufs_encontradas:
            ufs_encontradas = list(UF_COORDS.keys())

        # Emoji por tipo
        emoji = "⚠️"
        t = texto.lower()
        if "tornado" in t: emoji = "🌪️"
        elif "ciclone" in t: emoji = "🌀"
        elif "vermelho" in t: emoji = "⛈️"
        elif "laranja" in t: emoji = "🌩️"
        elif "amarelo" in t: emoji = "🌨️"
        elif "chuva" in t: emoji = "🌧️"

        for uf in ufs_encontradas:
            lat, lon = UF_COORDS.get(uf, [-15, -55])

            alerts.append({
                "fonte": "INMET",
                "uf": uf,
                "lat": lat,
                "lon": lon,
                "emoji": emoji,
                "texto": texto,
                "titulo": title,
                "publicado": e.get("published", "")
            })

    return jsonify(alerts)

if __name__ == "__main__":
    app.run()