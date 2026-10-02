#!/usr/bin/env python3
"""Fetch cards matching a Scryfall query, serve a checklist page, write picks in Archidekt import format."""
import json, os, sys, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
QUERY = os.environ.get("QUERY", "o:prepared")
PORT = int(os.environ.get("PORT", "8765"))
CACHE = os.path.join(HERE, "cards.json")
OUTPUT = os.path.join(HERE, "selected.txt")
HEADERS = {"User-Agent": "mtg-util-prepared-cards/0.1", "Accept": "application/json"}


def fetch_cards():
    url = "https://api.scryfall.com/cards/search?" + urllib.parse.urlencode({"q": QUERY, "order": "cmc"})
    cards = []
    while url:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as r:
            page = json.load(r)
        cards += page["data"]
        url = page.get("next_page")
        if url:
            time.sleep(0.1)  # Scryfall asks for 50-100ms between requests
    return cards


def slim(c):
    faces = c.get("card_faces") or []
    image = (c.get("image_uris") or (faces[0].get("image_uris") if faces else {}) or {}).get("normal", "")
    return {"name": c["name"], "cmc": c["cmc"], "image": image, "mana_cost": c.get("mana_cost", ""),
            "type_line": c.get("type_line", ""), "uri": c["scryfall_uri"]}


def load_cards(refresh=False):
    if refresh or not os.path.exists(CACHE):
        cards = sorted((slim(c) for c in fetch_cards()), key=lambda c: (c["cmc"], c["name"]))
        with open(CACHE, "w") as f:
            json.dump({"query": QUERY, "cards": cards}, f, indent=1)
    with open(CACHE) as f:
        return json.load(f)


class Handler(BaseHTTPRequestHandler):
    def send(self, body, ctype="application/json", code=200):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self.send(f.read(), "text/html; charset=utf-8")
        elif self.path == "/cards":
            self.send(json.dumps(load_cards()))
        elif self.path == "/refresh":
            self.send(json.dumps(load_cards(refresh=True)))
        elif self.path == "/selected":
            names = open(OUTPUT).read().splitlines() if os.path.exists(OUTPUT) else []
            self.send(json.dumps([n.split(" ", 1)[1] for n in names if " " in n]))
        else:
            self.send("not found", "text/plain", 404)

    def do_POST(self):
        if self.path != "/save":
            return self.send("not found", "text/plain", 404)
        names = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with open(OUTPUT, "w") as f:
            f.write("".join(f"1 {n}\n" for n in names))
        self.send(json.dumps({"saved": len(names), "file": OUTPUT}))


if __name__ == "__main__":
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        sys.exit(f"Can't listen on port {PORT}: {e}. Something else is using it; try PORT=8766 ./run")
    n = len(load_cards()["cards"])
    print(f"{n} cards for query {QUERY!r}. http://localhost:{PORT}  (writes {OUTPUT})", file=sys.stderr)
    server.serve_forever()
