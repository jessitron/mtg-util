"""Gateway to Claude: a card's spell goes in, a score from 0 to 2 comes out."""
from pydantic import BaseModel

from ..domain.card import Card
from ..domain.ports import RulesText
from .spell_rubric import LEVELS, QUESTION, spell_facts

SYSTEM_PROMPT = (
    "You rate Magic: The Gathering spells for a game-balance study.\n\n"
    f"{QUESTION}\n\n"
    + "\n".join(f"- {label}: {text}" for label, text in LEVELS)
    + "\n\nAlso give a score from 0 to 2: 0 is weak, 1 is balanced, 2 is powerful. Use decimals for in-between cards "
    "(1.5 is strong for its cost but not a staple; 0.5 is below par but playable).\n\n"
    "Give a one-sentence reason first, then the score."
)


class Answer(BaseModel):
    reason: str  # first, so the model thinks before it commits to a number
    score: float  # 0 weak, 1 balanced, 2 powerful


class LlmPowerScore:
    """Asks Claude how powerful a card's spell is for its own cost. Fetches the rules through the RulesText port."""

    def __init__(self, rules_text: RulesText, model: str, client=None):
        self.model = model
        self._rules_text = rules_text
        self._client = client

    def score(self, card: Card) -> float:
        rules = self._rules_text.rules_for(card)
        if self._client is None:
            import anthropic  # deferred, so tests and a missing key fail only when a score is asked for

            self._client = anthropic.Anthropic()
        response = self._client.messages.parse(
            model=self.model,
            max_tokens=4096,  # room for adaptive thinking on the models that always think
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": spell_facts(rules.spell, two_faced=len(rules.faces) > 1)}],
            output_format=Answer,
        )
        if response.parsed_output is None:
            raise RuntimeError(f"no score for {card.name} (stop_reason={response.stop_reason})")
        return round(min(max(response.parsed_output.score, 0.0), 2.0), 2)  # the schema can't enforce the range
