import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify

INMET_RSS_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

app = Flask(__name__)

def parse_inmet_xml(xml_bytes):
    root = ET.fromstring(xml_bytes)

    # detecta namespace automaticamente
    ns = {}
    if root.tag.startswith("{"):
        ns["ns"] = root.tag.split("}")[0].strip("{")

    channel = root.find("ns:channel", ns) if ns else root.find("channel")
    if channel is None:
        return []

    conteudo = []

    items = channel.findall("ns:item", ns) if ns else channel.findall("item")
    for item in items:
        alerta = {}

        def get(tag):
            el = item.find(f"ns:{tag}", ns) if ns else item.find(tag)
            return el.text.strip() if el is not None and el.text else None

        titulo = get("title")
        descricao = get("description")
        data = get("pubDate")
        link = get("link")

        if titulo:
            alerta["titulo"] = titulo
        if descricao:
            alerta["descricao"] = descricao
        if data:
            alerta["data"] = data
        if link:
            alerta["link"] = link

        if alerta:
            conteudo.append(alerta)

    return conteudo


@app.route("/inmet", methods=["GET"])
def inmet():
    resp = requests.get(
        INMET_RSS_URL,
        allow_redirects=True,
        timeout=20,
        headers={"User-Agent": "INMET-Client"}
    )

    conteudo = parse_inmet_xml(resp.content)

    return jsonify({
        "fonte": "INMET",
        "conteudo": conteudo
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)