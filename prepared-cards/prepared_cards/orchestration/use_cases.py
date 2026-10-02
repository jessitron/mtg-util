from typing import Iterable

from ..domain.card_pool import CardPool
from ..domain.power_score import PowerScore, ScoredCard
from ..domain.ports import CardCatalog, SelectionStore
from ..domain.selection import Selection


class CardPicker:
    """Show the candidate cards, most powerful first, and remember which ones the player picks."""

    def __init__(self, catalog: CardCatalog, power: PowerScore, store: SelectionStore):
        self._catalog = catalog
        self._power = power
        self._store = store

    def candidates(self, refresh: bool = False) -> CardPool:
        return self._catalog.refresh() if refresh else self._catalog.pool()

    def ranked_candidates(self, refresh: bool = False) -> tuple[ScoredCard, ...]:
        return self.candidates(refresh).ranked(self._power)

    def current_selection(self) -> Selection:
        return self._store.load()

    def save_selection(self, names: Iterable[str]) -> Selection:
        selection = Selection.of(names)
        self._store.save(selection)
        return selection

    def save_and_render(self, names: Iterable[str]) -> str:
        return self._store.render(self.save_selection(names))
