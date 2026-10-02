import json
import unittest

from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from spell_power_eval.adapters.honeycomb_telemetry import HoneycombTelemetry
from spell_power_eval.domain.baseline import AlwaysBalanced
from spell_power_eval.domain.card import Card
from spell_power_eval.domain.power import Power
from spell_power_eval.domain.pricing import Usage
from spell_power_eval.domain.ports import ModelCall, Verdict
from spell_power_eval.domain.scoring import LabeledCard
from spell_power_eval.orchestration.evaluation import evaluate

CARD = Card(name="Serra Angel", mana_cost="{3}{W}{W}", mana_value=5.0, type_line="Creature — Angel", oracle_text="Flying, vigilance")


class Claudish:
    name = "haiku"

    def classify(self, card):
        call = ModelCall("anthropic", "claude-haiku-4-5", "claude-haiku-4-5-20251001", input=card.facts(), output='[{"type": "text", "text": "{}"}]', system="Be fair.", finish_reasons=("end_turn",))
        return Verdict(Power.POWERFUL, 1.6, detail="Flies.", usage=Usage(200, 50), call=call)


class Broken:
    name = "jev-choice"

    def classify(self, card):
        raise RuntimeError("boom")


class HoneycombTelemetryTest(unittest.TestCase):
    def run_eval(self, classifiers, human=1.4):
        exporter = InMemorySpanExporter()
        telemetry = HoneycombTelemetry(exporter, processor_class=SimpleSpanProcessor)
        evaluate([LabeledCard(CARD, human)], classifiers, telemetry=telemetry, run_id="20261002T000000Z")
        telemetry.close()
        return {span.name: span for span in exporter.get_finished_spans()}

    def test_a_call_is_a_chat_span_under_the_run(self):
        spans = self.run_eval([Claudish()])
        chat, run = spans["chat claude-haiku-4-5"], spans["invoke_agent spell-power-eval"]
        self.assertEqual(chat.parent.span_id, run.context.span_id)
        attributes = chat.attributes
        self.assertEqual(attributes["gen_ai.operation.name"], "chat")
        self.assertEqual(attributes["gen_ai.conversation.id"], "20261002T000000Z")
        self.assertEqual(attributes["gen_ai.agent.name"], "spell-power-eval")
        self.assertEqual((attributes["gen_ai.usage.input_tokens"], attributes["gen_ai.usage.output_tokens"]), (200, 50))
        self.assertEqual(attributes["gen_ai.response.model"], "claude-haiku-4-5-20251001")
        self.assertEqual(list(attributes["gen_ai.response.finish_reasons"]), ["end_turn"])

    def test_messages_ride_on_an_event(self):
        event = {e.name: e for e in self.run_eval([Claudish()])["chat claude-haiku-4-5"].events}["gen_ai.client.inference.operation.details"]
        sent = json.loads(event.attributes["gen_ai.input.messages"])
        self.assertEqual(sent[0]["role"], "user")
        self.assertIn("Name: Serra Angel", sent[0]["parts"][0]["content"])
        self.assertEqual(json.loads(event.attributes["gen_ai.output.messages"])[0]["role"], "assistant")
        self.assertIn("Be fair.", event.attributes["gen_ai.system_instructions"])

    def test_the_comparison_with_the_human_is_recorded(self):
        span = self.run_eval([Claudish()])["chat claude-haiku-4-5"]
        attributes = span.attributes
        self.assertEqual((attributes["spell_eval.human_score"], attributes["spell_eval.human_label"]), (1.4, "balanced"))
        self.assertAlmostEqual(attributes["spell_eval.score_error"], 0.2)
        self.assertAlmostEqual(attributes["spell_eval.score_diff"], 0.2)
        self.assertEqual((attributes["spell_eval.steps_off"], attributes["spell_eval.label_match"]), (1, False))
        evaluation = {e.name: e for e in span.events}["gen_ai.evaluation.result"]
        self.assertEqual(evaluation.attributes["gen_ai.evaluation.score.label"], "mismatch")
        self.assertIn("Jess scored 1.40", evaluation.attributes["gen_ai.evaluation.explanation"])

    def test_a_failed_call_is_an_error_span(self):
        span = self.run_eval([Broken()])["chat jev-choice"]
        self.assertFalse(span.status.is_ok)
        self.assertEqual(span.attributes["error.type"], "RuntimeError")
        self.assertNotIn("spell_eval.score", span.attributes)

    def test_a_classifier_that_calls_no_api_sends_no_span(self):
        spans = self.run_eval([AlwaysBalanced()])
        self.assertEqual(list(spans), ["invoke_agent spell-power-eval"])


if __name__ == "__main__":
    unittest.main()
