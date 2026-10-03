"""What a scorer's tokens cost. Prices ($ per million input/output tokens) were cached 2026-09-25; see ../../../reference/anthropic-api.md and jev.md.
An estimate, since the prices are remembered, not asked for."""
from typing import Optional

PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "jev-latest": (0.042, 0.0),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Dollars for one call, or None when we don't know the model's price. For Claude, output tokens include thinking."""
    if model not in PRICES:
        return None
    per_input, per_output = PRICES[model]
    return (input_tokens * per_input + output_tokens * per_output) / 1_000_000
