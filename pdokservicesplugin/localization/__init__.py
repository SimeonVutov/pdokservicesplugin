# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PdokServicesPlugin - localization
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

Translates plugin-owned interface text through Qt. Dutch is the source
language, so it needs no translation file of its own.
"""
from .locale import (
    AUTO,
    LANGUAGE_SETTING_KEY,
    SOURCE_LANGUAGE,
    SUPPORTED_LANGUAGES,
    PluginTranslator,
    current_language,
    is_source_language,
    language_from_locale,
    qgis_locale_name,
    read_language_preference,
    resolve_language,
    select_language,
    translation_file,
    tr,
    write_language_preference,
)

__all__ = [
    "AUTO",
    "LANGUAGE_SETTING_KEY",
    "PluginTranslator",
    "SOURCE_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "current_language",
    "is_source_language",
    "language_from_locale",
    "qgis_locale_name",
    "read_language_preference",
    "resolve_language",
    "select_language",
    "tr",
    "translation_file",
    "write_language_preference",
]
