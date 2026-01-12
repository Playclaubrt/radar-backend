import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify

INMET_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

app = Flask(__name__)

CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

def parse_rss(root):
    channel = root.find("channel")
    if channel is None:
        return []

    conteudo = []
    for item in channel.findall("item"):
        alerta = {}
        for tag in ["title", "description", "pubDate", "link"]:
            el = item.find(tag)
            if el is not None and el.text:
                alerta[tag] = el.text.strip()
        if alerta:
            conteudo.append(alerta)
    return conteudo


def parse_cap(root):
    conteudo = []
    for info in root.findall("cap:info", CAP_NS):
        alerta = {}

        def get(tag):
            el = info.find(f"cap:{tag}", CAP_NS)
            return el.text.strip() if el is not None and el.text else None

        fields = {
            "evento": "event",
            "descricao": "description",
            "instrucao": "instruction",
            "severidade": "severity",
            "urgencia": "urgency",
            "certeza": "certainty",
            "inicio": "onset",
            "fim": "expires",
            "titulo": "headline",
            "link": "web"
        }

        for k, v in fields.items():
            val = get(v)
            if val:
                alerta[k] = val

        area = info.find("cap:area", CAP_NS)
        if area is not None:
            area_desc = area.find("cap:areaDesc", CAP_NS)
            polygon = area.find("cap:polygon", CAP_NS)

            if area_desc is not None and area_desc.text:
                alerta["area"] = area_desc.text.strip()
            if polygon is not None and polygon.text:
                alerta["poligono"] = polygon.text.strip()

        if alerta:
            conteudo.append(alerta)

    return conteudo


@app.route("/inmet", methods=["GET"])
def inmet():
    resp = requests.get(
        INMET_URL,
        allow_redirects=True,
        timeout=20,
        headers={"User-Agent": "INMET-MultiParser"}
    )

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return jsonify({
            "fonte": "INMET",
            "conteudo": []
        })

    if root.tag.endswith("rss"):
        conteudo = parse_rss(root)
    elif root.tag.endswith("alert"):
        conteudo = parse_cap(root)
    else:
        conteudo = []

    return jsonify({
        "fonte": "INMET",
        "conteudo": conteudo
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)