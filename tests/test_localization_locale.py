# -*- coding: utf-8 -*-
"""Locale detection, translator loading and fallback behaviour."""
import os
import shutil
import subprocess
import tempfile
import unittest

from qgis.PyQt.QtCore import QCoreApplication

from pdokservicesplugin.localization import locale as loc

_app = None


def setUpModule():
    global _app
    _app = QCoreApplication.instance() or QCoreApplication([])


def find_lrelease():
    for name in ("lrelease6", "lrelease-qt6", "lrelease"):
        path = shutil.which(name)
        if path:
            return path
    return None


MINIMAL_TS = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS><TS version="2.1" language="en">
<context>
    <name>TestContext</name>
    <message>
        <source>Zoeken</source>
        <translation>Search</translation>
    </message>
</context>
</TS>
"""


class LanguageFromLocaleTest(unittest.TestCase):
    def test_reduces_locale_names_to_language_code(self):
        for value, expected in [
            ("en", "en"),
            ("en_GB", "en"),
            ("en-GB", "en"),
            ("en_US.UTF-8", "en"),
            ("EN_gb", "en"),
            ("nl_NL", "nl"),
            ("ca_ES@valencia", "ca"),
        ]:
            self.assertEqual(loc.language_from_locale(value), expected, value)

    def test_empty_input_yields_empty_string(self):
        self.assertEqual(loc.language_from_locale(""), "")
        self.assertEqual(loc.language_from_locale(None), "")


class SelectLanguageTest(unittest.TestCase):
    def test_supported_language_is_selected(self):
        self.assertEqual(loc.select_language("en_GB"), "en")

    def test_source_language_needs_no_translation(self):
        self.assertIsNone(loc.select_language("nl_NL"))

    def test_unsupported_locale_falls_back_to_source_language(self):
        for value in ("de_DE", "fr", "ca_ES@valencia", "", None, "zz"):
            self.assertIsNone(loc.select_language(value), value)


class ResolveLanguageTest(unittest.TestCase):
    def test_auto_follows_the_qgis_locale(self):
        self.assertEqual(loc.resolve_language(loc.AUTO, "en_GB"), "en")
        self.assertIsNone(loc.resolve_language(loc.AUTO, "nl_NL"))

    def test_explicit_preference_overrides_the_locale(self):
        self.assertEqual(loc.resolve_language("en", "nl_NL"), "en")
        self.assertIsNone(loc.resolve_language("nl", "en_GB"))

    def test_unknown_preference_falls_back_to_source_language(self):
        self.assertIsNone(loc.resolve_language("klingon", "en_GB"))


class TranslationFileTest(unittest.TestCase):
    def test_missing_translation_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(loc.translation_file("en", tmp))

    def test_no_language_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(loc.translation_file(None, tmp))


class PluginTranslatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.i18n = os.path.join(self.tmp, loc.I18N_DIRNAME)
        os.makedirs(self.i18n)
        self.translator = loc.PluginTranslator(self.tmp)

    def tearDown(self):
        self.translator.unload()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def compile_translation(self):
        lrelease = find_lrelease()
        if lrelease is None:
            self.skipTest("no lrelease available to compile a .qm")
        ts_path = os.path.join(self.i18n, f"{loc.TRANSLATION_PREFIX}_en.ts")
        qm_path = os.path.join(self.i18n, f"{loc.TRANSLATION_PREFIX}_en.qm")
        with open(ts_path, "w", encoding="utf-8") as handle:
            handle.write(MINIMAL_TS)
        subprocess.run(
            [lrelease, ts_path, "-qm", qm_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return qm_path

    def test_dutch_preference_installs_nothing(self):
        changed = self.translator.apply(preference="nl", locale_name="en_GB")
        self.assertFalse(changed)
        self.assertEqual(self.translator.language, loc.SOURCE_LANGUAGE)

    def test_missing_qm_falls_back_to_source_language(self):
        self.translator.apply(preference="en", locale_name="en_GB")
        self.assertEqual(self.translator.language, loc.SOURCE_LANGUAGE)

    def test_unreadable_qm_does_not_raise(self):
        qm_path = os.path.join(self.i18n, f"{loc.TRANSLATION_PREFIX}_en.qm")
        with open(qm_path, "wb") as handle:
            handle.write(b"this is not a translation catalogue")
        self.translator.apply(preference="en", locale_name="en_GB")
        self.assertEqual(self.translator.language, loc.SOURCE_LANGUAGE)

    def test_compiled_translation_is_installed_and_used(self):
        self.compile_translation()
        self.translator.apply(preference="en", locale_name="nl_NL")
        self.assertEqual(self.translator.language, "en")
        self.assertEqual(loc.tr("TestContext", "Zoeken"), "Search")

    def test_switching_back_to_dutch_restores_source_strings(self):
        self.compile_translation()
        self.translator.apply(preference="en", locale_name="nl_NL")
        self.assertEqual(loc.tr("TestContext", "Zoeken"), "Search")

        changed = self.translator.apply(preference="nl", locale_name="nl_NL")
        self.assertTrue(changed)
        self.assertEqual(self.translator.language, loc.SOURCE_LANGUAGE)
        self.assertEqual(loc.tr("TestContext", "Zoeken"), "Zoeken")

    def test_applying_the_same_language_twice_reports_no_change(self):
        self.compile_translation()
        self.assertTrue(self.translator.apply(preference="en", locale_name="nl_NL"))
        self.assertFalse(self.translator.apply(preference="en", locale_name="nl_NL"))

    def test_unload_restores_the_source_language(self):
        self.compile_translation()
        self.translator.apply(preference="en", locale_name="nl_NL")
        self.translator.unload()
        self.assertEqual(loc.current_language(), loc.SOURCE_LANGUAGE)
        self.assertEqual(loc.tr("TestContext", "Zoeken"), "Zoeken")


if __name__ == "__main__":
    unittest.main()
