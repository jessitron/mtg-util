from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .card import Card
from .power import Power
from .ports import Verdict


@dataclass(frozen=True)
class LabeledCard:
    """A card with the human's verdict: the ground truth."""

    card: Card
    expected: Power


@dataclass(frozen=True)
class Scorecard:
    """How one classifier did against the human labels. Failed calls count separately, not as wrong answers."""

    classifier: str
    answered: int
    failed: int
    exact: int
    ordinal_error_total: int
    score_error_total: float
    confusion: dict  # (expected label, got label) -> count

    @classmethod
    def of(cls, classifier: str, outcomes: Iterable[tuple[LabeledCard, "Verdict | None"]]) -> "Scorecard":
        answered = failed = exact = error = 0
        score_error = 0.0
        confusion: Counter = Counter()
        for labeled, verdict in outcomes:
            if verdict is None:
                failed += 1
                continue
            answered += 1
            exact += verdict.power == labeled.expected
            error += abs(verdict.power.value - labeled.expected.value)
            score_error += abs(verdict.score - labeled.expected.value)
            confusion[(labeled.expected.label, verdict.power.label)] += 1
        return cls(classifier, answered, failed, exact, error, score_error, dict(confusion))

    @property
    def accuracy(self) -> float:
        return self.exact / self.answered if self.answered else 0.0

    @property
    def mean_ordinal_error(self) -> float:
        """Average distance in steps: calling a weak card powerful costs 2, calling it balanced costs 1."""
        return self.ordinal_error_total / self.answered if self.answered else 0.0

    @property
    def mean_score_error(self) -> float:
        """Average distance between the classifier's 0-2 score and your label (0, 1, or 2)."""
        return self.score_error_total / self.answered if self.answered else 0.0
