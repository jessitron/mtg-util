from dataclasses import dataclass
from typing import Optional


def _whole(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


@dataclass(frozen=True)
class Card:
    """A Magic card as this eval sees it. The name is the full name ("Front // Back" for two-faced cards)."""

    name: str
    mana_cost: str
    mana_value: float
    type_line: str
    oracle_text: str
    power: Optional[str] = None
    toughness: Optional[str] = None
    loyalty: Optional[str] = None
    edhrec_rank: Optional[int] = None  # popularity among Commander decks; lower is more popular. Never shown to classifiers.

    def facts(self) -> str:
        """What every classifier is told about the card. Arithmetic is done here, not left to the model."""
        lines = [
            f"Name: {self.name}",
            f"Mana cost: {self.mana_cost or 'none'} (mana value {_whole(self.mana_value)})",
            f"Type: {self.type_line}",
        ]
        if self.oracle_text:
            lines.append(f"Rules text: {self.oracle_text}")
        if self.power is not None and self.toughness is not None:
            lines.append(f"Power/toughness: {self.power}/{self.toughness}")
            if self.power.isdigit() and self.toughness.isdigit() and self.mana_value > 0:
                total = int(self.power) + int(self.toughness)
                lines.append(f"Power plus toughness: {total} ({total / self.mana_value:.1f} per mana)")
        if self.loyalty is not None:
            lines.append(f"Starting loyalty: {self.loyalty}")
        return "\n".join(lines)
