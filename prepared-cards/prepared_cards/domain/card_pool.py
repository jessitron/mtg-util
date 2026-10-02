from dataclasses import dataclass
from typing import Iterable

from .card import Card
from .power_score import PowerScore, ScoredCard


@dataclass(frozen=True)
class CardPool:
    """The cards we are choosing from."""

    cards: tuple[Card, ...]

    @classmethod
    def of(cls, cards: Iterable[Card]) -> "CardPool":
        return cls(tuple(sorted(cards, key=lambda c: c.name)))

    def ranked(self, power: PowerScore) -> tuple[ScoredCard, ...]:
        """Most powerful first; equal scores stay in name order."""
        scored = [ScoredCard(card, power.score(card)) for card in self.cards]
        return tuple(sorted(scored, key=lambda s: -s.score))  # sorted is stable

    def __len__(self) -> int:
        return len(self.cards)
