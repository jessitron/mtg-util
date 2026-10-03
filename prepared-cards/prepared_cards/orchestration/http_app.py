"""The tiny local server: translates HTTP requests into CardPicker calls and the answers into JSON."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from ..domain.power_score import RankingEffort, ScoredCard
from .use_cases import CardPicker

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page", "index.html")


def ranked_to_json(ranked: tuple[ScoredCard, ...], effort: Optional[RankingEffort] = None) -> dict:
    data = {
        "cards": [
            {"name": s.card.name, "imageUrl": s.card.image_url, "gathererUrl": s.card.gatherer_url, "score": s.score}
            for s in ranked
        ]
    }
    if effort:
        data["effort"] = {"scorer": effort.scorer, "seconds": effort.seconds, "costUsd": effort.cost_usd}
    return data


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
                ranked = picker.ranked_candidates(refresh=self.path == "/api/refresh")
                self._send({"title": f"{len(ranked)} cards: {title}", **ranked_to_json(ranked, picker.effort(ranked))})
            elif self.path == "/api/selection":
                self._send(list(picker.current_selection().names))
            else:
                self._not_found()

        def do_POST(self):
            if self.path != "/api/selection":
                return self._not_found()
            names = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            text = picker.save_and_render(names)
            self._send({"saved": len(text.splitlines()), "file": output_description, "text": text})

    return HTTPServer(("127.0.0.1", port), Handler)
