# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PdokServicesPlugin - localization.labels
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

Keeps three things apart that are easy to confuse: the identifier PDOK expects
in a request (never translated), the Dutch title PDOK publishes (authoritative,
stays visible), and a translation of that title (may be missing).
"""

BILINGUAL_SEPARATOR = " — "


def bilingual(translated, source):
    """Combine a translation with its original, or return the original alone."""
    if not source:
        return translated or ""
    if not translated:
        return source
    if translated.strip().casefold() == source.strip().casefold():
        return source
    return f"{translated}{BILINGUAL_SEPARATOR}{source}"


class LayerLabel:
    """The labels belonging to one entry of the PDOK layer catalogue."""

    __slots__ = (
        "identifier",
        "source_title",
        "translated_title",
        "source_service_title",
        "translated_service_title",
    )

    def __init__(
        self,
        identifier,
        source_title,
        translated_title=None,
        source_service_title="",
        translated_service_title=None,
    ):
        self.identifier = identifier
        self.source_title = source_title
        self.translated_title = translated_title
        self.source_service_title = source_service_title
        self.translated_service_title = translated_service_title

    @property
    def display_title(self) -> str:
        return bilingual(self.translated_title, self.source_title)

    @property
    def display_service_title(self) -> str:
        return bilingual(self.translated_service_title, self.source_service_title)

    @property
    def is_translated(self) -> bool:
        return bool(self.translated_title) and (
            self.translated_title.strip().casefold()
            != (self.source_title or "").strip().casefold()
        )

    def __repr__(self):
        return (
            f"LayerLabel(identifier={self.identifier!r}, "
            f"source_title={self.source_title!r}, "
            f"translated_title={self.translated_title!r})"
        )


def label_for_layer(layer, translated_title=None, translated_service_title=None):
    """Build a LayerLabel from a raw layers-pdok.json entry, which is only read
    from: favourites are matched against that dict and requests are built from
    it, so it must not be modified."""
    return LayerLabel(
        identifier=layer.get("name", ""),
        source_title=layer.get("title", ""),
        translated_title=translated_title,
        source_service_title=layer.get("service_title", "") or "",
        translated_service_title=translated_service_title,
    )
