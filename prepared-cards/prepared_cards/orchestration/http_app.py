"""The tiny local server: translates HTTP requests into CardPicker calls and the answers into JSON."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..domain.card_pool import CardPool, ManaValueGroup
from .use_cases import CardPicker

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page", "index.html")


def _label(group: ManaValueGroup) -> str:
    mv = group.mana_value
    return f"Mana value {int(mv) if mv == int(mv) else mv}"


def pool_to_json(pool: CardPool) -> dict:
    return {
        "groups": [
            {
                "label": _label(g),
                "cards": [{"name": c.name, "imageUrl": c.image_url, "pageUrl": c.page_url} for c in g.cards],
            }
            for g in pool.by_mana_value()
        ]
    }


def make_server(picker: CardPicker, title: str, port: int, output_description: str) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type="application/json", status=200):
            data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body)).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _not_found(self):
            self._send("not found", "text/plain", 404)

        def do_GET(self):
            if self.path == "/":
                with open(PAGE, "rb") as f:
                    self._send(f.read(), "text/html; charset=utf-8")
            elif self.path in ("/api/cards", "/api/refresh"):
                pool = picker.candidates(refresh=self.path == "/api/refresh")
                self._send({"title": f"{len(pool)} cards: {title}", **pool_to_json(pool)})
            elif self.path == "/api/selection":
                self._send(list(picker.current_selection().names))
            else:
                self._not_found()

        def do_POST(self):
            if self.path != "/api/selection":
                return self._not_found()
            names = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            saved = picker.save_selection(names)
            self._send({"saved": len(saved), "file": output_description})

    return HTTPServer(("127.0.0.1", port), Handler)
