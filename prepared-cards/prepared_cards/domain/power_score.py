from dataclasses import dataclass
from typing import Protocol

from .card import Card


class PowerScore(Protocol):
    """Port: how powerful a card is for its cost, from 0 (weak) to 2 (powerful), decimals allowed. The only way we order cards."""

    def score(self, card: Card) -> float: ...


@dataclass(frozen=True)
class ScoredCard:
    card: Card
    score: float
