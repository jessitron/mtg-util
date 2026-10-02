import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from spell_power_eval.adapters.claude_classifier import ClaudeAnswer, ClaudeClassifier
from spell_power_eval.adapters.jev_classifier import KEY_VARIABLE, QUESTION_ID, JevClassifier
from spell_power_eval.adapters.labels_file import LabelsFile
from spell_power_eval.adapters.scryfall_catalog import ScryfallCatalog, card_from_scryfall
from spell_power_eval.domain.baseline import AlwaysBalanced
from spell_power_eval.domain.card import Card
from spell_power_eval.domain.power import Power
from spell_power_eval.domain.ports import Verdict
from spell_power_eval.domain.scoring import LabeledCard, Scorecard
from spell_power_eval.orchestration.evaluation import evaluate
from spell_power_eval.orchestration.report import results_json, text_report


def card(name="Serra Angel", mv=5.0, **extra):
    fields = dict(name=name, mana_cost="{3}{W}{W}", mana_value=mv, type_line="Creature — Angel", oracle_text="Flying, vigilance")
    return Card(**{**fields, **extra})


def raw(name, **extra):
    return {"name": name, "cmc": 2.0, "type_line": "Creature", **extra}


class PowerTest(unittest.TestCase):
    def test_parses_labels_in_any_case(self):
        self.assertEqual(Power.from_label(" Weak "), Power.WEAK)

    def test_rejects_other_words(self):
        with self.assertRaises(ValueError):
            Power.from_label("okay")

    def test_nearest_rounds_and_clamps(self):
        self.assertEqual([Power.nearest(x) for x in (-0.3, 0.4, 1.43, 1.5, 9)], [Power.WEAK, Power.WEAK, Power.BALANCED, Power.POWERFUL, Power.POWERFUL])


class CardFactsTest(unittest.TestCase):
    def test_does_the_arithmetic_for_the_model(self):
        facts = card(power="4", toughness="4").facts()
        self.assertIn("Power plus toughness: 8 (1.6 per mana)", facts)
        self.assertIn("Mana cost: {3}{W}{W} (mana value 5)", facts)

    def test_skips_arithmetic_for_star_stats_and_zero_cost(self):
        self.assertNotIn("per mana", card(power="*", toughness="4").facts())
        self.assertNotIn("per mana", card(mv=0.0, power="1", toughness="1").facts())

    def test_never_mentions_popularity(self):
        self.assertNotIn("1234", card(edhrec_rank=1234).facts())


class ScorecardTest(unittest.TestCase):
    def test_counts_exact_and_steps_and_failures(self):
        weak = LabeledCard(card("A"), Power.WEAK)
        strong = LabeledCard(card("B"), Power.POWERFUL)
        score = Scorecard.of("x", [(weak, Verdict(Power.POWERFUL)), (strong, Verdict(Power.POWERFUL)), (weak, None)])
        self.assertEqual((score.answered, score.failed, score.exact), (2, 1, 1))
        self.assertEqual(score.mean_ordinal_error, 1.0)
        self.assertEqual(score.confusion, {("weak", "powerful"): 1, ("powerful", "powerful"): 1})


class LabelsFileTest(unittest.TestCase):
    def read(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text)
        self.addCleanup(os.remove, f.name)
        return LabelsFile(f.name).read()

    def test_reads_labels_skips_comments_and_reports_unjudged(self):
        labels, unlabeled = self.read("# hi\n\nweak | Cancel\n? | Sol Ring\nPowerful|Lightning Bolt\n")
        self.assertEqual(labels, {"Cancel": Power.WEAK, "Lightning Bolt": Power.POWERFUL})
        self.assertEqual(unlabeled, ["Sol Ring"])

    def test_names_the_bad_line(self):
        with self.assertRaisesRegex(ValueError, ":1:"):
            self.read("Cancel\n")


class ScryfallTest(unittest.TestCase):
    def test_reads_two_faced_cards_from_the_front_face(self):
        c = card_from_scryfall(
            raw("Front // Back", cmc=3.0, card_faces=[{"mana_cost": "{2}{G}", "oracle_text": "A", "power": "2", "toughness": "3"}, {"oracle_text": "B"}], edhrec_rank=7)
        )
        self.assertEqual((c.mana_cost, c.oracle_text, c.power, c.toughness, c.edhrec_rank), ("{2}{G}", "A\n//\nB", "2", "3", 7))

    def test_one_batched_request_then_the_cache_answers(self):
        calls = []

        def post(url, body):
            calls.append(body)
            return {"data": [raw("Front // Back"), raw("Sol Ring")]}

        with tempfile.TemporaryDirectory() as d:
            catalog = ScryfallCatalog(os.path.join(d, "cache.json"), post_json=post, sleep=lambda s: None)
            first = catalog.find(["Sol Ring", "Front"])
            second = ScryfallCatalog(os.path.join(d, "cache.json"), post_json=post, sleep=lambda s: None).find(["sol ring"])
        self.assertEqual([c.name for c in first], ["Sol Ring", "Front // Back"])
        self.assertEqual(second[0].name, "Sol Ring")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["identifiers"], [{"name": "Sol Ring"}, {"name": "Front"}])

    def test_names_what_is_missing(self):
        catalog = ScryfallCatalog(None, post_json=lambda url, body: {"data": []}, sleep=lambda s: None)
        with self.assertRaisesRegex(LookupError, "Nope"):
            catalog.find(["Nope"])


class ClaudeClassifierTest(unittest.TestCase):
    def fake_client(self, parsed, stop_reason="end_turn"):
        self.seen = {}

        def parse(**kwargs):
            self.seen = kwargs
            return SimpleNamespace(parsed_output=parsed, stop_reason=stop_reason)

        return SimpleNamespace(messages=SimpleNamespace(parse=parse))

    def test_sends_the_facts_and_reads_the_verdict(self):
        classifier = ClaudeClassifier("haiku", client=self.fake_client(ClaudeAnswer(reason="Fair.", verdict="balanced")))
        verdict = classifier.classify(card())
        self.assertEqual((verdict.power, verdict.detail), (Power.BALANCED, "Fair."))
        self.assertEqual(self.seen["model"], "claude-haiku-4-5")
        self.assertIn("Name: Serra Angel", self.seen["messages"][0]["content"])
        self.assertIs(self.seen["output_format"], ClaudeAnswer)

    def test_a_missing_answer_is_an_error(self):
        classifier = ClaudeClassifier("sonnet", client=self.fake_client(None, stop_reason="refusal"))
        with self.assertRaisesRegex(RuntimeError, "refusal"):
            classifier.classify(card())


class JevClassifierTest(unittest.TestCase):
    def run_jev(self, kind, answer):
        sent = {}

        def post(url, body, key):
            sent.update(url=url, body=body, key=key)
            return {"answers": {QUESTION_ID: answer}}

        with mock.patch.dict(os.environ, {KEY_VARIABLE: "k"}):
            return JevClassifier(kind, post_json=post).classify(card()), sent

    def test_choice_asks_with_labelled_options(self):
        verdict, sent = self.run_jev("choice", {"type": "choice", "choice": "powerful", "confidence": 0.9, "probabilities": {"weak": 0.0, "balanced": 0.1, "powerful": 0.9}})
        self.assertEqual((verdict.power, verdict.confidence), (Power.POWERFUL, 0.9))
        self.assertEqual(list(sent["body"]["questions"][QUESTION_ID]["criteria"]), ["weak", "balanced", "powerful"])
        self.assertEqual((sent["key"], sent["body"]["model"]), ("k", "jev-latest"))
        self.assertIn("Name: Serra Angel", sent["body"]["state"])

    def test_score_asks_with_ordered_levels_and_rounds_the_answer(self):
        verdict, sent = self.run_jev("score", {"type": "score", "score": 1.43, "confidence": 0.35, "probabilities": {"0": 0.0, "1": 0.57, "2": 0.43}})
        self.assertEqual(verdict.power, Power.BALANCED)
        self.assertIn("balanced 0.57", verdict.detail)
        self.assertEqual(len(sent["body"]["questions"][QUESTION_ID]["criteria"]), 3)

    def test_no_key_is_an_error_not_a_crash_of_the_run(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, KEY_VARIABLE):
                JevClassifier("choice").classify(card())


class EvaluationTest(unittest.TestCase):
    class Broken:
        name = "broken"

        def classify(self, card):
            raise RuntimeError("boom")

    def setUp(self):
        self.cards = [LabeledCard(card("A", edhrec_rank=5), Power.WEAK), LabeledCard(card("B"), Power.BALANCED)]

    def test_one_failing_classifier_does_not_stop_the_others(self):
        evaluation = evaluate(self.cards, [self.Broken(), AlwaysBalanced()])
        self.assertEqual(evaluation.scorecard("broken").failed, 2)
        self.assertEqual(evaluation.scorecard("always-balanced").exact, 1)

    def test_report_shows_marks_errors_and_popularity(self):
        text = text_report(evaluate(self.cards, [self.Broken(), AlwaysBalanced()]))
        self.assertIn("balanced ✗", text)
        self.assertIn("balanced ✓", text)
        self.assertIn("broken on A: RuntimeError: boom", text)
        self.assertRegex(text, r"A\s+weak\s+ERROR\s+balanced ✗\s+5")

    def test_results_json_keeps_the_reasons(self):
        results = results_json(evaluate(self.cards, [AlwaysBalanced()]), {})
        self.assertEqual(results["cards"][0]["answers"]["always-balanced"]["power"], "balanced")
        self.assertEqual(results["scorecards"]["always-balanced"]["confusion"], {"weak->balanced": 1, "balanced->balanced": 1})


if __name__ == "__main__":
    unittest.main()
