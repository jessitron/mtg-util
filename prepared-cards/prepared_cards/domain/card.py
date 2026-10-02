from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """A Magic card as this app sees it. The name is the full name ("Front // Back" for two-faced cards)."""

    name: str
    mana_value: float
    mana_cost: str
    type_line: str
    image_url: str
    page_url: str
