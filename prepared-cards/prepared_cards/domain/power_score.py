from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

from .card import Card


class PowerScore(Protocol):
    """Port: how powerful a card is for its cost, from 0 (weak) to 2 (powerful), decimals allowed. The only way we order cards."""

    def score(self, card: Card) -> float: ...


@dataclass(frozen=True)
class ScoredCard:
    card: Card
    score: float


@dataclass(frozen=True)
class Scoring:
    """One scorer answer: the score, and what it cost in dollars (None when the price is unknown)."""

    score: float
    cost_usd: Optional[float]


class Scorer(Protocol):
    """Port: something that works out a card's power score the slow way (an LLM, say) and says what that cost."""

    name: str

    def scoring(self, card: Card) -> Scoring: ...


@dataclass(frozen=True)
class RankingEffort:
    """What it took to score some cards: who did it, how long they spent, and the dollars (None when any price is unknown)."""

    scorer: str
    seconds: float
    cost_usd: Optional[float]


class EffortLedger(Protocol):
    """Port: remembers what each score took, across restarts, so a ranking can say what it cost."""

    def effort(self, cards: Iterable[Card]) -> RankingEffort: ...
