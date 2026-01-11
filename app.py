import time
import re
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_RSS = "https://apiprevmet3.inmet.gov.br/alertas/rss"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CACHE_TTL = 300  # 5 minutos
_cache = {
    "timestamp": 0,
    "dados": []
}

UFS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
]

# -------------------------------------------------
# LEITURA TOLERANTE DO RSS
# -------------------------------------------------
def tentar_ler_rss():
    try:
        r = requests.get(INMET_RSS, headers=HEADERS, timeout=20)
    except Exception:
        return None

    if r.status_code != 200:
        return None

    texto = r.text.strip()

    if "<item>" not in texto:
        return None

    return texto


# -------------------------------------------------
# EXTRAÇÃO COMPLETA DO ALERTA
# -------------------------------------------------
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
        pubdate = item.findtext("pubDate", "").strip()

        if not titulo:
            continue

        # Severidade (texto)
        severidade = "DESCONHECIDA"
        if "PERIGO" in titulo.upper():
            severidade = "PERIGO"
        if "POTENCIAL" in titulo.upper():
            severidade = "PERIGO POTENCIAL"

        # Tipo do evento (chuva, vento, etc.)
        tipo = "DESCONHECIDO"
        for t in ["CHUVA", "VENTO", "GEADA", "ONDA DE CALOR", "FRIO"]:
            if t in titulo.upper():
                tipo = t
                break

        # UFs citadas
        ufs_encontradas = []
        for uf in UFS:
            if uf in titulo or uf in descricao:
                ufs_encontradas.append(uf)

        if not ufs_encontradas:
            ufs_encontradas = ["DESCONHECIDO"]

        alerta = {
            "titulo": titulo,
            "descricao_completa": descricao,
            "tipo": tipo,
            "severidade": severidade,
            "ufs": ufs_encontradas,
            "link": link,
            "publicado_em": pubdate
        }

        alertas.append(alerta)

    return alertas


# -------------------------------------------------
# CACHE + FALLBACK
# -------------------------------------------------
def obter_alertas():
    agora = time.time()

    if agora - _cache["timestamp"] < CACHE_TTL:
        return _cache["dados"], True, "cache"

    xml = tentar_ler_rss()

    if xml is None:
        return _cache["dados"], True, "fallback"

    dados = converter(xml)

    _cache["timestamp"] = agora
    _cache["dados"] = dados

    return dados, False, "inmet"


# -------------------------------------------------
# ROTAS
# -------------------------------------------------
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

    por_uf = {uf: [] for uf in UFS}

    for a in alertas:
        for uf in a["ufs"]:
            if uf in por_uf:
                por_uf[uf].append(a)

    return jsonify({
        "fonte": "INMET",
        "modo": "geografico",
        "origem": origem,
        "cache": cache,
        "ufs": por_uf
    })