import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

CACHE_TTL = 300  # 5 minutos
_cache = {
    "timestamp": 0,
    "dados": []
}

# -----------------------------
# LEITURA TOLERANTE DO INMET
# -----------------------------
def tentar_ler_rss():
    try:
        r = requests.get(INMET_RSS, headers=HEADERS, timeout=20)
    except Exception:
        return None

    if r.status_code != 200:
        return None

    texto = r.text.strip()

    # Aceita só se parecer XML
    if "<rss" not in texto and "<item" not in texto:
        return None

    return texto


# -----------------------------
# CONVERSÃO XML → JSON
# -----------------------------
def converter(xml_texto):
    try:
        root = ET.fromstring(xml_texto)
    except Exception:
        return []

    alertas = []

    for item in root.findall(".//item"):
        titulo = item.findtext("title", "").strip()
        descricao = item.findtext("description", "").strip()
        link = item.findtext("link", "").strip()

        if not titulo:
            continue

        alerta = {
            "titulo": titulo,
            "descricao": descricao,
            "link": link,
            "uf": "DESCONHECIDO"
        }

        for uf in [
            "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
            "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
            "RS","RO","RR","SC","SP","SE","TO"
        ]:
            if uf in titulo or uf in descricao:
                alerta["uf"] = uf
                break

        alertas.append(alerta)

    return alertas


# -----------------------------
# CACHE + FALLBACK
# -----------------------------
def obter_alertas():
    agora = time.time()

    # Cache válido
    if agora - _cache["timestamp"] < CACHE_TTL:
        return _cache["dados"], True, "cache"

    xml_texto = tentar_ler_rss()

    # Se INMET falhar → usa último cache
    if xml_texto is None:
        return _cache["dados"], True, "fallback"

    dados = converter(xml_texto)

    _cache["timestamp"] = agora
    _cache["dados"] = dados

    return dados, False, "inmet"


# -----------------------------
# ROTAS
# -----------------------------
@app.route("/")
def status():
    return jsonify({
        "status": "ok",
        "fonte": "INMET",
        "backend": "RSS tolerante + cache"
    })


@app.route("/inmet/textual")
def textual():
    alertas, cache, origem = obter_alertas()

    return jsonify({
        "fonte": "INMET",
        "modo": "textual",
        "origem": origem,
        "cache": cache,
        "total": len(alertas),
        "alertas": alertas
    })


@app.route("/inmet/geografico")
def geografico():
    alertas, cache, origem = obter_alertas()

    por_uf = {}
    for a in alertas:
        por_uf.setdefault(a["uf"], []).append(a)

    return jsonify({
        "fonte": "INMET",
        "modo": "geografico",
        "origem": origem,
        "cache": cache,
        "ufs": por_uf
    })