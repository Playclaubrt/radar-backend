import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify

INMET_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

app = Flask(__name__)

CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

def parse_cap(xml_bytes):
    root = ET.fromstring(xml_bytes)

    info = root.find("cap:info", CAP_NS)
    if info is None:
        return []

    alerta = {}

    def get(path):
        el = info.find(f"cap:{path}", CAP_NS)
        return el.text.strip() if el is not None and el.text else None

    alerta["evento"] = get("event")
    alerta["descricao"] = get("description")
    alerta["instrucao"] = get("instruction")
    alerta["severidade"] = get("severity")
    alerta["urgencia"] = get("urgency")
    alerta["certeza"] = get("certainty")
    alerta["inicio"] = get("onset")
    alerta["fim"] = get("expires")
    alerta["titulo"] = get("headline")
    alerta["link"] = get("web")

    area = info.find("cap:area", CAP_NS)
    if area is not None:
        area_desc = area.find("cap:areaDesc", CAP_NS)
        polygon = area.find("cap:polygon", CAP_NS)

        if area_desc is not None and area_desc.text:
            alerta["area"] = area_desc.text.strip()

        if polygon is not None and polygon.text:
            alerta["poligono"] = polygon.text.strip()

    # remove chaves vazias
    alerta = {k: v for k, v in alerta.items() if v}

    return [alerta] if alerta else []


@app.route("/inmet", methods=["GET"])
def inmet():
    resp = requests.get(
        INMET_URL,
        allow_redirects=True,
        timeout=20,
        headers={"User-Agent": "INMET-CAP-Client"}
    )

    conteudo = parse_cap(resp.content)

    return jsonify({
        "fonte": "INMET",
        "conteudo": conteudo
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)