"""What every LLM scorer is asked, and how a spell is described to it. Shared so every scorer gets the same words.
The question and rubric are the ones spell-power-eval compared models on (spell_power_eval/domain/rubric.py);
they are copied here so this app stands alone."""
from ..domain.card_rules import CardFace

QUESTION = (
    "Compared to its mana cost, is this Magic: The Gathering spell weak, balanced, or powerful? "
    "Judge what the mana cost pays for in a typical game. Ignore combos, banned lists, and any one format."
)

# Situations, not adjectives: TypeSafe's docs say Jev matches best against concrete descriptions. Ordered weak to powerful.
LEVELS = (
    ("weak", "Costs more than its effect is worth. Most players would not play it unless the format or a theme forced them to."),
    ("balanced", "Fairly costed. What it does matches what that much mana buys in a typical game."),
    ("powerful", "Does more than its cost should buy. Players play it in every deck that can, or build around it."),
)

SPELL_NOTE = (
    "This is the spell half of a two-faced card whose other half is a creature. Judge the spell alone, at its own "
    "mana cost, as if it were a stand-alone card. Ignore the creature."
)


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
