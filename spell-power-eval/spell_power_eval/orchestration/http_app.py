"""The tiny local server: translates HTTP requests into RunStore reads and the answers into JSON."""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..domain.ports import RunStore

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_page.html")
RUN_NAME = re.compile(r"^\d{8}T\d{6}Z\.json$")  # the only names that reach the store, so no path can escape results/
RUN_ROUTE = "/api/runs/"


def run_summaries(store: RunStore) -> list[dict]:
    """Newest first. A file that isn't a readable run still lists, so the page can say so."""
    summaries = []
    for name in store.names():
        if not RUN_NAME.match(name):
            continue
        try:
            run = store.read(name) or {}
            summaries.append({"file": name, "cards": len(run["cards"]), "arms": list(run["scorecards"])})
        except (KeyError, TypeError, ValueError):
            summaries.append({"file": name, "cards": None, "arms": []})
    return summaries


def make_server(store: RunStore, port: int) -> HTTPServer:
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
            path = self.path.split("?")[0]
            if path == "/":
                with open(PAGE, "rb") as f:
                    self._send(f.read(), "text/html; charset=utf-8")
            elif path == "/api/runs":
                self._send(run_summaries(store))
            elif path.startswith(RUN_ROUTE):
                name = path[len(RUN_ROUTE):]
                run = store.read(name) if RUN_NAME.match(name) else None
                self._not_found() if run is None else self._send(run)
            else:
                self._not_found()

        def log_message(self, *args):
            pass

    return HTTPServer(("127.0.0.1", port), Handler)
