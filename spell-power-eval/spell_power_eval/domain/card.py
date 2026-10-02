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
    image_url: str = ""
    edhrec_rank: Optional[int] = None  # popularity among Commander decks; lower is more popular. Never shown to classifiers.
    note: str = ""  # context every classifier gets, such as "judge this spell alone"
    scryfall_cmc: Optional[float] = None  # Scryfall's own number; differs from mana_value on a prepared spell, where it is the creature's

    def _stat_total(self) -> Optional[int]:
        if self.power is not None and self.toughness is not None and self.power.isdigit() and self.toughness.isdigit() and self.mana_value > 0:
            return int(self.power) + int(self.toughness)
        return None

    def computed(self) -> list[tuple[str, str]]:
        """The numbers we work out ourselves, as (what, value) pairs, for showing to a human. `facts()` carries the same numbers to the classifiers."""
        values = [("Mana value we send", _whole(self.mana_value))]
        if self.scryfall_cmc is not None and self.scryfall_cmc != self.mana_value:
            values.append(("Scryfall's cmc (not sent; it belongs to the other face)", _whole(self.scryfall_cmc)))
        total = self._stat_total()
        if total is not None:
            values.append(("Power plus toughness", f"{total} ({total / self.mana_value:.1f} per mana)"))
        return values

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
            total = self._stat_total()
            if total is not None:
                lines.append(f"Power plus toughness: {total} ({total / self.mana_value:.1f} per mana)")
        if self.loyalty is not None:
            lines.append(f"Starting loyalty: {self.loyalty}")
        if self.note:
            lines.append(f"Note: {self.note}")
        return "\n".join(lines)
