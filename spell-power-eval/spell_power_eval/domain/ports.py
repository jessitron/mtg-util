from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager, Optional, Protocol, Sequence

from .card import Card
from .pricing import Usage
from .power import Power


@dataclass(frozen=True)
class ModelCall:
    """What went over the wire for one answer: the raw material for telemetry. Text is exactly what was sent and received."""

    provider: str  # "anthropic", "typesafe"
    request_model: str
    response_model: str
    input: str  # the user message for Claude; the whole request JSON for Jev
    output: str  # the response content blocks as JSON for Claude; the whole response JSON for Jev
    system: Optional[str] = None
    finish_reasons: tuple = ()


@dataclass(frozen=True)
class Verdict:
    """One classifier's answer for one card."""

    power: Power
    score: float  # 0 (weak) to 2 (powerful); decimals allowed. Every classifier gives one.
    confidence: Optional[float] = None  # the classifier's own claim, if it makes one
    detail: str = ""  # a reason, or the probabilities behind the label
    usage: Optional[Usage] = None  # tokens the call used; the basis for a cost estimate
    call: Optional[ModelCall] = None  # the exchange itself; None for a classifier that calls no API


class Classifier(Protocol):
    """Port: anything that can rate a card against its cost."""

    name: str

    def classify(self, card: Card) -> Verdict: ...


class CardCatalog(Protocol):
    """Port: where card facts come from. Raises LookupError naming any card it can't find."""

    def find(self, names: Sequence[str]) -> list[Card]: ...


class RunStore(Protocol):
    """Port: where finished runs are kept. A run is the results JSON that `report.results_json` builds."""

    def names(self) -> list[str]:
        """Every stored run's name, newest first."""
        ...

    def read(self, name: str) -> Optional[dict]:
        """One run, or None when no run has that name."""
        ...


@dataclass(frozen=True)
class RecordedCall:
    """One classifier on one card, with the human's score beside it. What a Telemetry records."""

    run_id: str
    classifier: str
    card: Card
    human_score: float
    started_ns: int
    ended_ns: int
    verdict: Optional[Verdict] = None
    error: Optional[str] = None
    cost_usd: Optional[float] = None


class Telemetry(Protocol):
    """Port: where we report each API call. `run` wraps a whole evaluation; `record_call` reports one call after it finishes."""

    def run(self, run_id: str) -> ContextManager: ...

    def record_call(self, call: RecordedCall) -> None: ...

    def close(self) -> None:
        """Send whatever is still buffered."""
        ...


class NoTelemetry:
    """Null object: telemetry is off."""

    @contextmanager
    def run(self, run_id: str):
        yield

    def record_call(self, call: RecordedCall) -> None:
        pass

    def close(self) -> None:
        pass
