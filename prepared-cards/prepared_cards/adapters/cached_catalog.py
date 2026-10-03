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
            remembered = self._read()
            if remembered is not None:
                return remembered
        return self.refresh()

    def refresh(self) -> CardPool:
        pool = self._source.refresh()
        self._write(pool)
        return pool

    def _read(self) -> CardPool | None:
        """The remembered pool, or None when the file predates a field Card now has (so we look again)."""
        with open(self._path) as f:
            remembered = json.load(f)
        fields = {f.name for f in dataclasses.fields(Card)}
        if any(set(c) != fields for c in remembered):
            return None
        return CardPool.of(Card(**c) for c in remembered)

    def _write(self, pool: CardPool) -> None:
        with open(self._path, "w") as f:
            json.dump([dataclasses.asdict(c) for c in pool.cards], f, indent=1)
