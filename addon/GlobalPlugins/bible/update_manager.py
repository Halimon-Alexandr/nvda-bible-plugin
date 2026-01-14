import addonHandler
import requests
import json
import threading
import wx
import gui
import ui
import globalVars
import os
import core
import winsound
import time

addonHandler.initTranslation()

class UpdateManager:
    def __init__(self, plugin_instance):
        self.plugin_instance = plugin_instance
        self.pending_update = None

    def check_for_updates(self, is_start=False, callback=None):
        try:
            current_addon = addonHandler.getCodeAddon()
            current_version = current_addon.manifest["version"]
            current_version_int = int(current_version.replace(".", ""))

            response = requests.get(
                "https://api.github.com/repos/Halimon-Alexandr/nvda-bible-plugin/releases/latest",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            tag_name = data['tag_name']
            last_version_str = tag_name.lstrip('v')
            last_version_int = int(last_version_str.replace(".", ""))
            release_notes = data.get('body', _("No release notes available."))

            download_url = None
            for asset in data['assets']:
                if asset['name'].endswith('.nvda-addon'):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                if not is_start:
                    wx.CallAfter(gui.messageBox,
                                _("Could not find addon file in release"),
                                _("Update Error"), wx.OK | wx.ICON_ERROR)
                return

            if last_version_int > current_version_int:
                if callback:
                    callback(last_version_str, download_url, release_notes)
                else:
                    wx.CallAfter(self.show_update_dialog, last_version_str, download_url, release_notes)
            elif not is_start:
                wx.CallAfter(gui.messageBox,
                            _("No updates available"),
                            _("Bible Plugin Update"), wx.OK | wx.ICON_INFORMATION)
        except requests.exceptions.RequestException as e:
            if not is_start:
                wx.CallAfter(gui.messageBox,
                            _("Update check failed: ") + str(e),
                            _("Update Error"), wx.OK | wx.ICON_ERROR)

    def prompt_restart_dialog(self):
        def on_response():
            dlg = wx.MessageDialog(
                None,
                _("Changes have been made to the add-ons. To apply them, NVDA must be restarted. Would you like to restart it now?"),
                _("Restart NVDA"),
                wx.YES_NO | wx.ICON_QUESTION
            )
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                core.restart()
        wx.CallAfter(on_response)

    def play_beep_loop(self, stop_event):
        while not stop_event.is_set():
            winsound.Beep(500, 100)
            time.sleep(1)

    def download_and_install(self, version, download_url):
        stop_beep = threading.Event()
        beep_thread = threading.Thread(target=self.play_beep_loop, args=(stop_beep,))
        beep_thread.start()
        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            addon_data = response.content

            temp_path = os.path.join(globalVars.appArgs.configPath, "bible_update.nvda-addon")
            with open(temp_path, "wb") as f:
                f.write(addon_data)

            cur_addon = addonHandler.getCodeAddon()
            bundle = addonHandler.AddonBundle(temp_path)
            if cur_addon:
                cur_addon.requestRemove()
            addonHandler.installAddonBundle(bundle)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            stop_beep.set()
            wx.CallAfter(self.prompt_restart_dialog)
        except requests.exceptions.RequestException as e:
            stop_beep.set()
            wx.CallAfter(
                gui.messageBox,
                _("Failed to install update: ") + str(e),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )

    def show_update_dialog(self, version, download_url, release_notes=None):
        dlg = UpdateDialog(gui.mainFrame, version, download_url, self.plugin_instance, release_notes)
        dlg.ShowModal()

class UpdateDialog(wx.Dialog):
    def __init__(self, parent, version, download_url, plugin_instance, release_notes=None):
        title = _("Bible update")
        super().__init__(parent, title=title, size=(500, 400))
        self.version = version
        self.download_url = download_url
        self.plugin_instance = plugin_instance

        if release_notes:
            self.release_notes = f"{_('Version:')} {version}\n\n{_('What is new:')}\n{release_notes}"
        else:
            self.release_notes = f"{_('Version:')} {version}\n\n{_('What is new:')}\n{_('No release notes available.')}"

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        text = wx.StaticText(
            self,
            label=_("A new version is available! Would you like to update?")
        )
        main_sizer.Add(text, 0, wx.ALL, 10)

        notes_text = wx.TextCtrl(
            self,
            value=self.release_notes,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL,
            size=(-1, 150)
        )
        main_sizer.Add(notes_text, 0, wx.ALL | wx.EXPAND, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_yes = wx.Button(self, wx.ID_YES, label=_("Yes, update"))
        self.btn_no = wx.Button(self, wx.ID_NO, label=_("No, not now"))
        btn_sizer.Add(self.btn_yes, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_no, 0, wx.LEFT, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)
        self.Centre()
        self.Show()
        self.Raise()
        self.SetFocus()
        self.btn_yes.Bind(wx.EVT_BUTTON, self.on_yes)
        self.btn_no.Bind(wx.EVT_BUTTON, self.on_no)

    def on_yes(self, event):
        self.Destroy()
        threading.Thread(
            target=self.plugin_instance.update_manager.download_and_install,
            args=(self.version, self.download_url)
        ).start()
        wx.CallLater(100, ui.message, _("Please wait, application update in progress."))

    def on_no(self, event):
        self.Destroy()
        self.plugin_instance.openBibleWindow()
