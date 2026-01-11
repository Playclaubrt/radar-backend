import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"

def ler_alertas():
    r = requests.get(INMET_RSS, timeout=15)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    alertas = []

    for item in root.findall(".//item"):
        titulo = item.findtext("title", "").strip()
        descricao = item.findtext("description", "").strip()
        link = item.findtext("link", "").strip()

        alertas.append({
            "titulo": titulo,
            "descricao": descricao,
            "link": link
        })

    return alertas


@app.route("/")
def home():
    return jsonify({"status": "ok", "fonte": "INMET"})


@app.route("/inmet")
def inmet():
    modo = request.args.get("modo", "textual")

    try:
        alertas = ler_alertas()
    except Exception as e:
        return jsonify({"erro": "falha ao ler INMET"}), 500

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