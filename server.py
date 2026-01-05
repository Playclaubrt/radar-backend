from flask import Flask, jsonify
from flask_cors import CORS
import feedparser
import re

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/avisos/rss"

# Lista oficial de UFs
UFS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
]

def extrair_ufs(texto):
    texto = texto.upper()
    encontradas = []
    for uf in UFS:
        if re.search(rf"\b{uf}\b", texto):
            encontradas.append(uf)
    return encontradas

@app.route("/")
def home():
    return "Backend INMET online"

@app.route("/inmet")
def inmet_alertas():
    feed = feedparser.parse(INMET_RSS)

    alertas = []

    for entry in feed.entries:
        titulo = entry.get("title", "")
        descricao = entry.get("summary", "")
        publicado = entry.get("published", "")

        # Extrai UFs do texto (textual)
        ufs = extrair_ufs(titulo + " " + descricao)

        alerta = {
            "titulo": titulo,
            "descricao": descricao,
            "publicado": publicado,
            "ufs": ufs,              # 👈 ESSENCIAL
            "fonte": "INMET"
        }

        alertas.append(alerta)

    return jsonify(alertas)