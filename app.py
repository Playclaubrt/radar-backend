import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

INMET_URL = "https://apiprevmet3.inmet.gov.br/alertas/ativos"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

def ler_alertas():
    r = requests.get(INMET_URL, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        raise Exception("INMET indisponivel")

    if not r.text.strip():
        raise Exception("Resposta vazia do INMET")

    content_type = r.headers.get("Content-Type", "")

    if "application/json" not in content_type:
        raise Exception("INMET nao retornou JSON")

    try:
        dados = r.json()
    except Exception:
        raise Exception("JSON invalido do INMET")

    if not isinstance(dados, list):
        raise Exception("Formato inesperado do INMET")

    alertas = []

    for a in dados:
        alertas.append({
            "titulo": a.get("titulo", ""),
            "descricao": a.get("descricao", ""),
            "severidade": a.get("severidade", ""),
            "uf": a.get("uf", ""),
            "inicio": a.get("inicio", ""),
            "fim": a.get("fim", "")
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

    if modo == "geografico":
        por_uf = {}
        for a in alertas:
            uf = a["uf"] or "DESCONHECIDO"
            por_uf.setdefault(uf, []).append(a)

        return jsonify({
            "fonte": "INMET",
            "modo": "geografico",
            "ufs": por_uf
        })

    return jsonify({
        "fonte": "INMET",
        "modo": "textual",
        "total": len(alertas),
        "alertas": alertas
    })