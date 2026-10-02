from .card import Card
from .power import Power
from .pricing import Usage
from .ports import Verdict


class AlwaysBalanced:
    """The floor. Any classifier worth paying for beats a rubber stamp."""

    name = "always-balanced"

    def classify(self, card: Card) -> Verdict:
        return Verdict(Power.BALANCED, 1.0, detail="no reading of the card", usage=Usage(0, 0))
