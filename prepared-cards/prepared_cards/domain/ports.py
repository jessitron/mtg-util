from typing import Protocol

from .card_pool import CardPool
from .selection import Selection


class CardCatalog(Protocol):
    """Where candidate cards come from."""

    def pool(self) -> CardPool: ...

    def refresh(self) -> CardPool:
        """Ignore anything remembered and look again at the source."""
        ...


class SelectionStore(Protocol):
    """Where the player's picks are kept between sessions."""

    def load(self) -> Selection: ...

    def save(self, selection: Selection) -> None: ...
