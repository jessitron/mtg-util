import time
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from ..domain.ports import Classifier, NoTelemetry, RecordedCall, Telemetry, Verdict
from ..domain.pricing import estimate_cost
from ..domain.scoring import LabeledCard, Scorecard


@dataclass(frozen=True)
class Attempt:
    """One classifier on one card. A failure is recorded and the run goes on."""

    verdict: Optional[Verdict] = None
    error: Optional[str] = None

    def cost(self, classifier: str) -> Optional[float]:
        return estimate_cost(classifier, self.verdict.usage) if self.verdict else None


@dataclass(frozen=True)
class Evaluation:
    cards: Sequence[LabeledCard]
    classifiers: Sequence[str]
    attempts: dict  # (card name, classifier name) -> Attempt

    def scorecard(self, classifier: str) -> Scorecard:
        return Scorecard.of(classifier, ((c, self.attempts[(c.card.name, classifier)].verdict) for c in self.cards))

    def cost(self, classifier: str) -> Optional[float]:
        """Estimated dollars this classifier spent over the run, or None when no call reported usage."""
        costs = [c for card in self.cards if (c := self.attempts[(card.card.name, classifier)].cost(classifier)) is not None]
        return sum(costs) if costs else None


def evaluate(
    cards: Sequence[LabeledCard],
    classifiers: Sequence[Classifier],
    on_progress: Callable[[str], None] = lambda _: None,
    telemetry: Telemetry = NoTelemetry(),
    run_id: str = "",
) -> Evaluation:
    attempts = {}
    with telemetry.run(run_id):
        for classifier in classifiers:
            for labeled in cards:
                on_progress(f"{classifier.name}: {labeled.card.name}")
                started = time.time_ns()
                try:
                    attempt = Attempt(verdict=classifier.classify(labeled.card))
                except Exception as e:  # one bad call must not lose the rest of a paid run
                    attempt = Attempt(error=f"{type(e).__name__}: {e}")
                attempts[(labeled.card.name, classifier.name)] = attempt
                if attempt.error or (attempt.verdict and attempt.verdict.call):  # a rubber stamp makes no call
                    telemetry.record_call(RecordedCall(run_id, classifier.name, labeled.card, labeled.score, started, time.time_ns(), attempt.verdict, attempt.error, attempt.cost(classifier.name)))
    return Evaluation(cards, [c.name for c in classifiers], attempts)
