import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify

INMET_RSS_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

app = Flask(__name__)

def parse_inmet_xml(xml_bytes):
    root = ET.fromstring(xml_bytes)

    channel = root.find("channel")
    if channel is None:
        return []

    alertas = []

    for item in channel.findall("item"):
        alerta = {}

        title = item.findtext("title")
        description = item.findtext("description")
        pubDate = item.findtext("pubDate")
        link = item.findtext("link")

        if title:
            alerta["titulo"] = title
        if description:
            alerta["descricao"] = description
        if pubDate:
            alerta["data"] = pubDate
        if link:
            alerta["link"] = link

        alertas.append(alerta)

    return alertas


@app.route("/inmet", methods=["GET"])
def inmet():
    resp = requests.get(
        INMET_RSS_URL,
        allow_redirects=True,
        timeout=15,
        headers={"User-Agent": "INMET-Client"}
    )

    alertas = parse_inmet_xml(resp.content)

    return jsonify({
        "fonte": "INMET",
        "conteudo": alertas
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)