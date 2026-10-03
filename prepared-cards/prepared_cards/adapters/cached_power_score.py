import json
import os
import time
from typing import Callable, Iterable

from ..domain.card import Card
from ..domain.power_score import RankingEffort, Scorer


class CachedPowerScore:
    """Remembers another scorer's answers in a JSON file, so each card is scored once. It is the PowerScore the app uses
    and the EffortLedger: beside each score it keeps the seconds the scorer took and the dollars it cost.

    The file is written after every new score, so a slow scorer that stops partway keeps what it finished.
    File shape: card name to {"score", "seconds", "cost_usd"}. An older file with bare scores still loads, with no time or cost."""

    def __init__(self, source: Scorer, path: str, clock: Callable[[], float] = time.perf_counter):
        self.name = source.name
        self._source = source
        self._path = path
        self._clock = clock
        self._entries = self._read()

    def score(self, card: Card) -> float:
        if card.name not in self._entries:
            started = self._clock()
            scoring = self._source.scoring(card)
            self._entries[card.name] = {"score": scoring.score, "seconds": self._clock() - started, "cost_usd": scoring.cost_usd}
            self._write()
        return self._entries[card.name]["score"]

    def effort(self, cards: Iterable[Card]) -> RankingEffort:
        """What these cards' scores took. The cost is None if any card's cost is unknown. Cards not yet scored count for nothing."""
        entries = [self._entries[c.name] for c in cards if c.name in self._entries]
        costs = [e["cost_usd"] for e in entries]
        return RankingEffort(self.name, sum(e["seconds"] for e in entries), None if None in costs else sum(costs))

    def _read(self) -> dict[str, dict]:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            raw = json.load(f)
        return {name: v if isinstance(v, dict) else {"score": v, "seconds": 0.0, "cost_usd": None} for name, v in raw.items()}

    def _write(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._entries, f, indent=1)
