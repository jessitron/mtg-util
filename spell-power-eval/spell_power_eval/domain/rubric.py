"""The question every classifier answers, in one place so every arm of the eval gets the same words."""
from .power import Power

QUESTION = (
    "Compared to its mana cost, is this Magic: The Gathering card weak, balanced, or powerful? "
    "Judge what the mana cost pays for in a typical game. Ignore combos, banned lists, and any one format."
)

# Situations, not adjectives: TypeSafe's docs say Jev matches best against concrete descriptions.
DESCRIPTIONS = {
    Power.WEAK: "Costs more than its effect is worth. Most players would not play it unless the format or a theme forced them to.",
    Power.BALANCED: "Fairly costed. What it does matches what that much mana buys in a typical game.",
    Power.POWERFUL: "Does more than its cost should buy. Players play it in every deck that can, or build around it.",
}

SCORE_SCALE = (
    "Also give a score from 0 to 2: 0 is weak, 1 is balanced, 2 is powerful. Use decimals for in-between cards "
    "(1.5 is strong for its cost but not a staple; 0.5 is below par but playable)."
)

CLAUDE_SYSTEM_PROMPT = (
    "You rate Magic: The Gathering cards for a game-balance study.\n\n"
    f"{QUESTION}\n\n"
    + "\n".join(f"- {power.label}: {text}" for power, text in DESCRIPTIONS.items())
    + f"\n\n{SCORE_SCALE}\n\nGive a one-sentence reason first, then the score."
)
