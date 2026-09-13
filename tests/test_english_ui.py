# -*- coding: utf-8 -*-
"""The shipped English translation of the plugin's own interface."""
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from qgis.PyQt.QtCore import QCoreApplication, QTranslator

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(REPO_ROOT, "pdokservicesplugin")
TS_PATH = os.path.join(PLUGIN_DIR, "i18n", "pdokservicesplugin_en.ts")
QM_PATH = os.path.join(PLUGIN_DIR, "i18n", "pdokservicesplugin_en.qm")

_app = None
_translator = None


def setUpModule():
    global _app, _translator
    _app = QCoreApplication.instance() or QCoreApplication([])
    _translator = QTranslator()
    assert _translator.load(QM_PATH), f"could not load {QM_PATH}"
    assert QCoreApplication.installTranslator(_translator)


def tearDownModule():
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)


def tr(context, source):
    return QCoreApplication.translate(context, source)


class TranslationResourcesTest(unittest.TestCase):
    def test_translation_files_are_shipped(self):
        self.assertTrue(os.path.exists(TS_PATH), "missing .ts source")
        self.assertTrue(os.path.exists(QM_PATH), "missing compiled .qm")

    def test_ts_declares_its_languages(self):
        root = ET.parse(TS_PATH).getroot()
        self.assertEqual(root.get("language"), "en")
        self.assertEqual(root.get("sourcelanguage"), "nl")

    def test_every_message_is_translated(self):
        root = ET.parse(TS_PATH).getroot()
        unfinished = []
        for context in root.findall("context"):
            for message in context.findall("message"):
                node = message.find("translation")
                if node is not None and node.get("type") == "unfinished":
                    unfinished.append(
                        f"{context.findtext('name')}: {message.findtext('source')}"
                    )
        self.assertEqual(unfinished, [], "untranslated messages remain")

    def test_qm_recompiles_from_the_committed_ts(self):
        lrelease = next(
            (
                shutil.which(name)
                for name in ("lrelease6", "lrelease-qt6", "lrelease")
                if shutil.which(name)
            ),
            None,
        )
        if lrelease is None:
            self.skipTest("no lrelease available")
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.qm")
            result = subprocess.run(
                [lrelease, TS_PATH, "-qm", out], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("unfinished", result.stdout.replace("0 unfinished", ""))
            self.assertTrue(os.path.getsize(out) > 0)


class GenericUiIsEnglishTest(unittest.TestCase):
    """Generic controls must be fully English, never bilingual."""

    DIALOG = "PdokServicesPluginDialog"
    PLUGIN = "PdokServicesPlugin"

    def test_dialog_controls_are_translated(self):
        for source, expected in [
            ("Zoeken", "Search"),
            ("Zoek", "Search"),
            ("Laag toevoegen", "Add layer"),
            ("Standaard", "Default"),
            ("Boven", "Top"),
            ("Onder", "Bottom"),
            ("Instellingen", "Settings"),
            ("Zoek Type", "Search type"),
            ("Gemeente", "Municipality"),
            ("Adres", "Address"),
            ("Taal", "Language"),
        ]:
            self.assertEqual(tr(self.DIALOG, source), expected, source)

    def test_plugin_strings_are_translated(self):
        for source, expected in [
            ("Laagnaam", "Layer name"),
            ("Resultaat", "Result"),
            ("Zoek in PDOK Locatieserver", "Search PDOK Location Server"),
            ("Voeg deze laag toe aan favorieten", "Add this layer to favourites"),
            ("Verwijder deze laag uit favorieten", "Remove this layer from favourites"),
            ("Niet ingevuld", "Not provided"),
            ("Taal", "Language"),
            ("Automatisch (volg QGIS)", "Automatic (follow QGIS)"),
        ]:
            self.assertEqual(tr(self.PLUGIN, source), expected, source)

    def test_generic_controls_are_not_bilingual(self):
        dutch_words = ("Zoeken", "Laagnaam", "Annuleren", "Toevoegen", "Verwijder")
        for context, source in [
            (self.DIALOG, "Zoeken"),
            (self.DIALOG, "Laag toevoegen"),
            (self.DIALOG, "Standaard"),
            (self.PLUGIN, "Laagnaam"),
            (self.PLUGIN, "Verwijder deze laag uit favorieten"),
        ]:
            translated = tr(context, source)
            self.assertNotIn("—", translated, f"{source} became bilingual")
            self.assertNotIn("(", translated, f"{source} carries a Dutch gloss")
            for word in dutch_words:
                self.assertNotIn(word, translated, f"{source} kept Dutch text")

    def test_official_product_names_are_preserved(self):
        # Class 2: acronyms and product names are never translated away.
        self.assertEqual(tr(self.DIALOG, "PDOK Locatieserver"), "PDOK Locatieserver")
        self.assertEqual(tr("PDOKWCSTool", "AHN"), "AHN")
        self.assertIn("BAG", tr(self.DIALOG, "Weg (BAG openbare ruimte)"))


class ProcessingTranslationContextTest(unittest.TestCase):
    """Regression guard: the algorithms used context "Processing" while lupdate
    recorded the class name, so their translations never loaded."""

    def test_ts_has_no_processing_context(self):
        root = ET.parse(TS_PATH).getroot()
        names = {c.findtext("name") for c in root.findall("context")}
        self.assertNotIn("Processing", names)
        for expected in ("PDOKGeocoder", "PDOKReverseGeocoder", "PDOKWCSTool"):
            self.assertIn(expected, names)

    def test_algorithms_translate_through_their_own_context(self):
        from pdokservicesplugin.processing_provider.processing_ahn import PDOKWCSTool
        from pdokservicesplugin.processing_provider.processing_geocoder import (
            PDOKGeocoder,
        )
        from pdokservicesplugin.processing_provider.processing_reverse_geocoder import (
            PDOKReverseGeocoder,
        )

        self.assertEqual(PDOKGeocoder().tr("Locatie Server"), "PDOK Locatieserver")
        self.assertEqual(
            PDOKReverseGeocoder().tr("Fields (comma seperated list)"),
            "Fields (comma separated list)",
        )
        self.assertEqual(PDOKWCSTool().tr("AHN"), "AHN")


class PackagingTest(unittest.TestCase):
    def test_zip_contains_the_compiled_translation(self):
        if shutil.which("zip") is None or shutil.which("make") is None:
            self.skipTest("zip/make not available")
        result = subprocess.run(
            ["make", "zip"], cwd=REPO_ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        built = [
            os.path.join(REPO_ROOT, "repo", name)
            for name in os.listdir(os.path.join(REPO_ROOT, "repo"))
            if name.endswith(".zip")
        ]
        self.assertTrue(built, "no zip produced")
        newest = max(built, key=os.path.getmtime)
        with zipfile.ZipFile(newest) as archive:
            names = archive.namelist()
        self.assertIn("pdokservicesplugin/i18n/pdokservicesplugin_en.qm", names)
        # The .ts is a development source and does not belong in the package.
        self.assertNotIn("pdokservicesplugin/i18n/pdokservicesplugin_en.ts", names)


if __name__ == "__main__":
    unittest.main()
