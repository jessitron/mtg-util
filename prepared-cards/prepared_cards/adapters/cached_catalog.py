import dataclasses
import json
import os

from ..domain.card import Card
from ..domain.card_pool import CardPool
from ..domain.ports import CardCatalog


class CachedCatalog:
    """Remembers another catalog's pool in a JSON file, so we only bother Scryfall once."""

    def __init__(self, source: CardCatalog, path: str):
        self._source = source
        self._path = path

    def pool(self) -> CardPool:
        if os.path.exists(self._path):
            return self._read()
        return self.refresh()

    def refresh(self) -> CardPool:
        pool = self._source.refresh()
        self._write(pool)
        return pool

    def _read(self) -> CardPool:
        with open(self._path) as f:
            return CardPool.of(Card(**c) for c in json.load(f))

    def _write(self, pool: CardPool) -> None:
        with open(self._path, "w") as f:
            json.dump([dataclasses.asdict(c) for c in pool.cards], f, indent=1)
