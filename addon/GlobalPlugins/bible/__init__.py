import globalPluginHandler
import scriptHandler
import wx
import os
import json
import pickle
from .bible_viewer import BibleFrame, FindInBibleDialog, VerseLinkDialog, NotificationDialog, _

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    @scriptHandler.script(
        description=_("Opens the Bible window"),
        gesture="kb:NVDA+x"
    )
    def script_openBibleWindow(self, gesture):
        self.openBibleWindow()

    def openBibleWindow(self):
        self.frame = BibleFrame(None, title="Bible")
        self.frame.Show()
        self.frame.Raise()
