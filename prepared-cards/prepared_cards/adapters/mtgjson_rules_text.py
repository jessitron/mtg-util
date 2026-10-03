"""Anti-corruption layer: the MTGJSON card database (see ../../../mtgjson/README.md) in, CardRules out."""
import os
import sqlite3

from ..domain.card import Card
from ..domain.card_rules import CardFace, CardRules

FACES = """
select c.faceName, c.name, c.manaCost, c.faceManaValue, c.manaValue, c.type, c.text, c.power, c.toughness
from cards c join cardIdentifiers i on i.uuid = c.uuid
where i.scryfallId = ?
order by c.side
"""


class MtgjsonRulesText:
    """Looks a card up by its Scryfall id. The database is read-only, and its path is absolute so a worktree finds the main checkout's copy."""

    def __init__(self, database_path: str):
        if not os.path.exists(database_path):
            raise FileNotFoundError(f"No MTGJSON database at {database_path}. Fetch it with mtgjson/run in the main checkout.")
        self._database_path = database_path

    def rules_for(self, card: Card) -> CardRules:
        with sqlite3.connect(f"file:{self._database_path}?mode=ro", uri=True) as db:
            rows = db.execute(FACES, (card.scryfall_id,)).fetchall()
        if not rows:
            raise LookupError(f"MTGJSON has no card with Scryfall id {card.scryfall_id} ({card.name})")
        return CardRules(tuple(_face(row) for row in rows))


def _face(row) -> CardFace:
    face_name, name, mana_cost, face_mana_value, mana_value, type_line, text, power, toughness = row
    return CardFace(
        name=face_name or name,  # a one-face card has no faceName
        mana_cost=mana_cost or "",
        mana_value=float(mana_value if face_mana_value is None else face_mana_value),
        type_line=type_line or "",
        text=text or "",
        power=power or "",
        toughness=toughness or "",
    )
