import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"

def ler_alertas():
    resposta = requests.get(INMET_RSS, timeout=10)
    resposta.raise_for_status()

    root = ET.fromstring(resposta.content)
    alertas = []

    for item in root.iter("item"):
        titulo = item.findtext("title", "").strip()
        descricao = item.findtext("description", "").strip()
        link = item.findtext("link", "").strip()

        alertas.append({
            "titulo": titulo,
            "descricao": descricao,
            "link": link
        })

    return alertas


@app.route("/inmet")
def inmet():
    modo = request.args.get("modo", "textual")
    alertas = ler_alertas()

    if modo == "textual":
        return jsonify({
            "fonte": "INMET",
            "modo": "textual",
            "alertas": alertas
        })

    if modo == "geografico":
        return jsonify({
            "fonte": "INMET",
            "modo": "geografico",
            "alertas": alertas
        })

    return jsonify({"erro": "modo invalido"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)