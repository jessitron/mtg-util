import os
import tempfile
import unittest

from prepared_cards.adapters.archidekt_file import ArchidektImportFile
from prepared_cards.adapters.cached_catalog import CachedCatalog
from prepared_cards.adapters.scryfall_catalog import ScryfallCatalog, card_from_scryfall
from prepared_cards.domain.card import Card
from prepared_cards.domain.card_pool import CardPool
from prepared_cards.domain.selection import Selection
from prepared_cards.orchestration.http_app import pool_to_json
from prepared_cards.orchestration.use_cases import CardPicker


def card(name, mv):
    return Card(name, mv, "", "Creature", f"http://img/{name}", f"http://page/{name}")


def raw(name, cmc, **extra):
    return {"name": name, "cmc": cmc, "scryfall_uri": f"http://s/{name}", **extra}


class CardPoolTest(unittest.TestCase):
    def test_groups_by_mana_value_ascending_then_name(self):
        pool = CardPool.of([card("B", 2.0), card("A", 2.0), card("Z", 0.0)])
        groups = pool.by_mana_value()
        self.assertEqual([g.mana_value for g in groups], [0.0, 2.0])
        self.assertEqual([c.name for c in groups[1].cards], ["A", "B"])


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

        picker = CardPicker(Catalog(), Store())
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
    def test_labels_whole_mana_values_without_decimal(self):
        data = pool_to_json(CardPool.of([card("A", 3.0), card("B", 0.5)]))
        self.assertEqual([g["label"] for g in data["groups"]], ["Mana value 0.5", "Mana value 3"])


if __name__ == "__main__":
    unittest.main()
