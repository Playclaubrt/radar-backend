import requests
from flask import Flask, Response

INMET_RSS_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

app = Flask(__name__)

@app.route("/inmet", methods=["GET"])
def inmet():
    resp = requests.get(
        INMET_RSS_URL,
        allow_redirects=True,
        timeout=15,
        headers={
            "User-Agent": "INMET-Proxy"
        }
    )

    return Response(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("Content-Type", "application/xml")
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)