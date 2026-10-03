from dataclasses import dataclass


@dataclass(frozen=True)
class CardFace:
    """One face of a card, with its own cost and rules text. A prepared card's back face is its spell."""

    name: str
    mana_cost: str
    mana_value: float
    type_line: str
    text: str
    power: str = ""
    toughness: str = ""


@dataclass(frozen=True)
class CardRules:
    """What a card does, as printed: every face, front first. The raw material for judging how powerful it is."""

    faces: tuple[CardFace, ...]

    @property
    def spell(self) -> CardFace:
        """The last face. For a prepared card, that is the spell on its back; for a one-face card, the card itself."""
        return self.faces[-1]
