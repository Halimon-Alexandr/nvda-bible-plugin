import addonHandler
import os
import globalPluginHandler
import scriptHandler
import wx
import gui
from gui.settingsDialogs import SettingsPanel
from .bible_viewer import BibleFrame, FindInBibleDialog, VerseLinkDialog, ParallelReferencesDialog
from .settings import Settings

addonHandler.initTranslation()

plugin_dir = os.path.dirname(__file__)
setting = Settings()

class BibleSettingsPanel(SettingsPanel):
    title = _("Bible")
    settings = None

    def __init__(self, parent):
        super(BibleSettingsPanel, self).__init__(parent)
        self.translations = self.load_available_translations()

    @classmethod
    def setSettings(cls, settings):
        cls.settings = settings

    def load_available_translations(self):
        translations_path = os.path.join(plugin_dir, 'translations')

        if not os.path.exists(translations_path):
            return []

        translations = [d for d in os.listdir(translations_path) if os.path.isdir(os.path.join(translations_path, d))]
        return translations

    def makeSettings(self, settingsSizer):
        sizer = wx.BoxSizer(wx.VERTICAL)

        translations_group = wx.StaticBox(self, label=_("Select the translations you want to use in the Bible:"))
        translations_sizer = wx.StaticBoxSizer(translations_group, wx.VERTICAL)

        self.translations = self.load_available_translations()
        self.translations_list = wx.ListBox(self, choices=self.translations, style=wx.LB_MULTIPLE)

        selected_translations = self.settings.get_setting("selected_translations") or []

        selected_indices = [idx for idx, translation in enumerate(self.translations) if translation in selected_translations]
        for idx in selected_indices:
            self.translations_list.Select(idx)

        translations_sizer.Add(self.translations_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(translations_sizer, 0, wx.EXPAND | wx.ALL, 5)

        api_group = wx.StaticBox(self, label=_("Enter your Gemini API key to enable intelligent search:"))
        api_sizer = wx.StaticBoxSizer(api_group, wx.VERTICAL)

        self.api_key_label = wx.StaticText(self, label=_("Gemini API key:"))
        current_api_key = self.settings.get_setting("gemini_api_key") or ""
        self.api_key_field = wx.TextCtrl(self, value=current_api_key)

        api_sizer.Add(self.api_key_label, 0, wx.ALL, 5)
        api_sizer.Add(self.api_key_field, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(api_sizer, 0, wx.EXPAND | wx.ALL, 5)

        settingsSizer.Add(sizer, 1, wx.EXPAND)

        self.translations_list.Refresh()
        self.Layout()

    def onSave(self):
        self.settings.set_setting("gemini_api_key", self.api_key_field.GetValue())

        selected_indices = self.translations_list.GetSelections()
        selected_translations = [self.translations_list.GetString(i) for i in selected_indices]

        self.settings.set_setting("selected_translations", selected_translations)
        self.settings.save_settings()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        global setting
        self.settings = setting

        BibleSettingsPanel.setSettings(self.settings)

        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(BibleSettingsPanel)

    def open_settings_dialog(self):
        dlg = gui.settingsDialogs.NVDASettingsDialog(gui.mainFrame, BibleSettingsPanel)
        dlg.Show()
        dlg.Raise()
        dlg.SetFocus()

    def openBibleWindow(self):
        self.frame = BibleFrame(None, title="Bible", settings=self.settings)
        self.frame.Show()
        self.frame.Raise()

    def startBibleApplication(self):
        selected_translations = self.settings.get_setting("selected_translations", [])

        if not selected_translations:
            self.open_settings_dialog()
        else:
            self.openBibleWindow()

    @scriptHandler.script(
        description=_("Opens the Bible window"),
        gesture="kb:NVDA+x"
    )
    def script_openBibleWindow(self, gesture):
        self.startBibleApplication()

    __gestures = {
        "kb:NVDA+x": "openBibleWindow",
    }
