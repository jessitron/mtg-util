"""Anti-corruption layer: Scryfall's card JSON in, our Card out. One batched request, cached on disk."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Callable, Optional, Sequence

from ..domain.card import Card

COLLECTION_URL = "https://api.scryfall.com/cards/collection"
SEARCH_URL = "https://api.scryfall.com/cards/search"
BATCH_SIZE = 75  # Scryfall's limit per collection request
HEADERS = {"User-Agent": "mtg-util-spell-power-eval/0.1", "Accept": "application/json", "Content-Type": "application/json"}
POLITE_DELAY_SECONDS = 0.1  # Scryfall asks for 50-100ms between requests


SPELL_NOTE = (
    "This is the spell half of a two-faced card whose other half is a creature. Judge the spell alone, at its own "
    "mana cost, as if it were a stand-alone card. Ignore the creature."
)


def _mana_value(mana_cost: str) -> float:
    """A mana cost's total: a number counts as itself, any other symbol (colored, hybrid, Phyrexian) as 1, {X} as 0."""
    total = 0
    for symbol in re.findall(r"\{([^}]*)\}", mana_cost):
        total += int(symbol) if symbol.isdigit() else 0 if symbol == "X" else 1
    return float(total)


def _spell_from_prepared(raw: dict, spell: dict) -> Card:
    """A prepared creature's spell face as a card of its own. Scryfall's `cmc` is the creature's, so the value comes from the spell's cost."""
    cost = spell.get("mana_cost", "")
    return Card(
        name=spell["name"],
        mana_cost=cost,
        mana_value=_mana_value(cost),
        type_line=spell.get("type_line", ""),
        oracle_text=spell.get("oracle_text", ""),
        image_url=(raw.get("image_uris") or spell.get("image_uris") or {}).get("normal", ""),
        edhrec_rank=raw.get("edhrec_rank"),
        note=SPELL_NOTE,
    )


def card_from_scryfall(raw: dict, asked: Optional[str] = None) -> Card:
    """`asked` is the name the label used. Naming the spell face of a prepared card gets you the spell alone; any other name, the whole card."""
    faces = raw.get("card_faces") or []
    if raw.get("layout") == "prepare" and len(faces) == 2 and asked and asked.lower() == faces[1]["name"].lower():
        return _spell_from_prepared(raw, faces[1])
    front = faces[0] if faces else {}
    oracle = raw.get("oracle_text") or "\n//\n".join(face.get("oracle_text", "") for face in faces)
    return Card(
        name=raw["name"],
        mana_cost=raw.get("mana_cost") or front.get("mana_cost", ""),
        mana_value=float(raw["cmc"]),
        type_line=raw.get("type_line", ""),
        oracle_text=oracle,
        power=raw.get("power") or front.get("power"),
        toughness=raw.get("toughness") or front.get("toughness"),
        loyalty=raw.get("loyalty") or front.get("loyalty"),
        image_url=(raw.get("image_uris") or front.get("image_uris") or {}).get("normal", ""),
        edhrec_rank=raw.get("edhrec_rank"),
    )


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as response:
        return json.load(response)


def _post_json(url: str, body: dict) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


class ScryfallCatalog:
    """Looks cards up by exact name. The cache keeps Scryfall's raw JSON, so changing how we read a card needs no refetch."""

    def __init__(self, cache_path: Optional[str] = None, post_json: Callable[[str, dict], dict] = _post_json, sleep=time.sleep, get_json: Callable[[str], dict] = _get_json):
        self._cache_path = cache_path
        self._post_json = post_json
        self._get_json = get_json
        self._sleep = sleep

    def find(self, names: Sequence[str]) -> list[Card]:
        cache = self._load_cache()
        missing = [name for name in names if name.lower() not in cache]
        if missing:
            self._fetch_into(cache, missing)
            self._save_cache(cache)
        not_found = [name for name in names if name.lower() not in cache]
        if not_found:
            raise LookupError("Scryfall doesn't know: " + ", ".join(not_found))
        return [card_from_scryfall(cache[name.lower()], asked=name) for name in names]

    def _fetch_into(self, cache: dict, names: list[str]) -> None:
        for start in range(0, len(names), BATCH_SIZE):
            if start:
                self._sleep(POLITE_DELAY_SECONDS)
            batch = names[start : start + BATCH_SIZE]
            page = self._post_json(COLLECTION_URL, {"identifiers": [{"name": name} for name in batch]})
            for raw in page["data"]:
                self._remember(cache, raw)
            for missed in page.get("not_found", []):  # the collection endpoint only knows front faces; search knows the spell side of a prepared card
                self._sleep(POLITE_DELAY_SECONDS)
                found = self._get_json(SEARCH_URL + "?" + urllib.parse.urlencode({"q": '!"%s"' % missed["name"]}))
                for raw in found.get("data", []):
                    self._remember(cache, raw)

    @staticmethod
    def _remember(cache: dict, raw: dict) -> None:
        cache[raw["name"].lower()] = raw
        for face_name in raw["name"].split(" // "):  # a label may name just one face
            cache.setdefault(face_name.lower(), raw)

    def _load_cache(self) -> dict:
        if self._cache_path and os.path.exists(self._cache_path):
            with open(self._cache_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self, cache: dict) -> None:
        if self._cache_path:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f)
