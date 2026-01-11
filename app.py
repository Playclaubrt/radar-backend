import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"

HEADERS = {
    "User-Agent": "Mozilla/5.0 INMET-Client"
}

def ler_alertas():
    r = requests.get(INMET_RSS, headers=HEADERS, timeout=20)

    # Se o INMET estiver fora do ar
    if r.status_code != 200:
        raise Exception("INMET indisponivel")

    # Garante que é XML
    if "<rss" not in r.text and "<feed" not in r.text:
        raise Exception("Resposta nao XML do INMET")

    root = ET.fromstring(r.text)
    alertas = []

    for item in root.findall(".//item"):
        titulo = item.findtext("title", "").strip()
        descricao = item.findtext("description", "").strip()
        link = item.findtext("link", "").strip()

        if titulo:
            alertas.append({
                "titulo": titulo,
                "descricao": descricao,
                "link": link
            })

    return alertas


@app.route("/")
def status():
    return jsonify({"status": "ok", "fonte": "INMET"})


@app.route("/inmet")
def inmet():
    modo = request.args.get("modo", "textual")

    try:
        alertas = ler_alertas()
    except Exception as e:
        return jsonify({
            "fonte": "INMET",
            "erro": str(e)
        }), 503

    return jsonify({
        "fonte": "INMET",
        "modo": modo,
        "total": len(alertas),
        "alertas": alertas
    })