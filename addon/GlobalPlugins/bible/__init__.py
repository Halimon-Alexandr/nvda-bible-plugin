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
        self.on_close_callback = None
    @classmethod

    def setSettings(cls, settings):
        cls.settings = settings

    def onSave(self):
        self.save_settings_logic()

# This code is used in both the NVDA plugin and the desktop app

    def save_settings_logic(self):
        self.settings.set_setting("gemini_api_key", self.api_key_field.GetValue())
        self.settings.set_setting("auto_check_updates", self.auto_check.IsChecked())
        self.settings.save_settings()

    def extract_language(self, translation_name):
        if " - " in translation_name:
            language = translation_name.split(" - ", 1)[0]
            return language
        return "Unknown"

    def makeSettings(self, settingsSizer):
        self.selected_translations = {} 
        self.selected_plans = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        translations_group = wx.StaticBox(self, label=_("Translations Management"))
        translations_sizer = wx.StaticBoxSizer(translations_group, wx.VERTICAL)

        language_label = wx.StaticText(self, label=_("Filter by Language:"))
        translations_sizer.Add(language_label, 0, wx.ALL, 5)

        self.language_filter = wx.Choice(self, choices=[_("All")])
        self.language_filter.SetSelection(0)
        self.language_filter.Bind(wx.EVT_CHOICE, self.on_language_filter_changed)
        translations_sizer.Add(self.language_filter, 0, wx.EXPAND | wx.ALL, 5)

        self.translations_list = wx.CheckListBox(self, choices=[], style=wx.LB_SINGLE)
        translations_sizer.Add(self.translations_list, 1, wx.EXPAND | wx.ALL, 5)

        trans_actions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.action_btn = wx.Button(self, label=_("Action"))
        trans_actions_sizer.Add(self.action_btn, 0, wx.RIGHT, 5)
        translations_sizer.Add(trans_actions_sizer, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        sizer.Add(translations_sizer, 0, wx.EXPAND | wx.ALL, 5)

        plans_group = wx.StaticBox(self, label=_("Reading Plans Management"))
        plans_sizer = wx.StaticBoxSizer(plans_group, wx.VERTICAL)

        self.plans_list = wx.CheckListBox(self, choices=[], style=wx.LB_SINGLE)
        plans_sizer.Add(self.plans_list, 1, wx.EXPAND | wx.ALL, 5)

        plans_actions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.plan_action_btn = wx.Button(self, label=_("Action"))
        self.reset_progress_btn = wx.Button(self, label=_("Reset Progress"))
        self.about_plan_btn = wx.Button(self, label=_("About Plan"))

        plans_actions_sizer.Add(self.plan_action_btn, 0, wx.RIGHT, 5)
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

        self.translations_list.Bind(wx.EVT_CHECKLISTBOX, self.on_translation_checked)
        self.translations_list.Bind(wx.EVT_LISTBOX, self.on_translation_selected)
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_clicked)

        self.plans_list.Bind(wx.EVT_CHECKLISTBOX, self.on_plan_checked)
        self.plans_list.Bind(wx.EVT_LISTBOX, self.on_plan_selected)
        self.plan_action_btn.Bind(wx.EVT_BUTTON, self.on_plan_action_clicked)
        self.reset_progress_btn.Bind(wx.EVT_BUTTON, self.on_reset_progress)
        self.about_plan_btn.Bind(wx.EVT_BUTTON, self.on_about_plan)

        self.refresh_lists()
        self.refresh_plans_list()
        self.Layout()

    def on_language_filter_changed(self, event):
        selected_language = self.language_filter.GetString(self.language_filter.GetSelection())
        self.refresh_lists(selected_language)

    def update_buttons_state(self):
        selected_names = [name for name, sel in self.selected_translations.items() if sel]

        if not selected_names:
            self.action_btn.SetLabel(_("Action"))
            self.action_btn.Disable()
            return

        has_local = any(self.settings.is_translation_local(name) for name in selected_names)
        has_remote = any(not self.settings.is_translation_local(name) for name in selected_names)

        self.action_btn.Enable(True)

        if has_local and has_remote:
            self.action_btn.SetLabel(_("Download/Delete selected"))
        elif has_local:
            self.action_btn.SetLabel(_("Delete selected"))
        else:
            self.action_btn.SetLabel(_("Download selected"))

    def run_download_thread(self, names_list, deleted_list=None):
        count = len(names_list)
        pd = wx.ProgressDialog(
            _("Downloading"),
            _("Starting download..."),
            maximum=count,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        )
        
        def task():
            success_count = 0
            downloaded_successfully = []
            
            for i, name in enumerate(names_list):
                msg = _("Downloading: {name} ({current}/{total})").format(name=name, current=i+1, total=count)
                wx.CallAfter(pd.Update, i, msg)
                
                if self.settings.download_translations_bulk([name]):
                    downloaded_successfully.append(name)
                    success_count += 1
                    self.selected_translations[name] = False
                
                if pd.WasCancelled():
                    break

            def finalize():
                if pd:
                    pd.Destroy()
                
                self.refresh_lists()
                wx.GetApp().Yield() 

                if downloaded_successfully:
                    msg = self._build_result_message(downloaded=downloaded_successfully, deleted=deleted_list)
                    wx.MessageBox(msg, _("Success"), wx.OK | wx.ICON_INFORMATION, parent=self)
                elif not pd.WasCancelled():
                    wx.MessageBox(_("Error during download process."), _("Error"), wx.OK | wx.ICON_ERROR, parent=self)

                wx.CallAfter(self.translations_list.SetFocus)

            wx.CallAfter(finalize)

        threading.Thread(target=task, daemon=True).start()

    def _build_result_message(self, downloaded=None, deleted=None):
        lines = []

        if deleted:
            lines.append(_("Deleted translations: {count}").format(count=len(deleted)))
            for name in deleted:
                lines.append(f"  - {name}")

        if downloaded:
            if lines:
                lines.append("")
            lines.append(_("Downloaded translations: {count}").format(count=len(downloaded)))
            for name in downloaded:
                lines.append(f"  - {name}")

        if not lines:
            return _("No changes were made.")

        return "\n".join(lines)

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
        
        full_string = self.plans_list.GetString(selection)
        name_part = full_string.replace(_("Selected"), "").replace(_("Not selected"), "").strip()
        plan_name = name_part.rsplit(" (", 1)[0].strip()

        description = self.settings.get_plan_description(plan_name)
        
        if description:
            dlg = wx.MessageDialog(
                self,
                description,
                _("About {plan_name}").format(plan_name=plan_name),
                wx.OK | wx.ICON_INFORMATION
            )
            dlg.ShowModal()
            dlg.Destroy()
        else:
            wx.MessageBox(
                _("Failed to load plan description for: {plan_name}").format(plan_name=plan_name),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )

    def on_action_clicked(self, event):
        to_delete = []
        to_download = []
        for name, sel in self.selected_translations.items():
            if sel:
                if self.settings.is_translation_local(name):
                    to_delete.append(name)
                else:
                    to_download.append(name)
        
        if not to_delete and not to_download:
            return
            
        confirm_lines = []
        if to_delete:
            confirm_lines.append(_("Translations to be deleted: {count}").format(count=len(to_delete)))
            for n in to_delete:
                confirm_lines.append(f"  - {n}")
        if to_download:
            if confirm_lines:
                confirm_lines.append("")
            confirm_lines.append(_("Translations to be downloaded: {count}").format(count=len(to_download)))
            for n in to_download:
                confirm_lines.append(f"  - {n}")
        
        msg = "\n".join(confirm_lines)
        dlg = wx.MessageDialog(self, msg, _("Confirm"), wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        
        if result != wx.ID_YES:
            return
            
        if to_delete:
            count = len(to_delete)
            pd_del = wx.ProgressDialog(
                _("Deleting"),
                _("Preparing to delete..."),
                maximum=count,
                parent=self,
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
            )
            for i, name in enumerate(to_delete):
                pd_del.Update(i, _("Deleting: {name}").format(name=name))
                self.settings.delete_local_translation([name])
                self.selected_translations[name] = False
            pd_del.Destroy()
            
        if to_download:
            self.run_download_thread(to_download, deleted_list=to_delete)
        else:
            self.refresh_lists()
            wx.GetApp().Yield()
            self.translations_list.SetFocus()
            msg = self._build_result_message(deleted=to_delete)
            wx.MessageBox(msg, _("Success"), wx.OK | wx.ICON_INFORMATION, parent=self)
            wx.CallAfter(self.translations_list.SetFocus)

    def on_plan_action_clicked(self, event):
        to_delete = []
        to_download = []
        local_plans = self.settings.get_available_plans()
        for name, sel in self.selected_plans.items():
            if sel:
                if name in local_plans:
                    to_delete.append(name)
                else:
                    to_download.append(name)
                    
        if not to_delete and not to_download:
            return
            
        confirm_lines = []
        if to_delete:
            confirm_lines.append(_("Plans to be deleted: {count}").format(count=len(to_delete)))
            for n in to_delete:
                confirm_lines.append(f"  - {n}")
        if to_download:
            if confirm_lines:
                confirm_lines.append("")
            confirm_lines.append(_("Plans to be downloaded: {count}").format(count=len(to_download)))
            for n in to_download:
                confirm_lines.append(f"  - {n}")
                
        dlg = wx.MessageDialog(self, "\n".join(confirm_lines), _("Confirm"), wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        
        if result != wx.ID_YES:
            return
            
        if to_delete:
            count = len(to_delete)
            pd_p_del = wx.ProgressDialog(
                _("Deleting"),
                _("Deleting plans..."),
                maximum=count,
                parent=self,
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
            )
            for i, name in enumerate(to_delete):
                pd_p_del.Update(i, _("Deleting: {name}").format(name=name))
                self.settings.delete_local_plan(name)
                self.selected_plans[name] = False
            pd_p_del.Destroy()
            
        if to_download:
            total_down = len(to_download)
            pd_p_down = wx.ProgressDialog(
                _("Downloading"),
                _("Starting download..."),
                maximum=total_down,
                parent=self,
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
            )
            
            def download_bulk_task():
                success_downloaded = []
                for i, name in enumerate(to_download):
                    msg = _("Downloading: {name} ({current}/{total})").format(name=name, current=i+1, total=total_down)
                    wx.CallAfter(pd_p_down.Update, i, msg)
                    
                    if self.settings.download_reading_plan(name):
                        success_downloaded.append(name)
                        self.selected_plans[name] = False
                    
                    if pd_p_down.WasCancelled():
                        break
                
                def finalize_plans():
                    if pd_p_down:
                        pd_p_down.Destroy()
                    self.refresh_plans_list()
                    wx.GetApp().Yield()
                    self.plans_list.SetFocus()
                    msg = self._build_plan_result_message(downloaded=success_downloaded, deleted=to_delete)
                    wx.MessageBox(msg, _("Success"), wx.OK | wx.ICON_INFORMATION, parent=self)
                    wx.CallAfter(self.plans_list.SetFocus)
                
                wx.CallAfter(finalize_plans)
                
            threading.Thread(target=download_bulk_task, daemon=True).start()
        else:
            self.refresh_plans_list()
            wx.GetApp().Yield()
            self.plans_list.SetFocus()
            msg = self._build_plan_result_message(deleted=to_delete)
            wx.MessageBox(msg, _("Success"), wx.OK | wx.ICON_INFORMATION, parent=self)
            wx.CallAfter(self.plans_list.SetFocus)

    def _build_plan_result_message(self, downloaded=None, deleted=None):
        lines = []

        if deleted:
            lines.append(_("Deleted plans: {count}").format(count=len(deleted)))
            for name in deleted:
                lines.append(f"  - {name}")

        if downloaded:
            if lines:
                lines.append("")
            lines.append(_("Downloaded plans: {count}").format(count=len(downloaded)))
            for name in downloaded:
                lines.append(f"  - {name}")

        if not lines:
            return _("No changes were made.")

        return "\n".join(lines)

    def update_plan_buttons_state(self):
        selected_names = [name for name, sel in self.selected_plans.items() if sel]
        available_local = self.settings.get_available_plans()
        
        if not selected_names:
            self.plan_action_btn.SetLabel(_("Action"))
            self.plan_action_btn.Disable()
        else:
            has_local = any(name in available_local for name in selected_names)
            has_remote = any(name not in available_local for name in selected_names)
            
            self.plan_action_btn.Enable(True)
            if has_local and has_remote:
                self.plan_action_btn.SetLabel(_("Download/Delete selected"))
            elif has_local:
                self.plan_action_btn.SetLabel(_("Delete selected"))
            else:
                self.plan_action_btn.SetLabel(_("Download selected"))

        selection = self.plans_list.GetSelection()
        if selection == wx.NOT_FOUND:
            self.reset_progress_btn.Disable()
            self.about_plan_btn.Disable()
        else:
            full_string = self.plans_list.GetString(selection)
            name_part = full_string.replace(_("Selected"), "").replace(_("Not selected"), "").strip()
            plan_name = name_part.rsplit(" (", 1)[0].strip()
            
            is_local = plan_name in available_local
            progress = self.settings.get_reading_plan_progress(plan_name)
            
            self.reset_progress_btn.Enable(bool(is_local and progress))
            self.about_plan_btn.Enable(True)

    def on_translation_checked(self, event):
        index = event.GetSelection()
        is_checked = self.translations_list.IsChecked(index)
        full_string = self.translations_list.GetString(index)
        
        translation_name = full_string.rsplit(" (", 1)[0].strip()
        self.selected_translations[translation_name] = is_checked

        status_msg = _("Selected") if is_checked else _("Not selected")
        ui.message(status_msg)
        
        self.update_buttons_state()

    def on_plan_checked(self, event):
        index = event.GetSelection()
        is_checked = self.plans_list.IsChecked(index)
        full_string = self.plans_list.GetString(index)
        
        plan_name = full_string.rsplit(" (", 1)[0].strip()
        self.selected_plans[plan_name] = is_checked
        
        status_msg = _("Selected") if is_checked else _("Not selected")
        ui.message(status_msg)
        
        self.update_plan_buttons_state()

    def on_translation_selected(self, event):
        index = self.translations_list.GetSelection()
        if index != wx.NOT_FOUND:
            is_checked = self.translations_list.IsChecked(index)
            status_msg = _("Selected") if is_checked else _("Not selected")
            ui.message(status_msg)
        self.update_buttons_state()

    def on_plan_selected(self, event):
        index = self.plans_list.GetSelection()
        if index != wx.NOT_FOUND:
            is_checked = self.plans_list.IsChecked(index)
            status_msg = _("Selected") if is_checked else _("Not selected")
            ui.message(status_msg)
        self.update_plan_buttons_state()

    def refresh_lists(self, filter_language=None):
        self.translations = self.settings.get_available_translations()

        available_languages = set()
        for t in self.translations:
            lang = self.extract_language(t)
            available_languages.add(lang)
        
        languages_for_choice = [_("All")] + sorted(list(available_languages))

        if hasattr(self, 'language_filter'):
            current_selection = self.language_filter.GetStringSelection()
            if self.language_filter.GetItems() != languages_for_choice:
                self.language_filter.SetItems(languages_for_choice)
                if current_selection in languages_for_choice:
                    self.language_filter.SetStringSelection(current_selection)
                else:
                    self.language_filter.SetSelection(0)

        if filter_language is None:
            filter_language = self.language_filter.GetStringSelection()

        downloaded = []
        available = []
        
        for t in self.translations:
            lang = self.extract_language(t)
            if filter_language == _("All") or lang == filter_language:
                if self.settings.is_translation_local(t):
                    downloaded.append(t)
                else:
                    available.append(t)
        
        all_filtered = downloaded + available
        display_items = []
        checked_indices = []

        for i, translation in enumerate(all_filtered):
            is_local = self.settings.is_translation_local(translation)
            status = f"({_('Downloaded')})" if is_local else f"({_('Not downloaded')})"
            display_items.append(f"{translation} {status}")
            
            if self.selected_translations.get(translation, False):
                checked_indices.append(i)

        self.translations_list.SetItems(display_items)
        for index in checked_indices:
            self.translations_list.Check(index, True)
        
        self.update_buttons_state()

    def refresh_plans_list(self):
        selected_index = self.plans_list.GetSelection()
        self.local_plans = self.settings.get_available_plans()
        self.github_plans = self.settings.load_available_plans_from_github()

        completed_plans_data = []
        in_progress_plans_data = []
        downloaded_plans_data = []

        for plan in sorted(self.local_plans):
            progress = self.settings.get_reading_plan_progress(plan)
            plan_data = self.settings.get_reading_plan_data(plan)
            
            status_text = _("Downloaded")
            target_list = downloaded_plans_data

            if progress:
                days_count = len(plan_data.get("days", []))
                days_range = range(1, days_count + 1)
                
                is_started = any(
                    progress.get(str(day), {}).get("intro", False) or
                    any(progress.get(str(day), {}).values())
                    for day in days_range
                )
                is_completed = all(
                    progress.get(str(day), {}).get("intro", False) and
                    all(progress.get(str(day), {}).values())
                    for day in days_range
                ) if days_count > 0 else False

                if is_completed:
                    status_text = _("Completed")
                    target_list = completed_plans_data
                elif is_started:
                    status_text = _("In progress")
                    target_list = in_progress_plans_data

            target_list.append((plan, f"{plan} ({status_text})"))

        available_plans_data = []
        for plan in sorted(self.github_plans):
            if plan not in self.local_plans:
                available_plans_data.append((plan, f"{plan} ({_('Not downloaded')})"))

        all_combined_data = completed_plans_data + in_progress_plans_data + downloaded_plans_data + available_plans_data
        
        display_strings = [item[1] for item in all_combined_data]
        self.plans_list.Clear()
        self.plans_list.SetItems(display_strings)

        for i, (plan_name, unused) in enumerate(all_combined_data):
            if self.selected_plans.get(plan_name, False):
                self.plans_list.Check(i, True)

        if selected_index != wx.NOT_FOUND:
            total_items = self.plans_list.GetCount()
            if total_items > 0:
                new_index = min(selected_index, total_items - 1)
                self.plans_list.SetSelection(new_index)
        
        self.update_plan_buttons_state()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Bible")

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.update_manager = UpdateManager(self)
        self.pending_update = None
        self._bible_frame = None
        self.cache_timer = wx.Timer()
        self.cache_timer.Bind(wx.EVT_TIMER, self.on_clear_cache_timer)

        BibleSettingsPanel.setSettings(Settings())
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(BibleSettingsPanel)
        
        if Settings().get_setting("auto_check_updates", True) and not globalVars.appArgs.secure:
            threading.Thread(target=self.check_for_updates_wrapper).start()

    def check_for_updates_wrapper(self):
        def update_callback(version, download_url, release_notes):
            self.pending_update = (version, download_url, release_notes)
        self.update_manager.check_for_updates(is_start=True, callback=update_callback)

    def on_clear_cache_timer(self, event):
        Settings().clear_bible_cache()
        if self.cache_timer.IsRunning():
            self.cache_timer.Stop()

    def open_settings_dialog(self):
        dlg = gui.settingsDialogs.NVDASettingsDialog(gui.mainFrame, BibleSettingsPanel)
        dlg.Show()
        dlg.Raise()
        dlg.SetFocus()

    def openBibleWindow(self):
        if self.cache_timer.IsRunning():
            self.cache_timer.Stop()

        if self._bible_frame:
            try:
                if self._bible_frame.IsShown():
                    self._bible_frame.Raise()
                    return
                else:
                    self._bible_frame.Show()
                    self._bible_frame.Raise()
                    return
            except wx.PyDeadObjectError:
                self._bible_frame = None

        threading.Thread(target=play_sound, args=("startup.wav",)).start()
        self._bible_frame = BibleFrame(None, title=_("Bible"), settings=Settings())
        self._bible_frame.Bind(wx.EVT_CLOSE, self.on_bible_frame_close)
        self._bible_frame.Show()
        self._bible_frame.Raise()

    def on_bible_frame_close(self, event):
        self.cache_timer.Start(600000, oneShot=True)
        event.Skip()

    def startBibleApplication(self):
        has_translations = False
        if os.path.exists(TRANSLATIONS_PATH):
            try:
                for item in os.listdir(TRANSLATIONS_PATH):
                    if os.path.isdir(os.path.join(TRANSLATIONS_PATH, item)):
                        has_translations = True
                        break
            except OSError:
                has_translations = False

        if not has_translations:
            message = _(
                "No Bible translations installed.\n"
                "Please download at least one translation in settings."
            )
            
            wx.CallAfter(
                gui.messageBox,
                message,
                _("Bible"),
                wx.OK | wx.ICON_INFORMATION
            )
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