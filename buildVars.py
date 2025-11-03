def _(arg):
    return arg

from datetime import datetime

addon_info = {
    "addon_name": "bible",
    "addon_summary": _("Bible"),
    "addon_description": _("""This is an app designed for convenient exploration of various Bible translations"""),
    "addon_version": datetime.now().strftime("%Y.%m.%d"),
    "addon_author": "Alexandr Halimon<halimon.alexandr@gmail.com>",
    "addon_url": "https://github.com/Halimon-Alexandr/nvda-bible-plugin",
    "addon_sourceURL": "https://github.com/Halimon-Alexandr/nvda-bible-plugin",
    "addon_docFileName": "readme.html",
    "addon_minimumNVDAVersion": "2024.0.0",
    "addon_lastTestedNVDAVersion": "2025.4.0",
    "addon_updateChannel": None,
    "addon_license": "GPL 2",
    "addon_licenseURL": "https://www.gnu.org/licenses/gpl-2.0.html",
}

pythonSources = ["addon/GlobalPlugins/Bible/*.py"]
i18nSources = pythonSources + ["buildVars.py"]
excludedFiles = []
baseLanguage = "en"
markdownExtensions = []
