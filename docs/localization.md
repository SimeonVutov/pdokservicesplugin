---
title: Localization
---

# Localization

Dutch is the source language of this plugin: every literal string in the Python
code and in the Qt Designer file is Dutch, so running in Dutch needs no
translation file at all. Other languages are shipped as compiled Qt
translations.

Two different things get translated, and they are deliberately kept apart:

| | Plugin interface | PDOK terminology |
|---|---|---|
| What | Buttons, menus, messages, Processing labels | Names PDOK publishes for its services and layers |
| Where | `i18n/pdokservicesplugin_<lang>.qm` | `resources/translations/pdok_metadata_<lang>.json` |
| Mechanism | Qt `QTranslator` | Curated lookup table |
| In English | Fully replaced | Shown **next to** the Dutch original |

The reason for the difference is in [text classification](#text-classification):
a button is just a button, but `Waterdeel vlak` is an authoritative name that a
user may need to cite.

## Text classification

Not every visible string is treated the same way.

| Class | Example | Treatment |
|---|---|---|
| 1. Generic interface | `Zoeken`, `Annuleren` | Fully translated: `Search`, `Cancel`. Never bilingual. |
| 2. Dataset / product names | `BAG`, `AHN`, `BRT TOP10NL` | Acronyms unchanged. Long Dutch product names may get a bilingual form, e.g. `CBS Districts and Neighbourhoods — CBS Wijken en Buurten`. |
| 3. Layer / collection names | `Waterdeel vlak` | Bilingual in English: `Water area — Waterdeel vlak`. Plain Dutch in Dutch. |
| 4. Technical identifiers | `waterdeel_vlak`, service URLs, settings keys | **Never** translated. |
| 5. Descriptions | layer `abstract` | May be translated; product names inside stay recognizable. Falls back to Dutch. |
| 6. Schema / attribute names | `typewater`, `breedteklasse` | Not touched. Renaming them would break expressions, joins, saved projects and provider requests. |
| 7. Feature values | `ja`, `overig`, `waterloop` | Not touched. This is source data, not interface text. |

## Locale detection

`localization/locale.py` resolves the language in this order:

1. The plugin's own preference, `/pdokservicesplugin/language`, if it is not
   `auto`.
2. Otherwise the QGIS language: `locale/userLocale` when the user has ticked
   the override in QGIS, and the system locale otherwise.

The result is reduced to a bare language code (`en_GB` → `en`). If that code is
the source language, or there is no translation for it, no translator is
installed and the plugin runs in Dutch. Unsupported locales therefore degrade
quietly rather than failing.

## Switching language at runtime

`PluginTranslator.apply()` swaps the installed `QTranslator`. Because Qt does
not take ownership of a translator, the plugin keeps the reference; losing it
would silently stop translation.

Swapping the translator is not enough on its own — widgets keep the text they
were given. `PdokServicesPlugin.retranslate_ui()` re-applies everything the
plugin owns:

- `retranslateUi()` on the dialog, which re-applies every string from the `.ui`
- strings set from Python: placeholders, action texts, table headers
- the About tab, which is rebuilt from translated paragraphs
- the catalogue rows, re-labelled in place so the selection survives
- favourites in the toolbar menu
- the layer information panel, if a layer is selected
- the Processing registry, so algorithm names are re-read
- layers already added to the project (see below)

### Layers already on the map

When the plugin adds a layer it tags it with custom properties:
`identifier`, `service_md_id` and the `display_title` it used. On a language
change the plugin looks the catalogue entry up again by identifier and renames
the layer. If the name no longer starts with the title the plugin gave it, the
user renamed it by hand and it is left alone.

Note that this only renames the layer. The data itself stays Dutch, and cannot
be otherwise: WMS and WMTS layers are images rendered by PDOK with Dutch labels
baked in, vector tiles carry PDOK's own Dutch style, and WFS / OGC API Features
attributes are source data.

## PDOK terminology

### PDOK has no English to offer

Checked against the live services; none of this is assumed:

| Service | `lang=en` | `Accept-Language: en` | Result |
|---|---|---|---|
| OGC API Features (BRT TOP10NL) | ignored | ignored | Byte-identical Dutch response. No localization conformance class among its 24. |
| WMS GetCapabilities | ignored | ignored | Identical document. No INSPIRE `SupportedLanguages`. |
| WFS GetCapabilities | ignored | — | Identical document. |
| WCS | — | — | No language negotiation. |
| Locatieserver | **HTTP 400** | — | `query parameter 'lang' not defined in the specifications` |

Reproduce with:

```sh
curl -s 'https://api.pdok.nl/kadaster/brt-top10nl/ogc/v1/collections?f=json&lang=en' | md5sum
curl -s 'https://api.pdok.nl/kadaster/brt-top10nl/ogc/v1/collections?f=json'         | md5sum
curl -s -o /dev/null -w '%{http_code}\n' \
  'https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest?q=amsterdam&lang=en'
```

So the plugin **does not** send language parameters to PDOK. Doing it blindly
would not merely be useless, it would break the geocoder. English names come
from a curated local resource instead, and there is no runtime dependency on
any machine-translation service.

### Resolution order

For each layer title:

1. Official English supplied by PDOK — read from a `title_en` field on the
   catalogue entry. PDOK does not publish this today; the hook exists so that
   authoritative English wins automatically if it ever appears.
2. The curated translation.
3. The Dutch original, on its own.

A missing translation is normal and never an error.

### The curated resource

`pdokservicesplugin/resources/translations/pdok_metadata_en.json`. It is kept
out of `resources/layers-pdok.json` on purpose: that catalogue is regenerated
wholesale by `scripts/generate-pdok-layers-config.sh` and would discard
anything added to it.

Lookup keys are normalized — lowercased, with `_` and runs of whitespace folded
to single spaces — so one entry covers `Waterdeel vlak`, `waterdeel_vlak` and
`Waterdeel  Vlak`.

Titles resolve in two tiers:

```
"layer_titles":         { "adres": "Address" }              exact match
"layer_title_bases":    { "waterdeel": "Water" }            + suffix
"layer_title_suffixes": { "vlak": "{base} area" }
```

`Waterdeel vlak` → base `waterdeel` → `Water`, suffix `vlak` → `Water area`.
The longest suffix wins, so `labelpoint` beats `label`. PDOK writes these both
spaced (`Waterdeel vlak`) and glued (`Plaatslabel`); both are handled. A
trailing official abbreviation is carried across untranslated, so
`Begroeid terreindeel (BTD)` becomes `Vegetated terrain (BTD)`.

Composition only happens when **both** halves are known. A half-known compound
produces no translation at all rather than half-English nonsense.

This covers about 63% of catalogue rows from roughly 90 curated terms. The rest
fall back to Dutch, which is correct behaviour, not a gap to be filled with
guesses.

#### Adding a translation

Add the term to `layer_title_bases` if it takes geometry suffixes, or to
`layer_titles` if it stands alone, and run the tests. Only add a term when the
English name is reasonably settled — leaving it out is safe, since the Dutch
original is shown either way.

## Identifier safety

The three concepts are separate values on `LayerLabel`:

```
identifier        waterdeel_vlak                 used in every request
source_title      Waterdeel vlak                 authoritative, always visible
translated_title  Water area                     may be None
display_title     Water area — Waterdeel vlak    presentation only
```

Rules that keep this safe:

- Catalogue entries are only ever read from. Translating never writes to the
  dict that favourites are matched against and requests are built from.
- The identifier is never derived by parsing display text.
- Favourites match on `service_md_id` + `name`, never on a title, so existing
  Dutch favourites keep resolving.

## Search

The catalogue view filters on a hidden column that holds the identifier, the
Dutch title, the translated title and the service titles. So in English,
`road`, `wegdeel` and `wegdeel_hartlijn` all find
`Road centreline — Wegdeel hartlijn`.

## Working with translations

```sh
make transup        # extract strings from .py and .ui into i18n/*.ts
make transcompile   # compile .ts into .qm
make transclean     # remove compiled .qm
make test           # run the test suite
make zip            # package the plugin (compiles .qm first)
```

`make transup` uses `pylupdate6` (or `pylupdate5`), which reads both Python and
`.ui` files in one pass. `make transcompile` uses `lrelease6` (or `lrelease`).
Both are auto-detected; no paths are hard-coded.

Re-running `make transup` preserves existing translations and the `language`
attribute, so it is safe to run at any time.

Both the `.ts` and the `.qm` are committed: the `.ts` is the source a
translator edits, and the `.qm` has to be present in the package. `make zip`
recompiles the `.qm` and excludes the `.ts` from the archive.

### Translation contexts

`QgsProcessingAlgorithm` is **not** a `QObject`, so the algorithms define their
own `tr()`. It must use the class name as context, because that is what
`lupdate` records:

```python
def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)
```

These previously used the context `"Processing"` while `lupdate` wrote the
class name, so their translations never loaded. `tests/test_english_ui.py`
guards against that regression. `QgsProcessingProvider` and `QgsLocatorFilter`
*are* `QObject`s and use `self.tr()` directly.

## Adding a language

1. Add the code to `SUPPORTED_LANGUAGES` in `localization/locale.py`.
2. Add it to `LANGUAGES` in the `Makefile`.
3. Run `make transup`, translate the new `.ts`, run `make transcompile`.
4. Optionally add `resources/translations/pdok_metadata_<lang>.json` for PDOK
   terminology. Without it, PDOK names simply stay Dutch.
5. Add the language's own name to `PdokServicesPlugin.language_choices()`.

No architectural change is needed. Note that in a new language file, the string
`Vertaalde naam` should be translated as *that language's* word for its own
name, the way the English file renders it as "English name".

## Plugin metadata

QGIS `metadata.txt` has no standard per-language fields, and the plugin
repository does not serve localized metadata. So `description` and `about` hold
both languages in one field, with an explicit `English:` section. No
non-standard fields were invented.
