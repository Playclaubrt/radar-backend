import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify
from datetime import datetime
import time

INMET_RSS_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"
CACHE_TTL = 50  # segundos

app = Flask(__name__)

_cache = {
    "timestamp": 0,
    "data": None
}

def fetch_inmet_rss():
    resp = requests.get(
        INMET_RSS_URL,
        timeout=15,
        allow_redirects=True,
        headers={
            "User-Agent": "INMET-RSS-Client"
        }
    )

    content_type = resp.headers.get("Content-Type", "")
    if "xml" not in content_type.lower():
        raise ValueError("Resposta não XML do INMET")

    root = ET.fromstring(resp.content)

    channel = root.find("channel")
    if channel is None:
        return []

    alertas = []
    for item in channel.findall("item"):
        alerta = {}
        for child in item:
            tag = child.tag.split("}")[-1]
            alerta[tag] = child.text.strip() if child.text else None
        alertas.append(alerta)

    return alertas


@app.route("/inmet", methods=["GET"])
def inmet():
    now = time.time()

    if _cache["data"] and (now - _cache["timestamp"] < CACHE_TTL):
        return jsonify(_cache["data"])

    try:
        alertas = fetch_inmet_rss()
        data = {
            "alertas": alertas,
            "total": len(alertas),
            "fonte": "INMET",
            "cache": False,
            "atualizado_em": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        data = {
            "alertas": [],
            "total": 0,
            "fonte": "INMET",
            "cache": False,
            "erro": str(e),
            "atualizado_em": datetime.utcnow().isoformat() + "Z"
        }

    _cache["timestamp"] = now
    _cache["data"] = data

    return jsonify(data)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)