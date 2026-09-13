# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PdokServicesPlugin - localization.locale
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

Dutch is the source language: running in Dutch needs no translation file.
Every other language ships as i18n/pdokservicesplugin_<language>.qm, so adding
a language means adding a .ts/.qm pair and listing its code in
SUPPORTED_LANGUAGES.
"""
import logging
import os

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator

from .. import LOGGER_NAME
from ..lib.constants import SETTINGS_SECTIONS

log = logging.getLogger(LOGGER_NAME)

SOURCE_LANGUAGE = "nl"
SUPPORTED_LANGUAGES = ("en",)

#: Preference value meaning "follow whatever language QGIS itself runs in".
AUTO = "auto"

LANGUAGE_SETTING_KEY = f"{SETTINGS_SECTIONS}language"

I18N_DIRNAME = "i18n"
TRANSLATION_PREFIX = "pdokservicesplugin"

_active_language = SOURCE_LANGUAGE


def language_from_locale(locale_name):
    """Reduce 'en_GB', 'en-GB', 'en_GB.UTF-8' and friends to 'en'."""
    if not locale_name:
        return ""
    language = str(locale_name).strip()
    for separator in (".", "@", "_", "-"):
        language = language.split(separator)[0]
    return language.strip().lower()


def select_language(locale_name, available=None):
    """Language to use for a locale; None means run in the source language."""
    if available is None:
        available = SUPPORTED_LANGUAGES
    language = language_from_locale(locale_name)
    if not language or language == SOURCE_LANGUAGE:
        return None
    return language if language in available else None


def resolve_language(preference, locale_name, available=None):
    """Language to use for a stored preference; None means source language."""
    if preference and preference != AUTO:
        return select_language(preference, available)
    return select_language(locale_name, available)


def qgis_locale_name():
    """The locale QGIS itself is running in."""
    from qgis.core import QgsSettings

    settings = QgsSettings()
    # QGIS only honours its own locale setting when the user overrode the
    # system one.
    if settings.value("locale/overrideFlag", False, type=bool):
        user_locale = settings.value("locale/userLocale", "")
        if user_locale:
            return str(user_locale)
    return QLocale.system().name()


def read_language_preference():
    from qgis.core import QgsSettings

    return str(QgsSettings().value(LANGUAGE_SETTING_KEY, AUTO) or AUTO)


def write_language_preference(preference):
    from qgis.core import QgsSettings

    QgsSettings().setValue(LANGUAGE_SETTING_KEY, preference)


def translation_file(language, plugin_dir):
    """Path of the compiled translation, or None when none is installed."""
    if not language:
        return None
    path = os.path.join(plugin_dir, I18N_DIRNAME, f"{TRANSLATION_PREFIX}_{language}.qm")
    return path if os.path.exists(path) else None


def current_language():
    """Language code the plugin is currently presenting itself in."""
    return _active_language


def is_source_language():
    return _active_language == SOURCE_LANGUAGE


def tr(context, text):
    """Translate text in a named context.

    The main plugin class is a plain object, not a QObject, so it has no
    self.tr.
    """
    return QCoreApplication.translate(context, text)


class PluginTranslator:
    """Owns the installed QTranslator and swaps it when the language changes.

    Qt does not take ownership of a translator, so the reference held here is
    what keeps it alive.
    """

    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self._translator = None

    @property
    def language(self):
        return _active_language

    def apply(self, preference=None, locale_name=None):
        """Install the translation for a preference. Returns True if the
        language changed. Never raises: any failure falls back to Dutch."""
        global _active_language
        try:
            if preference is None:
                preference = read_language_preference()
            if locale_name is None:
                locale_name = qgis_locale_name()
            language = resolve_language(preference, locale_name)
        except Exception as e:
            log.warning(f"could not determine language, using Dutch: {e}")
            language = None

        if language == _active_language or (
            language is None and _active_language == SOURCE_LANGUAGE
        ):
            return False

        self._uninstall()
        if language is None:
            _active_language = SOURCE_LANGUAGE
            return True
        if self._install(language):
            _active_language = language
        else:
            _active_language = SOURCE_LANGUAGE
        return True

    def _install(self, language):
        try:
            path = translation_file(language, self.plugin_dir)
            if path is None:
                log.debug(f"no translation shipped for '{language}'")
                return False
            translator = QTranslator()
            if not translator.load(path):
                log.warning(f"could not load '{path}'")
                return False
            if not QCoreApplication.installTranslator(translator):
                log.warning(f"could not install translator for '{language}'")
                return False
            self._translator = translator
            return True
        except Exception as e:
            log.warning(f"localization disabled, falling back to Dutch: {e}")
            return False

    def _uninstall(self):
        if self._translator is None:
            return
        try:
            QCoreApplication.removeTranslator(self._translator)
        except Exception as e:
            log.debug(f"ignorable issue while removing translator: {e}")
        self._translator = None

    def unload(self):
        global _active_language
        self._uninstall()
        _active_language = SOURCE_LANGUAGE
