# PDOK Services Plugin — English localization fork

> **Unofficial English-localization fork.**
> The original *PDOK Services Plugin* was written by Richard Duivenvoorde and
> contributors. Current upstream:
> <https://codeberg.org/rduivenvoorde/pdokservicesplugin>.
> This fork adds English localization and the internationalization work behind
> it. It is **not** affiliated with, endorsed by, or produced by PDOK; "PDOK"
> is a trademark of its owner.

<img src="https://img.shields.io/liberapay/receives/rduivenvoorde.svg?logo=liberapay">

Buy the original author a beer via <https://liberapay.com/rduivenvoorde/>.

## What the plugin does

PDOK (*Publieke Dienstverlening Op de Kaart*) publishes the Dutch national
geo-data as web services. This QGIS plugin lets you search that catalogue and
load a layer with one click, instead of hunting for capabilities URLs.

- A searchable list of every published layer (WMS, WMTS, WFS, WCS, OGC API
  Tiles and Features), all available in the Dutch national CRS EPSG:28992.
- Two favourite layers within reach from the toolbar.
- A layer information panel with metadata links.
- A geocoder (PDOK Locatieserver) in the toolbar, in the dialog and in the QGIS
  locator bar.
- Processing algorithms: geocoder, reverse geocoder and an AHN elevation tool.

## What this fork adds

- **English user interface.** Buttons, menus, dialogs, messages, the Processing
  algorithms and the locator are fully translated. Nothing is shown
  redundantly in two languages.
- **Bilingual PDOK layer names.** In English the catalogue shows
  `Water area — Waterdeel vlak`, so you can read the English meaning *and*
  still cite the authoritative Dutch name in a report. Dutch stays plain Dutch.
- **A language switch.** The plugin follows the QGIS language by default. You
  can override it in *Settings ▸ Language* or from the toolbar button menu, and
  it takes effect immediately — no QGIS restart. Layers already added are
  renamed to match.
- **Search in either language.** `road`, `wegdeel` and `wegdeel_hartlijn` all
  find the same layer.
- **Technical identifiers are never translated.** A layer displayed as
  `Water area — Waterdeel vlak` is still requested as `waterdeel_vlak`, so
  favourites, saved projects and service requests keep working.

Translations of PDOK's own terminology are curated locally, because PDOK serves
Dutch only — see [docs/localization.md](docs/localization.md).

## Install

Download or build a zip and install it in QGIS via
*Plugins ▸ Manage and Install Plugins ▸ Install from ZIP*:

```sh
make zip        # writes repo/pdokservicesplugin.<version>.zip
```

Requires QGIS 3.14 or newer (tested on QGIS 4 with Qt6).

## Usage

1. Open the plugin from the toolbar or *Plugins ▸ PDOK Services Plugin*.
2. Type in the search box to filter the catalogue, e.g. `wfs cbs provincie`.
3. Select a layer to see its details, then **Default**, **Top** or **Bottom**
   to add it to the map.
4. Right-click a layer to add it to your favourites.
5. To change language, go to the **Settings** tab and pick one, or use the
   **Language** entry in the toolbar button menu.

## Developers

Install dev tools with:

```sh
pip3 install -r pdokservicesplugin/requirements/dev.txt
```

Lint and format:

```sh
pylint --errors-only --disable=E0611 pdokservicesplugin
black pdokservicesplugin
```

Run the tests:

```sh
make test
```

Translations (see [docs/localization.md](docs/localization.md) for detail):

```sh
make transup        # extract strings from .py and .ui into i18n/*.ts
make transcompile   # compile .ts into the .qm that ships with the plugin
```

Update the layers config file in
[`pdokservicesplugin/resources/layers-pdok.json`](pdokservicesplugin/resources/layers-pdok.json)
(run from the root of the repo). Note: some layers (specifically
OpenBasisKaart) are added manually, so take care not to delete those. This file
is generated; curated translations live in
`pdokservicesplugin/resources/translations/` and are not affected.

```sh
./scripts/generate-pdok-layers-config.sh pdokservicesplugin/resources/layers-pdok.json
```

Create a symlink to the QGIS plugin directory from the repository directory,
after creating a QGIS profile named `pdokplugin-develop`:

- Windows:

```bat
mklink /d "%APPDATA%\QGIS\QGIS3\profiles\pdokplugin-develop\python\plugins\pdokservicesplugin" "%REPODIR%\pdokservicesplugin"
```

- Linux (Ubuntu), run from the root of the repo:

```sh
symlink_path="$(realpath ~)/.local/share/QGIS/QGIS3/profiles/pdokplugin-develop/python/plugins/pdokservicesplugin"
mkdir -p $(dirname "$symlink_path")
ln -s "$(pwd)/pdokservicesplugin" "$symlink_path"
```

- macOS, run from the root of the repo:

```sh
symlink_path="/Users/$USER/Library/Application Support/QGIS/QGIS3/profiles/pdokplugin-develop/python/plugins/pdokservicesplugin"
mkdir -p $(dirname "$symlink_path")
ln -s "$(pwd)/pdokservicesplugin" "$symlink_path"
```

Optionally: extend the layers config file using OGC:API urls, see
[`scripts/modify-layers-pdok-ogcapi.py`](scripts/modify-layers-pdok-ogcapi.py)
for more detailed instructions.

## Documentation

- [docs/localization.md](docs/localization.md) — how localization works and how
  to maintain or extend it.
- [docs/manual-test-plan.md](docs/manual-test-plan.md) — manual QGIS test plan.
- [docs/index.md](docs/index.md) — the original feature overview (in Dutch).

## License and attribution

This plugin is free software under the **GNU Affero General Public License
v3.0**; see [LICENSE](LICENSE). The fork keeps the upstream license, copyright
headers and author information unchanged.

- Original author: Richard Duivenvoorde (<richard@zuidt.nl>), Zuidt —
  with contributions from Raymond Nijssen, Anton Bakker and others.
- Upstream repository: <https://codeberg.org/rduivenvoorde/pdokservicesplugin>
- Modifications in this fork: see [NOTICE](NOTICE).

The layer catalogue is generated from the
[Nationaal Georegister](https://www.nationaalgeoregister.nl/) with
[PDOK/ngr-services-spider](https://github.com/PDOK/ngr-services-spider). PDOK
data is published under its own licenses, per dataset.
