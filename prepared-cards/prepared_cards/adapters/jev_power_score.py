"""Gateway to TypeSafe's Jev: a card's spell goes in, its `score` answer (0 to 2) comes out.
Request and response shapes come from https://docs.typesafe.ai/api.md (see ../../../reference/jev.md)."""
import json
import os
import urllib.error
import urllib.request
from typing import Callable

from ..domain.card import Card
from ..domain.ports import RulesText
from .spell_rubric import LEVELS, QUESTION, spell_facts

URL = "https://api.typesafe.ai/v1/systemone"
KEY_VARIABLE = "TYPESAFE_API_KEY"
QUESTION_ID = "power_for_cost"


def _post_json(url: str, body: dict, api_key: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Jev answered HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e


class JevPowerScore:
    """Asks Jev to rate a card's spell on an ordered three-level rubric (level 0 weak, level 2 powerful). Fetches the rules through the RulesText port."""

    def __init__(self, rules_text: RulesText, model: str = "jev-latest", post_json: Callable[[str, dict, str], dict] = _post_json):
        self.model = model
        self._rules_text = rules_text
        self._post_json = post_json

    def score(self, card: Card) -> float:
        api_key = os.environ.get(KEY_VARIABLE)
        if not api_key:
            raise RuntimeError(f"{KEY_VARIABLE} is not set")
        rules = self._rules_text.rules_for(card)
        body = {
            "model": self.model,
            "state": spell_facts(rules.spell, two_faced=len(rules.faces) > 1),
            "questions": {QUESTION_ID: {"type": "score", "instructions": QUESTION, "criteria": [text for _, text in LEVELS]}},
        }
        answer = self._post_json(URL, body, api_key)["answers"][QUESTION_ID]
        return round(min(max(answer["score"], 0.0), 2.0), 2)
