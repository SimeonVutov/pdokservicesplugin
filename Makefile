PLUGINNAME = pdokservicesplugin

VERSION=$(shell cat pdokservicesplugin/metadata.txt | grep version= | sed -e 's,version=,,')

# Languages shipped besides the Dutch source language. Add a code here and run
# `make transup` to start a new translation.
LANGUAGES = en

I18N_DIR = $(PLUGINNAME)/i18n
TS_FILES = $(foreach lang,$(LANGUAGES),$(I18N_DIR)/$(PLUGINNAME)_$(lang).ts)
QM_FILES = $(TS_FILES:.ts=.qm)

# Qt ships these under different names per distribution and Qt version.
LUPDATE ?= $(shell command -v pylupdate6 || command -v pylupdate5)
LRELEASE ?= $(shell command -v lrelease6 || command -v lrelease-qt6 || command -v lrelease)

.PHONY: zip transup transcompile transclean test

zip: transcompile
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org or install from within QGIS
	#$(CURDIR)/repo$(CURDIR)/repo First remove an maybe already available older zip (with same version number)
	mkdir -p $(CURDIR)/repo
	rm -f $(CURDIR)/repo/$(PLUGINNAME).$(VERSION).zip
	zip -9r $(CURDIR)/repo/$(PLUGINNAME).$(VERSION).zip $(PLUGINNAME) LICENSE -x *.pyc -x *__pycache__* -x *.ts
	@echo Successfully created zip: $(CURDIR)/repo/$(PLUGINNAME).$(VERSION).zip

# Extract translatable strings from the Python and Qt Designer sources into the
# .ts files. Run this after adding or changing a user visible string.
transup:
	@test -n "$(LUPDATE)" || { echo "ERROR: no pylupdate6/pylupdate5 found (install PyQt6 development tools)"; exit 1; }
	@mkdir -p $(I18N_DIR)
	@for ts in $(TS_FILES); do \
		echo "updating $$ts"; \
		$(LUPDATE) $(PLUGINNAME) --exclude '*/i18n/*' -ts $$ts || exit 1; \
	done

transcompile: $(QM_FILES)

$(I18N_DIR)/%.qm: $(I18N_DIR)/%.ts
	@test -n "$(LRELEASE)" || { echo "ERROR: no lrelease6/lrelease found (install the Qt6 tools)"; exit 1; }
	$(LRELEASE) $< -qm $@

transclean:
	rm -f $(I18N_DIR)/*.qm

test:
	python3 -m unittest discover -s tests -t . -v
