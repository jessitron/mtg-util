"""Gateway to TypeSafe's Jev. Request and response shapes come from https://docs.typesafe.ai/api.md (see reference/jev.md)."""
import json
import os
import urllib.error
import urllib.request
from typing import Callable, Literal

from ..domain.card import Card
from ..domain.power import Power
from ..domain.pricing import Usage
from ..domain.ports import ModelCall, Verdict
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


def jev_request(kind: Literal["choice", "score"], card: Card) -> dict:
    """Exactly the JSON body we POST to Jev for a card. The results page shows this, so keep it the one place the request is built."""
    return {"model": "jev-latest", "state": card.facts(), "questions": {QUESTION_ID: _question(kind)}}


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
        request = jev_request(self._kind, card)
        response = self._post_json(URL, request, api_key)
        answer = response["answers"][QUESTION_ID]
        reported = response.get("usage")
        usage = Usage(reported["input_tokens"], reported["output_tokens"]) if reported else None
        probabilities = answer.get("probabilities", {})
        if self._kind == "choice":
            power = Power.from_label(answer["choice"])
            shown = {Power.from_label(k).label: v for k, v in probabilities.items()}
            score = sum(Power.from_label(label).value * p for label, p in shown.items())  # expected level
        else:
            score = answer["score"]
            power = Power.nearest(score)
            shown = {Power(int(k)).label: v for k, v in probabilities.items()}
        detail = ", ".join(f"{label} {p:.2f}" for label, p in shown.items())
        call = ModelCall("typesafe", request["model"], response.get("model", request["model"]), input=json.dumps(request), output=json.dumps(response))
        return Verdict(power, score, confidence=answer.get("confidence"), detail=detail, usage=usage, call=call)
