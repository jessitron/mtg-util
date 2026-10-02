"""Anti-corruption layer: Scryfall's card JSON in, our Card out."""
import json
import time
import urllib.parse
import urllib.request
from typing import Callable, Iterator

from ..domain.card import Card
from ..domain.card_pool import CardPool

API = "https://api.scryfall.com/cards/search"
HEADERS = {"User-Agent": "mtg-util-prepared-cards/0.2", "Accept": "application/json"}
POLITE_DELAY_SECONDS = 0.1  # Scryfall asks for 50-100ms between requests


def card_from_scryfall(raw: dict) -> Card:
    faces = raw.get("card_faces") or []
    images = raw.get("image_uris") or (faces[0].get("image_uris") if faces else None) or {}
    return Card(
        name=raw["name"],
        mana_value=float(raw["cmc"]),
        mana_cost=raw.get("mana_cost", ""),
        type_line=raw.get("type_line", ""),
        image_url=images.get("normal", ""),
        page_url=raw["scryfall_uri"],
    )


def _http_get_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as response:
        return json.load(response)


class ScryfallCatalog:
    def __init__(self, query: str, get_json: Callable[[str], dict] = _http_get_json, sleep=time.sleep):
        self._query = query
        self._get_json = get_json
        self._sleep = sleep

    def pool(self) -> CardPool:
        return CardPool.of(card_from_scryfall(raw) for raw in self._raw_cards())

    def refresh(self) -> CardPool:
        return self.pool()  # Scryfall has no memory

    def _raw_cards(self) -> Iterator[dict]:
        url = API + "?" + urllib.parse.urlencode({"q": self._query, "order": "cmc"})
        while url:
            page = self._get_json(url)
            yield from page["data"]
            url = page.get("next_page")
            if url:
                self._sleep(POLITE_DELAY_SECONDS)
