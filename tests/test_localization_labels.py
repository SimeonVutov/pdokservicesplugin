# -*- coding: utf-8 -*-
"""Separation of identifiers, source titles and translated titles."""
import copy
import unittest

from pdokservicesplugin.localization.labels import (
    BILINGUAL_SEPARATOR,
    LayerLabel,
    bilingual,
    label_for_layer,
)

CATALOGUE_ENTRY = {
    "name": "waterdeel_vlak",
    "title": "Waterdeel vlak",
    "service_title": "BRT TOP10NL",
    "service_type": "api features",
    "service_md_id": "abc123",
}


class BilingualTest(unittest.TestCase):
    def test_combines_translation_and_original(self):
        self.assertEqual(
            bilingual("Water area", "Waterdeel vlak"),
            f"Water area{BILINGUAL_SEPARATOR}Waterdeel vlak",
        )

    def test_without_translation_the_original_stands_alone(self):
        self.assertEqual(bilingual(None, "Waterdeel vlak"), "Waterdeel vlak")
        self.assertEqual(bilingual("", "Waterdeel vlak"), "Waterdeel vlak")

    def test_translation_equal_to_original_is_not_repeated(self):
        self.assertEqual(bilingual("Pand", "Pand"), "Pand")
        self.assertEqual(bilingual("pand", "Pand"), "Pand")

    def test_missing_original_yields_the_translation(self):
        self.assertEqual(bilingual("Water area", ""), "Water area")
        self.assertEqual(bilingual(None, ""), "")


class LayerLabelTest(unittest.TestCase):
    def test_untranslated_label_shows_the_dutch_title(self):
        label = label_for_layer(CATALOGUE_ENTRY)
        self.assertEqual(label.display_title, "Waterdeel vlak")
        self.assertFalse(label.is_translated)

    def test_translated_label_keeps_the_dutch_original_visible(self):
        label = label_for_layer(CATALOGUE_ENTRY, translated_title="Water area")
        self.assertEqual(label.display_title, "Water area — Waterdeel vlak")
        self.assertIn("Waterdeel vlak", label.display_title)
        self.assertTrue(label.is_translated)

    def test_identifier_is_never_affected_by_translation(self):
        label = label_for_layer(CATALOGUE_ENTRY, translated_title="Water area")
        self.assertEqual(label.identifier, "waterdeel_vlak")
        self.assertNotIn(BILINGUAL_SEPARATOR, label.identifier)

    def test_source_title_survives_translation(self):
        label = label_for_layer(CATALOGUE_ENTRY, translated_title="Water area")
        self.assertEqual(label.source_title, "Waterdeel vlak")
        self.assertEqual(label.translated_title, "Water area")

    def test_service_title_is_translated_bilingually(self):
        label = label_for_layer(
            {"name": "x", "title": "y", "service_title": "CBS Wijken en Buurten"},
            translated_service_title="CBS Districts and Neighbourhoods",
        )
        self.assertEqual(
            label.display_service_title,
            "CBS Districts and Neighbourhoods — CBS Wijken en Buurten",
        )

    def test_building_a_label_does_not_modify_the_catalogue_entry(self):
        entry = copy.deepcopy(CATALOGUE_ENTRY)
        label_for_layer(entry, translated_title="Water area")
        self.assertEqual(entry, CATALOGUE_ENTRY)

    def test_entry_without_service_title_is_handled(self):
        label = label_for_layer({"name": "n", "title": "t", "service_title": None})
        self.assertEqual(label.display_service_title, "")

    def test_label_can_be_built_directly(self):
        label = LayerLabel("pand", "Pand", "Building")
        self.assertEqual(label.display_title, "Building — Pand")
        self.assertEqual(label.identifier, "pand")


if __name__ == "__main__":
    unittest.main()
