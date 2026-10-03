import json
import os
import random
import sqlite3
import tempfile
import unittest
import unittest.mock
from dataclasses import replace

from prepared_cards.adapters.archidekt_file import ArchidektImportFile
from prepared_cards.adapters.cached_catalog import CachedCatalog
from prepared_cards.adapters.cached_power_score import CachedPowerScore
from prepared_cards.adapters.jev_power_score import JevPowerScore
from prepared_cards.adapters.llm_power_score import LlmPowerScore
from prepared_cards.adapters.mtgjson_rules_text import MtgjsonRulesText
from prepared_cards.adapters.random_power_score import RandomPowerScore
from prepared_cards.adapters.scryfall_catalog import ScryfallCatalog, card_from_scryfall
from prepared_cards.domain.card import Card
from prepared_cards.domain.card_pool import CardPool
from prepared_cards.domain.card_rules import CardFace, CardRules
from prepared_cards.domain.selection import Selection
from prepared_cards.orchestration.http_app import ranked_to_json
from prepared_cards.orchestration.use_cases import CardPicker


def card(name, mv):
    return Card(name, mv, "", "Creature", f"http://img/{name}", f"http://page/{name}", f"id-{name}")


def raw(name, cmc, **extra):
    return {"name": name, "cmc": cmc, "scryfall_uri": f"http://s/{name}", "id": f"id-{name}", **extra}


class FixedScores:
    """A PowerScore that reads from a dict and counts its calls."""

    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def score(self, c):
        self.calls.append(c.name)
        return self.scores[c.name]


class CardPoolTest(unittest.TestCase):
    def test_ranks_most_powerful_first_with_ties_in_name_order(self):
        pool = CardPool.of([card("B", 2.0), card("A", 2.0), card("Z", 0.0), card("M", 5.0)])
        ranked = pool.ranked(FixedScores({"A": 1.0, "B": 1.0, "Z": 1.9, "M": 0.2}))
        self.assertEqual([(s.card.name, s.score) for s in ranked], [("Z", 1.9), ("A", 1.0), ("B", 1.0), ("M", 0.2)])


class RandomPowerScoreTest(unittest.TestCase):
    def test_scores_fall_between_0_and_2(self):
        power = RandomPowerScore(random.Random(1))
        self.assertTrue(all(0 <= power.score(card("A", 1.0)) <= 2 for _ in range(100)))


class CachedPowerScoreTest(unittest.TestCase):
    def test_scores_each_card_once_and_remembers_across_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "scores.json")
            source = FixedScores({"A": 1.5})
            cached = CachedPowerScore(source, path)
            self.assertEqual(cached.score(card("A", 1.0)), 1.5)
            self.assertEqual(cached.score(card("A", 1.0)), 1.5)
            self.assertEqual(source.calls, ["A"])
            later = FixedScores({})
            self.assertEqual(CachedPowerScore(later, path).score(card("A", 1.0)), 1.5)
            self.assertEqual(later.calls, [])


class LlmPowerScoreTest(unittest.TestCase):
    class Rules:
        def __init__(self, rules):
            self.rules = rules

        def rules_for(self, c):
            return self.rules

    class Client:
        """Stands in for anthropic.Anthropic: records the request, answers with a canned score."""

        def __init__(self, score, parsed=True):
            self.requests = []
            self.messages = self
            self._score, self._parsed = score, parsed

        def parse(self, **request):
            self.requests.append(request)
            answer = type("A", (), {"reason": "because", "score": self._score})()
            return type("R", (), {"parsed_output": answer if self._parsed else None, "stop_reason": "refusal"})()

    creature = CardFace("Trio", "{2}{G}", 3.0, "Creature", "Becomes prepared.", "3", "3")
    spell = CardFace("Brainstorm", "{U}", 1.0, "Instant", "Draw three cards.")

    def test_judges_the_back_face_alone_with_the_spell_note(self):
        client = self.Client(1.7)
        scorer = LlmPowerScore(self.Rules(CardRules((self.creature, self.spell))), "m", client)
        self.assertEqual(scorer.score(card("Trio // Brainstorm", 3.0)), 1.7)
        sent = client.requests[0]["messages"][0]["content"]
        self.assertIn("Name: Brainstorm", sent)
        self.assertIn("mana value 1)", sent)
        self.assertIn("Draw three cards.", sent)
        self.assertIn("Ignore the creature", sent)
        self.assertNotIn("Trio", sent)
        self.assertEqual(client.requests[0]["model"], "m")

    def test_a_one_face_card_gets_no_spell_note(self):
        client = self.Client(1.0)
        LlmPowerScore(self.Rules(CardRules((self.spell,))), "m", client).score(card("Brainstorm", 1.0))
        self.assertNotIn("Note:", client.requests[0]["messages"][0]["content"])

    def test_clamps_to_the_range(self):
        for said, want in [(3.4, 2.0), (-1.0, 0.0)]:
            scorer = LlmPowerScore(self.Rules(CardRules((self.spell,))), "m", self.Client(said))
            self.assertEqual(scorer.score(card("B", 1.0)), want)

    def test_no_parsed_answer_is_an_error(self):
        scorer = LlmPowerScore(self.Rules(CardRules((self.spell,))), "m", self.Client(1.0, parsed=False))
        with self.assertRaisesRegex(RuntimeError, "no score"):
            scorer.score(card("B", 1.0))


class JevPowerScoreTest(unittest.TestCase):
    creature = LlmPowerScoreTest.creature
    spell = LlmPowerScoreTest.spell

    def scorer(self, rules, said=1.43, posts=None):
        def post(url, body, key):
            if posts is not None:
                posts.append((url, body, key))
            return {"answers": {"power_for_cost": {"type": "score", "score": said}}}

        return JevPowerScore(LlmPowerScoreTest.Rules(rules), post_json=post)

    def test_asks_a_three_level_score_question_about_the_back_face_alone(self):
        posts = []
        with unittest.mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "k"}):
            got = self.scorer(CardRules((self.creature, self.spell)), posts=posts).score(card("Trio // Brainstorm", 3.0))
        self.assertEqual(got, 1.43)
        url, body, key = posts[0]
        self.assertEqual((url, key, body["model"]), ("https://api.typesafe.ai/v1/systemone", "k", "jev-latest"))
        question = body["questions"]["power_for_cost"]
        self.assertEqual((question["type"], len(question["criteria"])), ("score", 3))
        self.assertIn("Name: Brainstorm", body["state"])
        self.assertIn("Ignore the creature", body["state"])
        self.assertNotIn("Trio", body["state"])

    def test_clamps_to_the_range(self):
        with unittest.mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "k"}):
            self.assertEqual(self.scorer(CardRules((self.spell,)), said=2.6).score(card("B", 1.0)), 2.0)

    def test_a_missing_key_says_which_variable(self):
        with unittest.mock.patch.dict(os.environ, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TYPESAFE_API_KEY"):
                self.scorer(CardRules((self.spell,))).score(card("B", 1.0))


class SelectionTest(unittest.TestCase):
    def test_dedupes_and_drops_blanks_keeping_order(self):
        self.assertEqual(Selection.of(["B", "A", "B", " "]).names, ("B", "A"))


class ScryfallTranslationTest(unittest.TestCase):
    def test_reads_image_from_top_level(self):
        c = card_from_scryfall(raw("X // Y", 2.0, image_uris={"normal": "top.jpg"}))
        self.assertEqual((c.name, c.mana_value, c.image_url), ("X // Y", 2.0, "top.jpg"))

    def test_falls_back_to_front_face_image(self):
        c = card_from_scryfall(raw("X", 1.0, card_faces=[{"image_uris": {"normal": "front.jpg"}}]))
        self.assertEqual(c.image_url, "front.jpg")

    def test_missing_image_is_empty(self):
        self.assertEqual(card_from_scryfall(raw("X", 1.0)).image_url, "")

    def test_follows_pagination_politely(self):
        calls, sleeps = [], []

        def get_json(url):
            calls.append(url)
            if len(calls) == 1:
                return {"data": [raw("B", 1.0)], "next_page": "http://page2"}
            return {"data": [raw("A", 1.0)]}

        pool = ScryfallCatalog("o:prepared", get_json, sleeps.append).pool()
        self.assertEqual([c.name for c in pool.cards], ["A", "B"])
        self.assertEqual(len(sleeps), 1)
        self.assertIn("q=o%3Aprepared", calls[0])


class CachedCatalogTest(unittest.TestCase):
    def test_fetches_once_then_reads_cache_until_refresh(self):
        class Counting:
            n = 0

            def pool(self):
                return self.refresh()

            def refresh(self):
                self.n += 1
                return CardPool.of([card(f"C{self.n}", 1.0)])

        with tempfile.TemporaryDirectory() as d:
            source = Counting()
            cached = CachedCatalog(source, os.path.join(d, "cards.json"))
            self.assertEqual(cached.pool().cards[0].name, "C1")
            self.assertEqual(cached.pool().cards[0].name, "C1")
            self.assertEqual(source.n, 1)
            self.assertEqual(cached.refresh().cards[0].name, "C2")
            self.assertEqual(cached.pool().cards[0].name, "C2")


    def test_a_cache_written_before_scryfall_id_is_refetched(self):
        class Source:
            def pool(self):
                return self.refresh()

            def refresh(self):
                return CardPool.of([card("New", 1.0)])

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cards.json")
            with open(path, "w") as f:
                json.dump([{"name": "Old", "mana_value": 1.0, "mana_cost": "", "type_line": "", "image_url": "", "page_url": ""}], f)
            self.assertEqual(CachedCatalog(Source(), path).pool().cards[0].name, "New")


class MtgjsonRulesTextTest(unittest.TestCase):
    def database(self, d):
        path = os.path.join(d, "cards.sqlite")
        db = sqlite3.connect(path)
        db.executescript("""
            create table cards (uuid text, side text, faceName text, name text, manaCost text, faceManaValue real,
                                manaValue real, type text, text text, power text, toughness text);
            create table cardIdentifiers (uuid text, scryfallId text);
            insert into cards values
              ('u1', 'a', 'Trio', 'Trio // Brainstorm', '{U}', 1.0, 1.0, 'Creature', 'Becomes prepared.', '1', '1'),
              ('u2', 'b', 'Brainstorm', 'Trio // Brainstorm', '{U}', 1.0, 1.0, 'Instant', 'Draw three cards.', NULL, NULL),
              ('u3', NULL, NULL, 'Opt', '{U}', NULL, 1.0, 'Instant', 'Scry 1. Draw a card.', NULL, NULL);
            insert into cardIdentifiers values ('u1', 'sid-trio'), ('u2', 'sid-trio'), ('u3', 'sid-opt');
        """)
        db.commit()
        db.close()
        return path

    def test_finds_every_face_by_scryfall_id_front_first(self):
        with tempfile.TemporaryDirectory() as d:
            rules = MtgjsonRulesText(self.database(d)).rules_for(replace(card("Trio // Brainstorm", 1.0), scryfall_id="sid-trio"))
            self.assertEqual([f.name for f in rules.faces], ["Trio", "Brainstorm"])
            self.assertEqual((rules.faces[0].power, rules.faces[0].toughness), ("1", "1"))
            self.assertEqual(rules.spell.text, "Draw three cards.")
            self.assertEqual(rules.spell.type_line, "Instant")

    def test_a_one_face_card_is_its_own_spell(self):
        with tempfile.TemporaryDirectory() as d:
            rules = MtgjsonRulesText(self.database(d)).rules_for(replace(card("Opt", 1.0), scryfall_id="sid-opt"))
            self.assertEqual((rules.spell.name, rules.spell.mana_value, rules.spell.power), ("Opt", 1.0, ""))

    def test_an_unknown_id_is_a_lookup_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(LookupError):
                MtgjsonRulesText(self.database(d)).rules_for(card("Nope", 1.0))

    def test_a_missing_database_says_how_to_fetch_it(self):
        with self.assertRaisesRegex(FileNotFoundError, "mtgjson/run"):
            MtgjsonRulesText("/no/such/file.sqlite")


class ArchidektImportFileTest(unittest.TestCase):
    def test_round_trips_in_import_format(self):
        with tempfile.TemporaryDirectory() as d:
            store = ArchidektImportFile(os.path.join(d, "selected.txt"))
            self.assertEqual(store.load(), Selection())
            store.save(Selection.of(["Harmonized Trio // Brainstorm", "Opt"]))
            with open(store.path) as f:
                self.assertEqual(f.read(), "1 Harmonized Trio // Brainstorm\n1 Opt\n")
            self.assertEqual(store.load().names, ("Harmonized Trio // Brainstorm", "Opt"))


class CardPickerTest(unittest.TestCase):
    def test_saves_the_selection(self):
        saved = []

        class Store:
            def load(self):
                return Selection.of(saved)

            def save(self, selection):
                saved[:] = selection.names

            def render(self, selection):
                return "".join(f"1 {n}\n" for n in selection.names)

        class Catalog:
            def pool(self):
                return CardPool.of([card("A", 1.0)])

            refresh = pool

        picker = CardPicker(Catalog(), FixedScores({"A": 1.0}), Store())
        picker.save_selection(["A", "A"])
        self.assertEqual(picker.current_selection().names, ("A",))
        self.assertEqual(picker.save_and_render(["A", "B"]), "1 A\n1 B\n")


class GathererLinkTest(unittest.TestCase):
    def test_searches_by_front_face_name(self):
        self.assertEqual(card("Harmonized Trio // Brainstorm", 3.0).gatherer_url,
                         "https://gatherer.wizards.com/search?searchTerm=Harmonized%20Trio")
        self.assertEqual(card("Abigale, Poet Laureate // Heroic Stanza", 3.0).gatherer_url,
                         "https://gatherer.wizards.com/search?searchTerm=Abigale%2C%20Poet%20Laureate")


class PageJsonTest(unittest.TestCase):
    def test_lists_cards_with_scores_in_ranked_order(self):
        ranked = CardPool.of([card("A", 3.0), card("B", 0.5)]).ranked(FixedScores({"A": 0.4, "B": 1.7}))
        data = ranked_to_json(ranked)
        self.assertEqual([(c["name"], c["score"]) for c in data["cards"]], [("B", 1.7), ("A", 0.4)])

    def test_picker_ranks_the_catalog_through_the_power_score(self):
        class Catalog:
            def pool(self):
                return CardPool.of([card("A", 1.0), card("B", 1.0)])

            refresh = pool

        picker = CardPicker(Catalog(), FixedScores({"A": 0.1, "B": 0.9}), store=None)
        self.assertEqual([s.card.name for s in picker.ranked_candidates()], ["B", "A"])


if __name__ == "__main__":
    unittest.main()
