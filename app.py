import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (INMET-RSS-Client)"
}

# CACHE EM MEMÓRIA
CACHE_TTL = 300  # 5 minutos
_cache_data = None
_cache_time = 0


def fetch_rss():
    r = requests.get(INMET_RSS, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        raise Exception("HTTP diferente de 200")
    if "<rss" not in r.text:
        raise Exception("Resposta nao RSS")
    return r.text


def parse_rss(xml_text):
    root = ET.fromstring(xml_text)
    alertas = []

    for item in root.findall(".//item"):
        titulo = item.findtext("title", "").strip()
        descricao = item.findtext("description", "").strip()
        link = item.findtext("link", "").strip()

        if not titulo:
            continue

        # Tentativa simples de extrair UF do texto
        uf = ""
        for sigla in [
            "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
            "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
            "RS","RO","RR","SC","SP","SE","TO"
        ]:
            if sigla in titulo or sigla in descricao:
                uf = sigla
                break

        alertas.append({
            "titulo": titulo,
            "descricao": descricao,
            "link": link,
            "uf": uf
        })

    return alertas


def get_alertas():
    global _cache_data, _cache_time

    agora = time.time()
    if _cache_data and agora - _cache_time < CACHE_TTL:
        return _cache_data, True

    xml = fetch_rss()
    alertas = parse_rss(xml)

    _cache_data = alertas
    _cache_time = agora

    return alertas, False


@app.route("/")
def status():
    return jsonify({
        "status": "ok",
        "fonte": "INMET",
        "cache_segundos": CACHE_TTL
    })


@app.route("/inmet")
def inmet():
    modo = request.args.get("modo", "textual")

    try:
        alertas, cache = get_alertas()
    except Exception as e:
        return jsonify({
            "fonte": "INMET",
            "erro": "Falha ao obter alertas",
            "detalhe": str(e)
        }), 503

    if modo == "geografico":
        por_uf = {}
        for a in alertas:
            uf = a["uf"] or "DESCONHECIDO"
            por_uf.setdefault(uf, []).append(a)

        return jsonify({
            "fonte": "INMET",
            "modo": "geografico",
            "cache": cache,
            "ufs": por_uf
        })

    return jsonify({
        "fonte": "INMET",
        "modo": "textual",
        "cache": cache,
        "total": len(alertas),
        "alertas": alertas
    })