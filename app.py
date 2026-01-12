import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify

RSS_INDEX = "https://apiprevmet3.inmet.gov.br/avisos/rss/"
CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

app = Flask(__name__)

def get_cap_xml():
    # 1) Busca índice RSS
    rss_resp = requests.get(
        RSS_INDEX,
        allow_redirects=True,
        timeout=20,
        headers={"User-Agent": "INMET-Client"}
    )

    rss_root = ET.fromstring(rss_resp.content)

    # 2) Extrai link do aviso ativo
    channel = rss_root.find("channel")
    if channel is None:
        return None

    item = channel.find("item")
    if item is None:
        return None

    link = item.findtext("link")
    if not link:
        return None

    # 3) Busca XML CAP real
    cap_resp = requests.get(
        link,
        timeout=20,
        headers={"User-Agent": "INMET-Client"}
    )

    return cap_resp.content


def parse_cap(xml_bytes):
    root = ET.fromstring(xml_bytes)
    conteudo = []

    for info in root.findall("cap:info", CAP_NS):
        alerta = {}

        def get(tag):
            el = info.find(f"cap:{tag}", CAP_NS)
            return el.text.strip() if el is not None and el.text else None

        campos = {
            "evento": "event",
            "titulo": "headline",
            "descricao": "description",
            "instrucao": "instruction",
            "severidade": "severity",
            "urgencia": "urgency",
            "certeza": "certainty",
            "inicio": "onset",
            "fim": "expires"
        }

        for k, v in campos.items():
            val = get(v)
            if val:
                alerta[k] = val

        area = info.find("cap:area", CAP_NS)
        if area is not None:
            desc = area.find("cap:areaDesc", CAP_NS)
            poly = area.find("cap:polygon", CAP_NS)

            if desc is not None and desc.text:
                alerta["area"] = desc.text.strip()
            if poly is not None and poly.text:
                alerta["poligono"] = poly.text.strip()

        if alerta:
            conteudo.append(alerta)

    return conteudo


@app.route("/inmet", methods=["GET"])
def inmet():
    try:
        cap_xml = get_cap_xml()
        if not cap_xml:
            return jsonify({"fonte": "INMET", "conteudo": []})

        conteudo = parse_cap(cap_xml)

    except Exception:
        conteudo = []

    return jsonify({
        "fonte": "INMET",
        "conteudo": conteudo
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)