"""Gateway to Claude: a card goes in, a Verdict comes out. Uses the Anthropic SDK's structured outputs."""
import json

from pydantic import BaseModel

from ..domain.card import Card
from ..domain.power import Power
from ..domain.pricing import Usage
from ..domain.ports import ModelCall, Verdict
from ..domain.rubric import CLAUDE_SYSTEM_PROMPT

# Short names for the command line. Prices ($ per million input/output tokens) were cached 2026-09-25.
CLAUDE_MODELS = {
    "haiku": "claude-haiku-4-5",  # $1 / $5
    "sonnet": "claude-sonnet-5-5",  # $2 / $10
    "opus": "claude-opus-5-5",  # $4 / $20
}


class ClaudeAnswer(BaseModel):
    reason: str  # first, so the model thinks before it commits to a number
    score: float  # 0 weak, 1 balanced, 2 powerful


def claude_request(short_name: str, card: Card) -> dict:
    """Exactly what we send to `messages.parse` for a card. The results page shows this, so keep it the one place the request is built."""
    return dict(
        model=CLAUDE_MODELS[short_name],
        max_tokens=4096,  # room for adaptive thinking on the models that always think
        system=CLAUDE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": card.facts()}],
        output_format=ClaudeAnswer,
    )


def _dump(block) -> dict:
    return block.model_dump(mode="json") if hasattr(block, "model_dump") else {"text": str(block)}


class ClaudeClassifier:
    def __init__(self, short_name: str, client=None):
        self.name = short_name
        self._client = client

    def classify(self, card: Card) -> Verdict:
        if self._client is None:
            import anthropic  # deferred, so a dry run needs no credentials

            self._client = anthropic.Anthropic()
        request = claude_request(self.name, card)
        response = self._client.messages.parse(**request)
        answer = response.parsed_output
        if answer is None:
            raise RuntimeError(f"no parsed answer (stop_reason={response.stop_reason})")
        score = min(max(answer.score, 0.0), 2.0)  # the schema can't enforce the range
        usage = Usage(response.usage.input_tokens, response.usage.output_tokens)
        call = ModelCall(
            "anthropic",
            request["model"],
            getattr(response, "model", request["model"]),
            input=card.facts(),
            output=json.dumps([_dump(block) for block in getattr(response, "content", [])]),
            system=CLAUDE_SYSTEM_PROMPT,
            finish_reasons=(response.stop_reason,) if response.stop_reason else (),
        )
        return Verdict(Power.nearest(score), score, detail=answer.reason, usage=usage, call=call)
