#!/usr/bin/env python3
"""Composition root: choose the adapters, hand them to the use cases, start the server."""
import os
import sys

from prepared_cards.adapters.archidekt_file import ArchidektImportFile
from prepared_cards.adapters.cached_catalog import CachedCatalog
from prepared_cards.adapters.scryfall_catalog import ScryfallCatalog
from prepared_cards.orchestration.http_app import make_server
from prepared_cards.orchestration.use_cases import CardPicker

HERE = os.path.dirname(os.path.abspath(__file__))
QUERY = os.environ.get("QUERY", "o:prepared")
PORT = int(os.environ.get("PORT", "8765"))


def main():
    catalog = CachedCatalog(ScryfallCatalog(QUERY), os.path.join(HERE, "scryfall-cache.json"))
    selection_file = ArchidektImportFile(os.path.join(HERE, "selected.txt"))
    picker = CardPicker(catalog, selection_file)
    try:
        server = make_server(picker, QUERY, PORT, selection_file.path)
    except OSError:
        sys.exit(
            f"Port {PORT} is already in use, so the server can't start.\n"
            f"Most likely a previous copy of this server is still running.\n"
            f"  See what has the port:  lsof -i :{PORT}\n"
            f"  Stop it:                kill $(lsof -ti :{PORT})\n"
            f"  Or use another port:    PORT={PORT + 1} ./run"
        )
    print(f"{len(picker.candidates())} cards for query {QUERY!r}. http://localhost:{PORT}  (writes {selection_file.path})", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
