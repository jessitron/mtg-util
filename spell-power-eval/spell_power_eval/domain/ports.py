from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from .card import Card
from .power import Power


@dataclass(frozen=True)
class Verdict:
    """One classifier's answer for one card."""

    power: Power
    score: float  # 0 (weak) to 2 (powerful); decimals allowed. Every classifier gives one.
    confidence: Optional[float] = None  # the classifier's own claim, if it makes one
    detail: str = ""  # a reason, or the probabilities behind the label


class Classifier(Protocol):
    """Port: anything that can rate a card against its cost."""

    name: str

    def classify(self, card: Card) -> Verdict: ...


class CardCatalog(Protocol):
    """Port: where card facts come from. Raises LookupError naming any card it can't find."""

    def find(self, names: Sequence[str]) -> list[Card]: ...
