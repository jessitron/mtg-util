#!/usr/bin/env python3
"""Composition root: choose the adapters, hand them to the use cases, start the server."""
import os
import sys

from prepared_cards.adapters.archidekt_file import ArchidektImportFile
from prepared_cards.adapters.cached_catalog import CachedCatalog
from prepared_cards.adapters.cached_power_score import CachedPowerScore
from prepared_cards.adapters.jev_power_score import JevPowerScore
from prepared_cards.adapters.llm_power_score import LlmPowerScore
from prepared_cards.adapters.mtgjson_rules_text import MtgjsonRulesText
from prepared_cards.adapters.scryfall_catalog import ScryfallCatalog
from prepared_cards.orchestration.http_app import make_server
from prepared_cards.orchestration.use_cases import CardPicker

HERE = os.path.dirname(os.path.abspath(__file__))
QUERY = os.environ.get("QUERY", "o:prepared")
PORT = int(os.environ.get("PORT", "8765"))
MODEL = os.environ.get("POWER_MODEL", "claude-haiku-4-5")
# The MTGJSON database lives in the main checkout; worktrees don't have it.
MTGJSON_DB = os.environ.get("MTGJSON_DB", "/Users/jessitron/code/jessitron/mtg-util/mtgjson/data/AllPrintings.sqlite")


def main():
    catalog = CachedCatalog(ScryfallCatalog(QUERY), os.path.join(HERE, "scryfall-cache.json"))
    rules_text = MtgjsonRulesText(MTGJSON_DB)
    scorer = JevPowerScore(rules_text, MODEL) if MODEL.startswith("jev") else LlmPowerScore(rules_text, MODEL)
    power = CachedPowerScore(scorer, os.path.join(HERE, f"power-scores-{MODEL}.json"))  # named for the model, so scores from different scorers never mix
    selection_file = ArchidektImportFile(os.path.join(HERE, "selected.txt"))
    picker = CardPicker(catalog, power, selection_file)
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
