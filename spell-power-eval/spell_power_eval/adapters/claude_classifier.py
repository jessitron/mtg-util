"""Gateway to Claude: a card goes in, a Verdict comes out. Uses the Anthropic SDK's structured outputs."""
from typing import Literal

from pydantic import BaseModel

from ..domain.card import Card
from ..domain.power import Power
from ..domain.ports import Verdict
from ..domain.rubric import CLAUDE_SYSTEM_PROMPT

# Short names for the command line. Prices ($ per million input/output tokens) were cached 2026-09-25.
CLAUDE_MODELS = {
    "haiku": "claude-haiku-4-5",  # $1 / $5
    "sonnet": "claude-sonnet-5-5",  # $2 / $10
    "opus": "claude-opus-5-5",  # $4 / $20
}


class ClaudeAnswer(BaseModel):
    reason: str  # first, so the model thinks before it commits to a label
    verdict: Literal["weak", "balanced", "powerful"]


class ClaudeClassifier:
    def __init__(self, short_name: str, client=None):
        self.name = short_name
        self._model = CLAUDE_MODELS[short_name]
        self._client = client

    def classify(self, card: Card) -> Verdict:
        if self._client is None:
            import anthropic  # deferred, so a dry run needs no credentials

            self._client = anthropic.Anthropic()
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=4096,  # room for adaptive thinking on the models that always think
            system=CLAUDE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": card.facts()}],
            output_format=ClaudeAnswer,
        )
        answer = response.parsed_output
        if answer is None:
            raise RuntimeError(f"no parsed answer (stop_reason={response.stop_reason})")
        return Verdict(Power.from_label(answer.verdict), detail=answer.reason)
