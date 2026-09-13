# -*- coding: utf-8 -*-
"""Drive the plugin inside a real QgsApplication.

Run as a subprocess by tests/test_plugin_integration.py, because a QGIS
application has to be the only one in its process. Exits non-zero on failure.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMainWindow, QToolBar


class StubIface:
    """The little of QgisInterface the plugin touches while starting up."""

    def __init__(self):
        self._window = QMainWindow()
        self._canvas = None

    def mainWindow(self):
        return self._window

    def registerLocatorFilter(self, _filter):
        pass

    def deregisterLocatorFilter(self, _filter):
        pass

    def addToolBar(self, name):
        return QToolBar(name, self._window)

    def addPluginToMenu(self, _menu, _action):
        pass

    def removePluginMenu(self, _menu, _action):
        pass

    def mapCanvas(self):
        from qgis.gui import QgsMapCanvas

        if self._canvas is None:
            self._canvas = QgsMapCanvas()
        return self._canvas


IDENTIFIER = "waterdeel_vlak"
SERVICE_TYPE = "api features"
failures = []


def check(label, condition, detail=""):
    if not condition:
        failures.append(f"{label}: {detail}")
    print(f"{'ok  ' if condition else 'FAIL'} {label} {detail}")


def find_row(plugin, identifier):
    for row in range(plugin.sourceModel.rowCount()):
        entry = plugin.sourceModel.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if entry and entry.get("name") == identifier and entry.get("service_type") == SERVICE_TYPE:
            return entry, plugin.sourceModel.item(row, 0).text(), plugin.sourceModel.item(row, 3).text()
    return None, None, None


def main():
    app = QgsApplication([], True)
    app.initQgis()

    from pdokservicesplugin.pdokservicesplugin import PdokServicesPlugin

    plugin = PdokServicesPlugin(StubIface())
    plugin.initGui()
    check("catalogue loaded", plugin.sourceModel.rowCount() > 1000, f"rows={plugin.sourceModel.rowCount()}")

    # --- Dutch -----------------------------------------------------------
    plugin.set_language_preference("nl")
    entry, name, haystack = find_row(plugin, IDENTIFIER)
    check("dutch language active", plugin.translator.language == "nl", plugin.translator.language)
    check("dutch layer name", name == "Waterdeel vlak", repr(name))
    check("dutch ui", plugin.dlg.tabWidget.tabText(3) == "Instellingen", plugin.dlg.tabWidget.tabText(3))
    check("dutch search", "waterdeel" in haystack.lower())
    check("dutch mode is not bilingual", "—" not in name, repr(name))

    # --- English ---------------------------------------------------------
    plugin.set_language_preference("en")
    entry, name, haystack = find_row(plugin, IDENTIFIER)
    check("english language active", plugin.translator.language == "en", plugin.translator.language)
    check("bilingual layer name", name == "Water area — Waterdeel vlak", repr(name))
    check("english ui", plugin.dlg.tabWidget.tabText(3) == "Settings", plugin.dlg.tabWidget.tabText(3))
    check("english header", plugin.sourceModel.headerData(0, Qt.Orientation.Horizontal) == "Layer name")
    for query in ("water area", "waterdeel", IDENTIFIER):
        check(f"search {query!r}", query in haystack.lower())

    # --- identifier safety on a real layer -------------------------------
    plugin.current_layer = entry
    layer = plugin.create_new_layer()
    plugin.tag_pdok_layer(layer, entry)
    QgsProject.instance().addMapLayer(layer, False)
    check("layer named bilingually", layer.name() == "Water area — Waterdeel vlak", repr(layer.name()))
    check("uri uses identifier", f"typename='{IDENTIFIER}'" in layer.source())
    check("uri has no display text", "Water area" not in layer.source() and "—" not in layer.source())

    # --- switching relabels the added layer, repeatedly -------------------
    for language, expected in (("nl", "Waterdeel vlak"), ("en", "Water area — Waterdeel vlak")) * 2:
        plugin.set_language_preference(language)
        check(f"relabel to {language}", layer.name() == expected, repr(layer.name()))
        check(f"uri intact after {language}", f"typename='{IDENTIFIER}'" in layer.source())

    # --- favourites still match on the identifier ------------------------
    plugin.save_fav_layer_in_settings(entry)
    check("favourite resolves in english", plugin.get_layer_in_pdok_layers(entry) is not None)
    plugin.set_language_preference("nl")
    check("favourite resolves in dutch", plugin.get_layer_in_pdok_layers(entry) is not None)
    plugin.delete_fav_layer_in_settings(entry)

    plugin.unload()
    app.exitQgis()

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("\nall startup checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
