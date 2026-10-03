import random

from ..domain.card import Card
from ..domain.power_score import Scoring


class RandomPowerScore:
    """A stand-in for a real scorer: a random score from 0 to 2, free. Lets the ranking work end to end offline."""

    name = "random"

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def scoring(self, card: Card) -> Scoring:
        return Scoring(round(self._rng.uniform(0, 2), 2), 0.0)
