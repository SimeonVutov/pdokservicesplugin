# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PdokServicesPlugin - localization.pdok_metadata
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

English names for the services and layers PDOK publishes.

PDOK serves Dutch only: asking its APIs for another language is either ignored
or rejected, so these names come from a curated resource file instead of from
the network. Resolution order is official PDOK English, then curated, then the
Dutch original; a missing translation is normal and simply leaves the Dutch
name standing on its own.

The resource is kept apart from resources/layers-pdok.json because that file is
regenerated wholesale by the ngr-services-spider script.
"""
import json
import logging
import os
import re

from .. import LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)

TRANSLATIONS_DIRNAME = os.path.join("resources", "translations")

#: Field a catalogue entry would carry if PDOK ever published English titles.
OFFICIAL_TITLE_FIELDS = ("title_en",)
OFFICIAL_SERVICE_TITLE_FIELDS = ("service_title_en",)

_TRAILING_CODE = re.compile(r"\s*\(([^()]*)\)\s*$")
_cache = {}


def normalize(text):
    """Fold a PDOK title to a lookup key: 'Waterdeel_vlak' -> 'waterdeel vlak'."""
    return re.sub(r"[\s_]+", " ", (text or "").strip().lower())


class PdokMetadataTranslations:
    """Curated English names, looked up by normalized Dutch title."""

    def __init__(self, titles=None, bases=None, suffixes=None, service_titles=None):
        self.titles = {normalize(k): v for k, v in (titles or {}).items()}
        self.bases = {normalize(k): v for k, v in (bases or {}).items()}
        self.suffixes = {normalize(k): v for k, v in (suffixes or {}).items()}
        self.service_titles = {
            normalize(k): v for k, v in (service_titles or {}).items()
        }
        # Longest first so that 'labelpoint' wins over 'label'.
        self._suffix_order = sorted(self.suffixes, key=len, reverse=True)

    def __bool__(self):
        return bool(self.titles or self.bases or self.service_titles)

    def title(self, source_title):
        """English name for a layer title, or None to keep the Dutch original."""
        if not source_title:
            return None
        text = str(source_title).strip()
        # An official abbreviation such as '(BTD)' is part of the name and is
        # carried across untranslated.
        code = ""
        match = _TRAILING_CODE.search(text)
        if match:
            code = f" ({match.group(1)})"
            text = text[: match.start()].strip()
        translated = self._lookup(text)
        return None if translated is None else f"{translated}{code}"

    def service_title(self, source_title):
        """English name for a service/product title, or None."""
        if not source_title:
            return None
        return self.service_titles.get(normalize(source_title))

    def _lookup(self, text):
        key = normalize(text)
        if not key:
            return None
        if key in self.titles:
            return self.titles[key]
        # A base term is also a valid title on its own ('Pand', 'Wegdeel').
        if key in self.bases:
            return self.bases[key]
        for suffix in self._suffix_order:
            base_key = self._strip_suffix(key, suffix)
            if base_key is None:
                continue
            base = self.titles.get(base_key) or self.bases.get(base_key)
            if base:
                return self.suffixes[suffix].format(base=base)
        return None

    @staticmethod
    def _strip_suffix(key, suffix):
        """PDOK writes these both spaced and glued ('waterdeel vlak', 'hoogtepunt')."""
        if key.endswith(" " + suffix):
            return key[: -len(suffix) - 1].strip()
        if key.endswith(suffix) and len(key) > len(suffix) + 2:
            return key[: -len(suffix)].strip()
        return None


EMPTY = PdokMetadataTranslations()


def resource_path(language, plugin_dir):
    return os.path.join(
        plugin_dir, TRANSLATIONS_DIRNAME, f"pdok_metadata_{language}.json"
    )


def load_translations(language, plugin_dir):
    """Read the curated resource. A missing or broken file yields no
    translations rather than an error, so the plugin keeps working in Dutch."""
    path = resource_path(language, plugin_dir)
    if not os.path.exists(path):
        return EMPTY
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return PdokMetadataTranslations(
            titles=data.get("layer_titles"),
            bases=data.get("layer_title_bases"),
            suffixes=data.get("layer_title_suffixes"),
            service_titles=data.get("service_titles"),
        )
    except Exception as e:
        log.warning(f"ignoring unusable PDOK metadata translations '{path}': {e}")
        return EMPTY


def translations_for(language, plugin_dir):
    """Cached accessor: the resource is read once per language."""
    if not language:
        return EMPTY
    key = (language, plugin_dir)
    if key not in _cache:
        _cache[key] = load_translations(language, plugin_dir)
    return _cache[key]


def clear_cache():
    _cache.clear()


def _official(layer, fields):
    for field in fields:
        value = layer.get(field)
        if value:
            return str(value)
    return None


def translated_title(layer, translations):
    """Official PDOK English if it exists, else the curated name, else None."""
    official = _official(layer, OFFICIAL_TITLE_FIELDS)
    if official:
        return official
    return translations.title(layer.get("title", ""))


def translated_service_title(layer, translations):
    official = _official(layer, OFFICIAL_SERVICE_TITLE_FIELDS)
    if official:
        return official
    return translations.service_title(layer.get("service_title", ""))
