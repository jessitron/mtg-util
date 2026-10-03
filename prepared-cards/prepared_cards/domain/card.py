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
    scryfall_id: str  # one id per printing, shared by every face; how other sources find this card

    @property
    def gatherer_url(self) -> str:
        """Gatherer's quick search (the top search box), on the front face. Scryfall has no Gatherer id for unreleased cards."""
        front = self.name.split(" // ")[0]
        return "https://gatherer.wizards.com/search?" + urllib.parse.urlencode({"searchTerm": front}, quote_via=urllib.parse.quote)
