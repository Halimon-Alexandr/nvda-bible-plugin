import addonHandler
import os
import globalPluginHandler
import scriptHandler
import wx
import ui
import gui
import globalVars
import threading
import winsound
from gui.settingsDialogs import SettingsPanel
from .bible_viewer import BibleTab, BibleFrame, SearchInBibleDialog, ReferenceDialog, ParallelReferencesDialog, ReadingPlanPanel, HelpDialog, SearchOnPageDialog
from .settings import Settings
from .update_manager import UpdateManager

addonHandler.initTranslation()
plugin_dir = os.path.dirname(__file__)
user_config_dir = globalVars.appArgs.configPath
TRANSLATIONS_PATH = os.path.join(user_config_dir, "bibleData/translations")

def play_sound(sound_file):
    sound_path = os.path.join(plugin_dir, 'Sounds', sound_file)
    if os.path.exists(sound_path):
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

class BibleSettingsPanel(SettingsPanel):
    title = _("Bible")
    settings = None

    def __init__(self, parent):
        super(BibleSettingsPanel, self).__init__(parent)
        self.settings = Settings()
        self.refresh_lists()
        self.refresh_plans_list()

    @classmethod
    def setSettings(cls, settings):
        cls.settings = settings

    def makeSettings(self, settingsSizer):
        sizer = wx.BoxSizer(wx.VERTICAL)

        translations_group = wx.StaticBox(self, label=_("Translations Management"))
        translations_sizer = wx.StaticBoxSizer(translations_group, wx.VERTICAL)
        self.translations = self.settings.get_available_translations()
        self.translations_list = wx.ListBox(self, choices=self.translations, style=wx.LB_SINGLE)
        translations_sizer.Add(self.translations_list, 1, wx.EXPAND | wx.ALL, 5)
        actions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.download_btn = wx.Button(self, label=_("Download"))
        self.delete_btn = wx.Button(self, label=_("Delete"))
        actions_sizer.Add(self.download_btn, 0, wx.RIGHT, 5)
        actions_sizer.Add(self.delete_btn, 0, wx.RIGHT, 5)
        translations_sizer.Add(actions_sizer, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(translations_sizer, 0, wx.EXPAND | wx.ALL, 5)

        plans_group = wx.StaticBox(self, label=_("Reading Plans Management"))
        plans_sizer = wx.StaticBoxSizer(plans_group, wx.VERTICAL)
        self.plans_list = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        plans_sizer.Add(self.plans_list, 1, wx.EXPAND | wx.ALL, 5)

        plans_actions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.download_plan_btn = wx.Button(self, label=_("Download"))
        self.delete_plan_btn = wx.Button(self, label=_("Delete"))
        self.reset_progress_btn = wx.Button(self, label=_("Reset Progress"))
        self.about_plan_btn = wx.Button(self, label=_("About Plan"))
        plans_actions_sizer.Add(self.download_plan_btn, 0, wx.RIGHT, 5)
        plans_actions_sizer.Add(self.delete_plan_btn, 0, wx.RIGHT, 5)
        plans_actions_sizer.Add(self.reset_progress_btn, 0, wx.RIGHT, 5)
        plans_actions_sizer.Add(self.about_plan_btn, 0, wx.RIGHT, 5)
        plans_sizer.Add(plans_actions_sizer, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(plans_sizer, 0, wx.EXPAND | wx.ALL, 5)

        api_group = wx.StaticBox(self, label=_("Enter your Gemini API key to enable intelligent search:"))
        api_sizer = wx.StaticBoxSizer(api_group, wx.VERTICAL)
        self.api_key_label = wx.StaticText(self, label=_("Gemini API key:"))
        current_api_key = self.settings.get_setting("gemini_api_key") or ""
        self.api_key_field = wx.TextCtrl(self, value=current_api_key)
        api_sizer.Add(self.api_key_label, 0, wx.ALL, 5)
        api_sizer.Add(self.api_key_field, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(api_sizer, 0, wx.EXPAND | wx.ALL, 5)

        updates_group = wx.StaticBox(self)
        updates_sizer = wx.StaticBoxSizer(updates_group, wx.VERTICAL)
        self.auto_check = wx.CheckBox(self, label=_("Automatically check for updates on startup"))
        auto_check_val = self.settings.get_setting("auto_check_updates", True)
        self.auto_check.SetValue(auto_check_val)
        updates_sizer.Add(self.auto_check, 0, wx.ALL, 5)
        sizer.Add(updates_sizer, 0, wx.EXPAND | wx.ALL, 5)

        settingsSizer.Add(sizer, 1, wx.EXPAND)

        self.translations_list.Bind(wx.EVT_LISTBOX, self.on_translation_selected)
        self.download_btn.Bind(wx.EVT_BUTTON, self.on_download)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)

        self.plans_list.Bind(wx.EVT_LISTBOX, self.on_plan_selected)
        self.download_plan_btn.Bind(wx.EVT_BUTTON, self.on_download_plan)
        self.delete_plan_btn.Bind(wx.EVT_BUTTON, self.on_delete_plan)
        self.reset_progress_btn.Bind(wx.EVT_BUTTON, self.on_reset_progress)
        self.about_plan_btn.Bind(wx.EVT_BUTTON, self.on_about_plan)

        self.update_buttons_state()
        self.update_plan_buttons_state()
        self.refresh_plans_list()
        self.Layout()

    def on_translation_selected(self, event):
        selection = self.translations_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        translation_with_status = self.translations_list.GetString(selection)
        translation_name = translation_with_status.rsplit(" (", 1)[0]
        self.update_buttons_state()

    def update_buttons_state(self):
        selection = self.translations_list.GetSelection()
        if selection == wx.NOT_FOUND:
            self.download_btn.Disable()
            self.delete_btn.Disable()
            return
        translation_with_status = self.translations_list.GetString(selection)
        translation_name = translation_with_status.rsplit(" (", 1)[0]
        is_local = self.settings.is_translation_local(translation_name)
        is_on_github = self.settings.is_translation_on_github(translation_name)

        if is_local:
            self.delete_btn.Enable()
            self.download_btn.Disable()
        else:
            self.delete_btn.Disable()
            if is_on_github:
                self.download_btn.Enable()
            else:
                self.download_btn.Disable()

    def on_delete(self, event):
        selection = self.translations_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        translation_with_status = self.translations_list.GetString(selection)
        translation_name = translation_with_status.rsplit(" (", 1)[0]
        dlg = wx.MessageDialog(
            self,
            _("Are you sure you want to delete {translation_name}?").format(translation_name=translation_name),
            _("Confirm"),
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            if self.settings.delete_local_translation(translation_name):
                wx.MessageBox(
                    _("{translation_name} successfully deleted!").format(translation_name=translation_name),
                    _("Success"),
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh_lists()
            else:
                wx.MessageBox(
                    _("Failed to delete {translation_name}").format(translation_name=translation_name),
                    _("Error"),
                    wx.OK | wx.ICON_ERROR
                )
        dlg.Destroy()
        wx.CallAfter(self.translations_list.SetFocus)

    def on_download(self, event):
        selection = self.translations_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        translation_with_status = self.translations_list.GetString(selection)
        translation_name = translation_with_status.rsplit(" (", 1)[0]
        dlg = wx.MessageDialog(
            self,
            _("Do you want to download {translation_name}?").format(translation_name=translation_name),
            _("Confirm"),
            wx.YES_NO | wx.ICON_QUESTION
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()
        wx.CallLater(200, ui.message, _("Downloading {translation_name}").format(translation_name=translation_name))

        def download_task():
            success = self.settings.download_translation(translation_name)
            if success:
                wx.CallAfter(self._show_success_message, translation_name)
            else:
                wx.CallAfter(self._show_error_message, translation_name)
        wx.CallAfter(self.translations_list.SetFocus)
        threading.Thread(target=download_task, daemon=True).start()

    def _show_success_message(self, translation_name):
        self.refresh_lists()
        wx.MessageBox(
            _("{translation_name} successfully downloaded!").format(translation_name=translation_name),
            _("Success"),
            wx.OK | wx.ICON_INFORMATION,
            self
        )

    def _show_error_message(self, translation_name):
        wx.MessageBox(
            _("Failed to download {translation_name}").format(translation_name=translation_name),
            _("Error"),
            wx.OK | wx.ICON_ERROR,
            self
        )

    def refresh_lists(self):
        selected_index = self.translations_list.GetSelection()
        self.translations = self.settings.get_available_translations()
        downloaded_translations = []
        available_translations = []
        for translation in self.translations:
            if self.settings.is_translation_local(translation):
                downloaded_translations.append(f"{translation} ({_('Downloaded')})")
            else:
                available_translations.append(f"{translation} ({_('Not downloaded')})")
        self.translations_list.SetItems(downloaded_translations + available_translations)
        if selected_index != wx.NOT_FOUND:
            total_items = self.translations_list.GetCount()
            if total_items > 0:
                new_index = min(selected_index, total_items - 1)
                self.translations_list.SetSelection(new_index)

    def on_plan_selected(self, event):
        self.update_plan_buttons_state()

    def update_plan_buttons_state(self):
        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            self.download_plan_btn.Disable()
            self.delete_plan_btn.Disable()
            self.reset_progress_btn.Disable()
            self.about_plan_btn.Disable()
            return

        plan_with_status = self.plans_list.GetString(selection)
        plan_name = plan_with_status.rsplit(" (", 1)[0]
        is_local = plan_name in self.settings.get_available_plans()
        progress = self.settings.get_reading_plan_progress(plan_name)

        if is_local:
            self.delete_plan_btn.Enable()
            self.reset_progress_btn.Enable(progress is not None)
            self.download_plan_btn.Disable()
        else:
            self.delete_plan_btn.Disable()
            self.reset_progress_btn.Disable()
            self.download_plan_btn.Enable()
        self.about_plan_btn.Enable()

    def on_download_plan(self, event):
        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        plan_with_status = self.plans_list.GetString(selection)
        plan_name = plan_with_status.rsplit(" (", 1)[0]
        dlg = wx.MessageDialog(
            self,
            _("Are you sure you want to download {plan_name}?").format(plan_name=plan_name),
            _("Confirm"),
            wx.YES_NO | wx.ICON_QUESTION
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()
        wx.CallLater(200, ui.message, _("Downloading {plan_name}").format(plan_name=plan_name))

        def download_task():
            success = self.settings.download_reading_plan(plan_name)
            if success:
                wx.CallAfter(self._show_plan_success_message, plan_name)
                wx.CallAfter(self.refresh_plans_list)
            else:
                wx.CallAfter(self._show_plan_error_message, plan_name)
        wx.CallAfter(self.plans_list.SetFocus)
        threading.Thread(target=download_task, daemon=True).start()

    def on_delete_plan(self, event):
        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        plan_with_status = self.plans_list.GetString(selection)
        plan_name = plan_with_status.rsplit(" (", 1)[0]
        dlg = wx.MessageDialog(
            self,
            _("Are you sure you want to delete {plan_name}?").format(plan_name=plan_name),
            _("Confirm"),
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            if self.settings.delete_local_plan(plan_name):
                wx.MessageBox(
                    _("{plan_name} successfully deleted!").format(plan_name=plan_name),
                    _("Success"),
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh_plans_list()
            else:
                wx.MessageBox(
                    _("Failed to delete {plan_name}").format(plan_name=plan_name),
                    _("Error"),
                    wx.OK | wx.ICON_ERROR
                )
        dlg.Destroy()
        wx.CallAfter(self.plans_list.SetFocus)

    def on_reset_progress(self, event):
        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        plan_with_status = self.plans_list.GetString(selection)
        plan_name = plan_with_status.rsplit(" (", 1)[0]

        dlg = wx.MessageDialog(
            self,
            _("Are you sure you want to reset the progress for {plan_name}?").format(plan_name=plan_name),
            _("Confirm"),
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.settings.remove_reading_plan_progress(plan_name)
            self.refresh_plans_list()
            wx.MessageBox(
                _("Progress for {plan_name} has been reset!").format(plan_name=plan_name),
                _("Success"),
                wx.OK | wx.ICON_INFORMATION
            )
        dlg.Destroy()
        wx.CallAfter(self.plans_list.SetFocus)

    def on_about_plan(self, event):
        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        plan_with_status = self.plans_list.GetString(selection)
        plan_name = plan_with_status.rsplit(" (", 1)[0]
        description = self.settings.get_plan_description(plan_name)
        if description:
            dlg = wx.MessageDialog(
                self,
                description,
                _("About {plan_name}").format(plan_name=plan_name),
                wx.OK | wx.ICON_INFORMATION
            )
            dlg.ShowModal()
        else:
            wx.MessageBox(
                _("Failed to load plan description!"),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )

    def _show_plan_success_message(self, plan_name):
        self.refresh_plans_list()
        wx.MessageBox(
            _("{plan_name} successfully downloaded!").format(plan_name=plan_name),
            _("Success"),
            wx.OK | wx.ICON_INFORMATION,
            self
        )

    def _show_plan_error_message(self, plan_name):
        wx.MessageBox(
            _("Failed to download {plan_name}").format(plan_name=plan_name),
            _("Error"),
            wx.OK | wx.ICON_ERROR,
            self
        )

    def refresh_plans_list(self):
        selected_index = self.plans_list.GetSelection()
        self.local_plans = self.settings.get_available_plans()
        self.github_plans = self.settings.load_available_plans_from_github()

        completed_plans = []
        in_progress_plans = []
        downloaded_plans = []

        for plan in sorted(self.local_plans):
            progress = self.settings.get_reading_plan_progress(plan)
            plan_data = self.settings.get_reading_plan_data(plan)

            if progress:
                is_started = any(
                    progress.get(str(day), {}).get("intro", False) or
                    any(progress.get(str(day), {}).values())
                    for day in range(1, len(plan_data.get("days", [])) + 1)
                )
                is_completed = all(
                    progress.get(str(day), {}).get("intro", False) and
                    all(progress.get(str(day), {}).values())
                    for day in range(1, len(plan_data.get("days", [])) + 1)
                )

                if is_completed:
                    completed_plans.append(f"{plan} ({_('Completed')})")
                elif is_started:
                    in_progress_plans.append(f"{plan} ({_('In progress')})")
                else:
                    downloaded_plans.append(f"{plan} ({_('Downloaded')})")
            else:
                downloaded_plans.append(f"{plan} ({_('Downloaded')})")

        available_plans = []
        for plan in sorted(self.github_plans):
            if plan not in self.local_plans:
                available_plans.append(f"{plan} ({_('Not downloaded')})")

        self.plans_list.SetItems(
            completed_plans + in_progress_plans + downloaded_plans + available_plans
        )

        if selected_index != wx.NOT_FOUND:
            total_items = self.plans_list.GetCount()
            if total_items > 0:
                new_index = min(selected_index, total_items - 1)
                self.plans_list.SetSelection(new_index)

    def onSave(self):
        self.settings.set_setting("gemini_api_key", self.api_key_field.GetValue())
        self.settings.set_setting("auto_check_updates", self.auto_check.IsChecked())
        self.settings.save_settings()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Bible")

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.update_manager = UpdateManager(self)
        self.pending_update = None
        self._bible_frame = None
        BibleSettingsPanel.setSettings(Settings())
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(BibleSettingsPanel)
        if Settings().get_setting("auto_check_updates", True) and not globalVars.appArgs.secure:
            threading.Thread(target=self.check_for_updates_wrapper).start()

    def check_for_updates_wrapper(self):
        def update_callback(version, download_url, release_notes):
            self.pending_update = (version, download_url, release_notes)
        self.update_manager.check_for_updates(is_start=True, callback=update_callback)

    def open_settings_dialog(self):
        dlg = gui.settingsDialogs.NVDASettingsDialog(gui.mainFrame, BibleSettingsPanel)
        dlg.Show()
        dlg.Raise()
        dlg.SetFocus()

    def openBibleWindow(self):
        if self._bible_frame and self._bible_frame.IsShown():
            self._bible_frame.Raise()
            return
        if self._bible_frame and not self._bible_frame.IsShown():
            self._bible_frame.Show()
            self._bible_frame.Raise()
            return
        threading.Thread(target=play_sound, args=("startup.wav",)).start()
        self._bible_frame = BibleFrame(None, title=_("Bible"), settings=Settings())
        self._bible_frame.Show()
        self._bible_frame.Raise()

    def startBibleApplication(self):
        if not os.path.exists(TRANSLATIONS_PATH) or not os.listdir(TRANSLATIONS_PATH):
            self.open_settings_dialog()
        else:
            if self.pending_update:
                version, url, release_notes = self.pending_update
                wx.CallAfter(self.update_manager.show_update_dialog, version, url, release_notes)
                self.pending_update = None
            else:
                self.openBibleWindow()

    @scriptHandler.script(
        description=_("Open the Bible window"),
        gesture="kb:NVDA+x"
    )
    def script_openBibleWindow(self, gesture):
        self.startBibleApplication()
