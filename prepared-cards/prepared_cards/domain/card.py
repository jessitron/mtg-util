import urllib.parse
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

    @property
    def gatherer_url(self) -> str:
        """Gatherer's name search, on the front face. Scryfall has no Gatherer id for unreleased cards."""
        front = self.name.split(" // ")[0]
        return "https://gatherer.wizards.com/advanced-search?" + urllib.parse.urlencode({"name": front})
