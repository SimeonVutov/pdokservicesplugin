---
title: Manual QGIS test plan
---

# Manual QGIS test plan

The automated suite (`make test`) covers the localization logic without a GUI.
These steps cover what it cannot: the plugin actually running inside QGIS.

## Setup

Create a QGIS profile named `pdokplugin-develop` and symlink the plugin into
it (see the Developers section of the README), then:

```sh
make transcompile        # the .qm must exist before QGIS loads the plugin
qgis --profile pdokplugin-develop
```

Enable the plugin in *Plugins ▸ Manage and Install Plugins*. Keep
*View ▸ Panels ▸ Log Messages* open on the "PDOK services plugin" tab.

Record for each run: QGIS version, Qt version, OS, and the QGIS interface
language (*Settings ▸ Options ▸ General ▸ User interface translation*).

---

## TEST A — English startup

1. Set the QGIS interface language to English and restart QGIS.
2. Open the plugin.

**Expect:** the dialog opens with no errors in the Log Messages panel, and no
Python exception dialog.

## TEST B — Generic interface is English and not bilingual

With the plugin open in English, check:

| Where | Expect |
|---|---|
| Tab names | `PDOK Services`, `PDOK Locatieserver`, `OpenGeoGroep and PDOK`, `Settings` |
| Search label | `Search` |
| Add-layer buttons | `Default`, `Top`, `Bottom` |
| Column headers | `Layer name`, `Type`, `Service` |
| Toolbar search placeholder | `Search PDOK Location Server` |
| Dialog close button | `Close` |
| Right-click a layer | `Add this layer to favourites` |

**Expect:** none of these show Dutch alongside the English — no
`Search (Zoeken)`, no `Cancel (Annuleren)`.

## TEST C — Bilingual PDOK layer names

1. Type `top10nl` in the catalogue search.
2. Look at the *Layer name* column.

**Expect:** official layer names keep their Dutch original, for example:

- `Water area — Waterdeel vlak`
- `Water line — Waterdeel lijn`
- `Road centreline — Wegdeel hartlijn`
- `Terrain area — Terrein vlak`

3. Select `Water area — Waterdeel vlak` and read the information panel.

**Expect:** `English name: Water area`, `Official PDOK name: Waterdeel vlak`
and `Name: waterdeel_vlak` shown as three separate rows.

## TEST D — English search

Search for `road`.

**Expect:** `Road centreline — Wegdeel hartlijn` is among the results.

## TEST E — Dutch search still works in English mode

Search for `wegdeel`.

**Expect:** the same layer appears. Then search `wegdeel_hartlijn` and expect
it again.

## TEST F — Identifier safety

1. Select `Water area — Waterdeel vlak` (the BRT TOP10NL OGC API Features one)
   and add it.
2. Open *Layer ▸ Properties ▸ Information*, or check the layer source.

**Expect:** the source contains `typename='waterdeel_vlak'`. It must **not**
contain `Water area`, and must not contain the `—` separator.

## TEST G — Real vector service

Add a WFS layer and an OGC API Features layer.

**Expect:** both draw, and the attribute table shows the original Dutch field
names (`typewater`, `breedteklasse`) with their original values. Localization
must not have touched the data.

## TEST H — Raster service

Add an AHN layer (WCS) and a WMTS background layer.

**Expect:** both draw normally.

## TEST I — Favourites

1. Right-click two layers and add them to favourites.
2. Close QGIS and reopen it.
3. Use the favourites from the toolbar button menu.

**Expect:** both favourites still resolve and load. Then set the language to
Dutch and check they still load — favourites match on the identifier, not on
the displayed title.

## TEST J — Dutch mode

1. In the plugin, go to *Settings ▸ Language* and choose `Nederlands`.

**Expect, immediately and without restarting QGIS:**

- the interface becomes Dutch (`Zoeken`, `Laagnaam`, `Standaard`);
- layer names become plain Dutch: `Waterdeel vlak`, **not**
  `Waterdeel vlak — Water area`;
- layers already added to the map are renamed to their Dutch names;
- the About tab is Dutch.

2. Switch back to `English` and confirm everything returns to English.
3. Set it to `Automatic (follow QGIS)` and confirm it follows the QGIS
   language.

Also check the **Language** entry in the toolbar button menu does the same.

## TEST K — Missing translation falls back to Dutch

In English, search for a layer with no curated English name, for example
`Landsgrens` or `TOP25raster`.

**Expect:** it is listed with its Dutch name alone, with no separator and no
placeholder text. Selecting it shows no `English name` row.

## TEST L — Unsupported locale

Set the QGIS interface language to something with no translation, e.g. German,
and restart with the plugin language set to `Automatic`.

**Expect:** the plugin falls back to Dutch and works normally. No errors.

## TEST M — Processing algorithms

Open the Processing toolbox in English and find the *PDOK Services Plugin*
provider.

**Expect:** `PDOK Geocoder`, `PDOK Reverse Geocoder` and `PDOK AHN WCS Tool`
under the groups `PDOK Locatieserver` and `AHN`, with English parameter labels.
Switch language and confirm the labels follow.

## TEST N — Locator bar

Type `pdok amsterdam` in the QGIS locator bar.

**Expect:** results appear and zoom correctly when clicked.

## TEST O — Packaging

```sh
make zip
unzip -l repo/pdokservicesplugin.*.zip | grep i18n
```

**Expect:** `pdokservicesplugin/i18n/pdokservicesplugin_en.qm` is present and
the `.ts` is not. Install that zip into a clean QGIS profile and repeat TEST A
and TEST B.
