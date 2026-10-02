from dataclasses import dataclass
from typing import Iterable

from .card import Card


@dataclass(frozen=True)
class ManaValueGroup:
    mana_value: float
    cards: tuple[Card, ...]


@dataclass(frozen=True)
class CardPool:
    """The cards we are choosing from."""

    cards: tuple[Card, ...]

    @classmethod
    def of(cls, cards: Iterable[Card]) -> "CardPool":
        return cls(tuple(sorted(cards, key=lambda c: (c.mana_value, c.name))))

    def by_mana_value(self) -> list[ManaValueGroup]:
        groups: dict[float, list[Card]] = {}
        for card in self.cards:  # already sorted, so groups come out in ascending order
            groups.setdefault(card.mana_value, []).append(card)
        return [ManaValueGroup(mv, tuple(cs)) for mv, cs in groups.items()]

    def __len__(self) -> int:
        return len(self.cards)
