from typing import Protocol

from .card import Card
from .card_pool import CardPool
from .card_rules import CardRules
from .selection import Selection


class CardCatalog(Protocol):
    """Where candidate cards come from."""

    def pool(self) -> CardPool: ...

    def refresh(self) -> CardPool:
        """Ignore anything remembered and look again at the source."""
        ...


class RulesText(Protocol):
    """Where a card's rules text comes from."""

    def rules_for(self, card: Card) -> CardRules:
        """Raises LookupError when the source has no such card."""
        ...


class SelectionStore(Protocol):
    """Where the player's picks are kept between sessions."""

    def load(self) -> Selection: ...

    def save(self, selection: Selection) -> None: ...

    def render(self, selection: Selection) -> str:
        """The picks as text to paste into the destination (Archidekt's import box)."""
        ...
