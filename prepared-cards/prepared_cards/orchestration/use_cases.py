from typing import Iterable

from ..domain.card_pool import CardPool
from ..domain.ports import CardCatalog, SelectionStore
from ..domain.selection import Selection


class CardPicker:
    """Show the candidate cards, remember which ones the player picks."""

    def __init__(self, catalog: CardCatalog, store: SelectionStore):
        self._catalog = catalog
        self._store = store

    def candidates(self, refresh: bool = False) -> CardPool:
        return self._catalog.refresh() if refresh else self._catalog.pool()

    def current_selection(self) -> Selection:
        return self._store.load()

    def save_selection(self, names: Iterable[str]) -> Selection:
        selection = Selection.of(names)
        self._store.save(selection)
        return selection
