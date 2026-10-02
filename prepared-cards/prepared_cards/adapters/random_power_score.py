import random

from ..domain.card import Card


class RandomPowerScore:
    """A stand-in for a real scorer: a random score from 0 to 2. Lets the ranking work end to end before an LLM is wired in."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def score(self, card: Card) -> float:
        return round(self._rng.uniform(0, 2), 2)
