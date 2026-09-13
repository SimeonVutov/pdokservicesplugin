# -*- coding: utf-8 -*-
"""Curated English names for PDOK services and layers."""
import copy
import json
import os
import tempfile
import unittest

from pdokservicesplugin.localization import label_for_layer
from pdokservicesplugin.localization import pdok_metadata as meta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(REPO_ROOT, "pdokservicesplugin")
CATALOGUE = os.path.join(PLUGIN_DIR, "resources", "layers-pdok.json")
RESOURCE = meta.resource_path("en", PLUGIN_DIR)


def translations():
    return meta.translations_for("en", PLUGIN_DIR)


class ResourceTest(unittest.TestCase):
    def test_curated_resource_is_shipped_and_valid(self):
        self.assertTrue(os.path.exists(RESOURCE))
        with open(RESOURCE, encoding="utf-8") as handle:
            data = json.load(handle)
        for section in (
            "layer_titles",
            "layer_title_bases",
            "layer_title_suffixes",
            "service_titles",
        ):
            self.assertIn(section, data)
            self.assertIsInstance(data[section], dict)

    def test_every_suffix_template_uses_the_base(self):
        with open(RESOURCE, encoding="utf-8") as handle:
            suffixes = json.load(handle)["layer_title_suffixes"]
        for key, template in suffixes.items():
            self.assertIn("{base}", template, key)

    def test_translations_live_outside_the_generated_catalogue(self):
        """Regenerating layers-pdok.json must not be able to destroy them."""
        with open(CATALOGUE, encoding="utf-8") as handle:
            catalogue = json.load(handle)
        for entry in catalogue[:200]:
            for field in ("title_en", "service_title_en", "translated_title"):
                self.assertNotIn(field, entry)
        self.assertNotIn("translations", os.path.basename(CATALOGUE))
        self.assertTrue(RESOURCE.endswith(os.path.join("translations", "pdok_metadata_en.json")))

    def test_catalogue_is_valid_json_with_expected_fields(self):
        with open(CATALOGUE, encoding="utf-8") as handle:
            catalogue = json.load(handle)
        self.assertGreater(len(catalogue), 1000)
        for entry in catalogue[:50]:
            for field in ("name", "title", "service_title", "service_type"):
                self.assertIn(field, entry)


class LookupTest(unittest.TestCase):
    def setUp(self):
        self.tr = translations()

    def test_the_documented_examples_resolve(self):
        for source, expected in [
            ("Waterdeel vlak", "Water area"),
            ("Waterdeel lijn", "Water line"),
            ("Wegdeel hartlijn", "Road centreline"),
            ("Terrein vlak", "Terrain area"),
            ("Pand", "Building"),
        ]:
            self.assertEqual(self.tr.title(source), expected, source)

    def test_lookup_ignores_case_and_underscores(self):
        for spelling in ("Waterdeel vlak", "waterdeel_vlak", "WATERDEEL  VLAK"):
            self.assertEqual(self.tr.title(spelling), "Water area", spelling)

    def test_official_abbreviation_is_kept_untranslated(self):
        self.assertEqual(self.tr.title("Wegdeel (WGD)"), "Road (WGD)")
        self.assertEqual(
            self.tr.title("Begroeid terreindeel (BTD)"), "Vegetated terrain (BTD)"
        )

    def test_longest_suffix_wins(self):
        self.assertEqual(self.tr.title("Buurt labelpoint"), "Neighbourhood label point")
        self.assertEqual(self.tr.title("Plaatslabel"), "Place label")

    def test_unknown_title_has_no_translation(self):
        for source in ("Volstrekt onbekende laag", "TOP25raster", "", None):
            self.assertIsNone(self.tr.title(source), source)

    def test_service_titles(self):
        self.assertEqual(
            self.tr.service_title("CBS Wijken en Buurten"),
            "CBS Districts and Neighbourhoods",
        )
        # Acronyms and product names are left alone.
        self.assertIsNone(self.tr.service_title("BRT TOP10NL"))
        self.assertIsNone(self.tr.service_title("BAG WMS"))


class ResolutionOrderTest(unittest.TestCase):
    def setUp(self):
        self.tr = translations()
        self.entry = {
            "name": "waterdeel_vlak",
            "title": "Waterdeel vlak",
            "service_title": "BRT TOP10NL",
        }

    def test_curated_translation_is_used_when_pdok_offers_none(self):
        self.assertEqual(meta.translated_title(self.entry, self.tr), "Water area")

    def test_official_english_from_pdok_wins_over_the_curated_name(self):
        entry = dict(self.entry, title_en="Water body polygon")
        self.assertEqual(meta.translated_title(entry, self.tr), "Water body polygon")

    def test_untranslatable_title_falls_back_to_dutch(self):
        entry = dict(self.entry, title="Volstrekt onbekende laag")
        self.assertIsNone(meta.translated_title(entry, self.tr))
        label = label_for_layer(entry)
        self.assertEqual(label.display_title, "Volstrekt onbekende laag")


class ResourceFailureTest(unittest.TestCase):
    def test_missing_resource_yields_no_translations(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(meta.load_translations("en", tmp))

    def test_broken_resource_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = meta.resource_path("en", tmp)
            os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{ this is not json")
            result = meta.load_translations("en", tmp)
            self.assertFalse(result)
            self.assertIsNone(result.title("Waterdeel vlak"))

    def test_no_language_yields_no_translations(self):
        self.assertFalse(meta.translations_for("", PLUGIN_DIR))


class CachingTest(unittest.TestCase):
    def test_resource_is_read_once_per_language(self):
        meta.clear_cache()
        first = meta.translations_for("en", PLUGIN_DIR)
        second = meta.translations_for("en", PLUGIN_DIR)
        self.assertIs(first, second)


class IdentifierSafetyTest(unittest.TestCase):
    """A bilingual display title must never leak into a request."""

    def setUp(self):
        self.tr = translations()
        self.entry = {
            "name": "waterdeel_vlak",
            "title": "Waterdeel vlak",
            "service_title": "BRT TOP10NL",
            "service_type": "api features",
            "service_md_id": "abc",
        }

    def label(self):
        return label_for_layer(
            self.entry,
            translated_title=meta.translated_title(self.entry, self.tr),
            translated_service_title=meta.translated_service_title(self.entry, self.tr),
        )

    def test_identifier_is_untouched_while_display_is_bilingual(self):
        label = self.label()
        self.assertEqual(label.identifier, "waterdeel_vlak")
        self.assertEqual(label.display_title, "Water area — Waterdeel vlak")

    def test_request_uri_uses_the_identifier_not_the_display_title(self):
        label = self.label()
        uri = (
            f" pagingEnabled='true' typename='{label.identifier}' "
            f"url='https://api.pdok.nl/kadaster/brt-top10nl/ogc/v1'"
        )
        self.assertIn("typename='waterdeel_vlak'", uri)
        self.assertNotIn("Water area", uri)
        self.assertNotIn("—", uri)

    def test_translating_does_not_modify_the_catalogue_entry(self):
        before = copy.deepcopy(self.entry)
        self.label()
        self.assertEqual(self.entry, before)

    def test_favourite_matching_is_unaffected_by_translation(self):
        # Favourites match on service_md_id + name, never on the title.
        favourite = {"name": "waterdeel_vlak", "service_md_id": "abc"}
        label = self.label()
        self.assertEqual(favourite["name"], label.identifier)
        self.assertEqual(favourite["service_md_id"], self.entry["service_md_id"])


class BilingualSearchTest(unittest.TestCase):
    def setUp(self):
        self.tr = translations()
        entry = {
            "name": "wegdeel_hartlijn",
            "title": "Wegdeel hartlijn",
            "service_title": "BRT TOP10NL",
        }
        self.label = label_for_layer(
            entry,
            translated_title=meta.translated_title(entry, self.tr),
            translated_service_title=meta.translated_service_title(entry, self.tr),
        )
        self.haystack = " ".join(self.label.search_terms).lower()

    def test_english_query_finds_the_layer(self):
        for query in ("road", "centreline", "road centreline"):
            self.assertIn(query, self.haystack, query)

    def test_dutch_query_still_finds_the_layer(self):
        for query in ("wegdeel", "hartlijn"):
            self.assertIn(query, self.haystack, query)

    def test_identifier_is_searchable(self):
        self.assertIn("wegdeel_hartlijn", self.haystack)

    def test_unrelated_query_does_not_match(self):
        self.assertNotIn("kadaster-perceel", self.haystack)

    def test_dutch_mode_search_terms_contain_no_english(self):
        dutch = label_for_layer(
            {"name": "wegdeel_hartlijn", "title": "Wegdeel hartlijn", "service_title": "BRT TOP10NL"}
        )
        self.assertNotIn("Road centreline", " ".join(dutch.search_terms))


class CoverageTest(unittest.TestCase):
    def test_a_useful_share_of_the_catalogue_is_translated(self):
        tr = translations()
        with open(CATALOGUE, encoding="utf-8") as handle:
            catalogue = json.load(handle)
        translated = sum(
            1
            for entry in catalogue
            if isinstance(entry.get("title"), str) and tr.title(entry["title"])
        )
        share = translated / len(catalogue)
        self.assertGreater(share, 0.5, f"only {share:.1%} of rows translated")

    def test_untranslated_rows_still_produce_a_usable_label(self):
        tr = translations()
        with open(CATALOGUE, encoding="utf-8") as handle:
            catalogue = json.load(handle)
        for entry in catalogue:
            if not isinstance(entry.get("title"), str):
                continue
            label = label_for_layer(
                entry, translated_title=meta.translated_title(entry, tr)
            )
            self.assertTrue(label.display_title)
            self.assertIn(entry["title"], label.display_title)


if __name__ == "__main__":
    unittest.main()
