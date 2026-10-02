import json
import os

from ..domain.card import Card
from ..domain.power_score import PowerScore


class CachedPowerScore:
    """Remembers another scorer's answers in a JSON file (card name to score), so each card is scored once.

    The file is written after every new score, so a slow scorer that stops partway keeps what it finished."""

    def __init__(self, source: PowerScore, path: str):
        self._source = source
        self._path = path
        self._scores = self._read()

    def score(self, card: Card) -> float:
        if card.name not in self._scores:
            self._scores[card.name] = self._source.score(card)
            self._write()
        return self._scores[card.name]

    def _read(self) -> dict[str, float]:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            return json.load(f)

    def _write(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._scores, f, indent=1)
