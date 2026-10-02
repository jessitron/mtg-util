from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Usage:
    """Tokens one call used, as the provider reported them. For Claude, output includes thinking."""

    input_tokens: int
    output_tokens: int


# $ per million (input, output) tokens, by arm name. Cached 2026-09-25 (see reference/anthropic-api.md and jev.md).
PRICES = {
    "always-balanced": (0.0, 0.0),
    "haiku": (1.0, 5.0),
    "sonnet": (2.0, 10.0),
    "opus": (4.0, 20.0),
    "jev-choice": (0.042, 0.0),
    "jev-score": (0.042, 0.0),
}


def estimate_cost(arm: str, usage: Optional[Usage]) -> Optional[float]:
    """Dollars for one call, or None when we lack the usage or the arm's price. An estimate: prices are cached, not live."""
    if usage is None or arm not in PRICES:
        return None
    per_input, per_output = PRICES[arm]
    return (usage.input_tokens * per_input + usage.output_tokens * per_output) / 1_000_000
