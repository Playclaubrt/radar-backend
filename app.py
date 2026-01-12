from flask import Flask, jsonify, request
import requests
import feedparser
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

CACHE = {
    "timestamp": 0,
    "alertas": []
}

RSS_URL = "https://apiprevmet3.inmet.gov.br/alertas/rss"
PORTAL_URL = "https://portal.inmet.gov.br/alertas"

CACHE_TTL = 300  # 5 minutos


def ler_rss():
    feed = feedparser.parse(RSS_URL)
    alertas = []

    if not feed.entries:
        return alertas

    for item in feed.entries:
        alertas.append({
            "titulo": item.get("title", ""),
            "descricao": item.get("summary", ""),
            "link": item.get("link", ""),
            "inicio": item.get("published", ""),
            "origem": "rss"
        })

    return alertas


def ler_portal():
    resp = requests.get(PORTAL_URL, timeout=10)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    alertas = []

    cards = soup.select(".alerta-item")
    for card in cards:
        titulo = card.get_text(strip=True)
        alertas.append({
            "titulo": titulo,
            "descricao": titulo,
            "link": PORTAL_URL,
            "inicio": "",
            "origem": "portal"
        })

    return alertas


def obter_alertas():
    global CACHE

    agora = time.time()

    if agora - CACHE["timestamp"] < CACHE_TTL:
        return CACHE["alertas"], True

    alertas = ler_rss()

    if not alertas:
        alertas = ler_portal()

    if alertas:
        CACHE = {
            "timestamp": agora,
            "alertas": alertas
        }
        return alertas, False

    return CACHE["alertas"], True


@app.route("/inmet")
def inmet():
    modo = request.args.get("modo", "textual")
    alertas, cache = obter_alertas()

    if modo == "geografico":
        ufs = {}
        for a in alertas:
            uf = "BR"
            ufs.setdefault(uf, []).append(a)

        return jsonify({
            "fonte": "INMET",
            "modo": "geografico",
            "cache": cache,
            "total": sum(len(v) for v in ufs.values()),
            "ufs": ufs
        })

    return jsonify({
        "fonte": "INMET",
        "modo": "textual",
        "cache": cache,
        "total": len(alertas),
        "alertas": alertas
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)