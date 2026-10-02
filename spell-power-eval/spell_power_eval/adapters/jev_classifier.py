"""Gateway to TypeSafe's Jev. Request and response shapes come from https://docs.typesafe.ai/api.md (see reference/jev.md)."""
import json
import os
import urllib.error
import urllib.request
from typing import Callable, Literal

from ..domain.card import Card
from ..domain.power import Power
from ..domain.ports import Verdict
from ..domain.rubric import DESCRIPTIONS, QUESTION

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


def _question(kind: str) -> dict:
    if kind == "choice":
        return {
            "type": "choice",
            "instructions": QUESTION,
            "criteria": {power.label: text for power, text in DESCRIPTIONS.items()},
        }
    # Score levels are ordered, so level 0 is weak and level 2 is powerful.
    return {"type": "score", "instructions": QUESTION, "criteria": [DESCRIPTIONS[power] for power in Power]}


class JevClassifier:
    """One arm of the eval per question type: `jev-choice` picks a label, `jev-score` rates on the ordered rubric."""

    def __init__(self, kind: Literal["choice", "score"], post_json: Callable[[str, dict, str], dict] = _post_json):
        self.name = f"jev-{kind}"
        self._kind = kind
        self._post_json = post_json

    def classify(self, card: Card) -> Verdict:
        api_key = os.environ.get(KEY_VARIABLE)
        if not api_key:
            raise RuntimeError(f"{KEY_VARIABLE} is not set")
        body = {"model": "jev-latest", "state": card.facts(), "questions": {QUESTION_ID: _question(self._kind)}}
        answer = self._post_json(URL, body, api_key)["answers"][QUESTION_ID]
        probabilities = answer.get("probabilities", {})
        if self._kind == "choice":
            power = Power.from_label(answer["choice"])
            shown = {Power.from_label(k).label: v for k, v in probabilities.items()}
        else:
            power = Power.nearest(answer["score"])
            shown = {Power(int(k)).label: v for k, v in probabilities.items()}
        detail = ", ".join(f"{label} {p:.2f}" for label, p in shown.items())
        if self._kind == "score":
            detail = f"score {answer['score']:.2f}; " + detail
        return Verdict(power, confidence=answer.get("confidence"), detail=detail)
