from flask import Flask, jsonify, request
import feedparser
import time
import threading
import os

app = Flask(__name__)

# ================= CONFIG =================
FEED_GERAL = "https://apiprevmet3.inmet.gov.br/alertas/rss"
FEED_AVISO = "https://apiprevmet3.inmet.gov.br/avisos/rss/{}"
INTERVALO = 50  # segundos

# ================= CACHE =================
CACHE = {
    "timestamp": 0,
    "avisos": {}
}

# ================= FUNÇÕES =================
def extrair_id(link):
    # ex: /avisos/rss/45736
    return link.rstrip("/").split("/")[-1]


def ler_feed_geral():
    feed = feedparser.parse(FEED_GERAL)
    ids = set()

    for item in feed.entries:
        link = item.get("link", "")
        if "/avisos/rss/" in link:
            ids.add(extrair_id(link))

    return ids


def ler_aviso(id_aviso):
    feed = feedparser.parse(FEED_AVISO.format(id_aviso))
    if not feed.entries:
        return None

    item = feed.entries[0]

    return {
        "id": id_aviso,
        "titulo": item.get("title", ""),
        "descricao": item.get("summary", ""),
        "link": item.get("link", ""),
        "publicado": item.get("published", ""),
        "origem": "INMET"
    }


def atualizar_cache():
    global CACHE

    while True:
        try:
            ids_atuais = ler_feed_geral()
            avisos_novos = {}

            for id_aviso in ids_atuais:
                aviso = ler_aviso(id_aviso)
                if aviso:
                    avisos_novos[id_aviso] = aviso

            CACHE["avisos"] = avisos_novos
            CACHE["timestamp"] = int(time.time())

        except Exception as e:
            print("Erro atualização INMET:", e)

        time.sleep(INTERVALO)


# ================= THREAD =================
thread = threading.Thread(target=atualizar_cache, daemon=True)
thread.start()

# ================= ROTAS =================
@app.route("/inmet")
def inmet_textual():
    return jsonify({
        "fonte": "INMET",
        "modo": "textual",
        "tempo_real": True,
        "intervalo_segundos": INTERVALO,
        "total": len(CACHE["avisos"]),
        "alertas": list(CACHE["avisos"].values()),
        "ultima_atualizacao": CACHE["timestamp"]
    })


@app.route("/inmet/geografico")
def inmet_geografico():
    ufs = {}

    for aviso in CACHE["avisos"].values():
        # INMET nem sempre separa UF no RSS
        # então agrupamos como BR até ter GeoRSS
        ufs.setdefault("BR", []).append(aviso)

    return jsonify({
        "fonte": "INMET",
        "modo": "geografico",
        "tempo_real": True,
        "intervalo_segundos": INTERVALO,
        "total": sum(len(v) for v in ufs.values()),
        "ufs": ufs,
        "ultima_atualizacao": CACHE["timestamp"]
    })


# ================= MAIN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)