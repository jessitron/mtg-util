"""Gateway to Claude: a card's spell goes in, a score from 0 to 2 comes out. The question and rubric are the ones
spell-power-eval compared models on (spell_power_eval/domain/rubric.py); they are copied here so this app stands alone."""
from pydantic import BaseModel

from ..domain.card import Card
from ..domain.card_rules import CardFace
from ..domain.ports import RulesText

SYSTEM_PROMPT = (
    "You rate Magic: The Gathering spells for a game-balance study.\n\n"
    "Compared to its mana cost, is this Magic: The Gathering spell weak, balanced, or powerful? "
    "Judge what the mana cost pays for in a typical game. Ignore combos, banned lists, and any one format.\n\n"
    "- weak: Costs more than its effect is worth. Most players would not play it unless the format or a theme forced them to.\n"
    "- balanced: Fairly costed. What it does matches what that much mana buys in a typical game.\n"
    "- powerful: Does more than its cost should buy. Players play it in every deck that can, or build around it.\n\n"
    "Also give a score from 0 to 2: 0 is weak, 1 is balanced, 2 is powerful. Use decimals for in-between cards "
    "(1.5 is strong for its cost but not a staple; 0.5 is below par but playable).\n\n"
    "Give a one-sentence reason first, then the score."
)

SPELL_NOTE = (
    "This is the spell half of a two-faced card whose other half is a creature. Judge the spell alone, at its own "
    "mana cost, as if it were a stand-alone card. Ignore the creature."
)


class Answer(BaseModel):
    reason: str  # first, so the model thinks before it commits to a number
    score: float  # 0 weak, 1 balanced, 2 powerful


def _whole(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def spell_facts(spell: CardFace, two_faced: bool) -> str:
    """What the model is told about the spell: its own face only, at its own cost."""
    lines = [
        f"Name: {spell.name}",
        f"Mana cost: {spell.mana_cost or 'none'} (mana value {_whole(spell.mana_value)})",
        f"Type: {spell.type_line}",
    ]
    if spell.text:
        lines.append(f"Rules text: {spell.text}")
    if two_faced:
        lines.append(f"Note: {SPELL_NOTE}")
    return "\n".join(lines)


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
