import globalVars
import addonHandler
import time
import ui
import wx
import os
import http.client
import winsound
import json
import re
import threading
from threading import Event
from queueHandler import queueFunction, eventQueue
from .settings import Settings

user_config_dir = globalVars.appArgs.configPath
TRANSLATIONS_PATH = os.path.join(user_config_dir, "bibleData/translations")
plugin_dir = os.path.dirname(__file__)
BOOK_ABBREVIATIONS_FILE = os.path.join(plugin_dir, "book_abbreviations.json")

addonHandler.initTranslation()


class BibleTab:
    def __init__(self, settings, initial_state=None):
        self.settings = settings
        self.bible_data = {}
        self.book_mapping = {}
        self.translation_mapping = {}
        self.parallel_refs = {}
        self.is_loaded = False
        self.loading_thread = None
        self.loading_event = threading.Event()

        if initial_state:
            self.state = initial_state
        else:
            self.state = {
                "book_index": 0,
                "chapter_index": 0,
                "verse_number": 1,
                "translation": "",
                "book_name": "",
                "chapter": "",
            }
    
    def save_state(self):
        return self.state.copy()

    def restore_state(self, state):
        self.state = state.copy()


class BibleFrame(wx.Frame):
    def __init__(self, parent, title, settings):
        display_size = wx.DisplaySize()
        width = int(display_size[0] * 0.9)
        height = int(display_size[1] * 0.9)
        style = wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        super(BibleFrame, self).__init__(
            parent, title=title, size=(width, height), style=style
        )
        self.Centre()
        self.settings = settings
        self.tabs = []
        self.current_tab_index = 0
        self.panel = wx.Panel(self)
        self.find_data = wx.FindReplaceData()
        self.find_dialog = None
        control_panel = wx.Panel(self.panel)
        self.book_label = wx.StaticText(control_panel, label=_("Book") + ":")
        self.book_combo = wx.ComboBox(control_panel, style=wx.CB_READONLY)
        self.chapter_label = wx.StaticText(control_panel, label=_("Chapter") + ":")
        self.chapter_combo = wx.ComboBox(control_panel, style=wx.CB_READONLY)
        self.translation_label = wx.StaticText(
            control_panel, label=_("Translation") + ":"
        )
        self.translation_combo = wx.ComboBox(control_panel, style=wx.CB_READONLY)

        self.text_display = wx.TextCtrl(
            self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        control_sizer.Add(self.book_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        control_sizer.Add(self.book_combo, 2, wx.EXPAND | wx.ALL, 5)
        control_sizer.Add(self.chapter_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        control_sizer.Add(self.chapter_combo, 1, wx.EXPAND | wx.ALL, 5)
        control_sizer.Add(
            self.translation_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5
        )
        control_sizer.Add(self.translation_combo, 2, wx.EXPAND | wx.ALL, 5)
        control_panel.SetSizer(control_sizer)

        main_sizer.Add(control_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.text_display, 1, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(main_sizer)

        self.translation_combo.Bind(wx.EVT_COMBOBOX, self.handle_translation_selection)
        self.book_combo.Bind(wx.EVT_COMBOBOX, self.handle_book_selection)
        self.chapter_combo.Bind(wx.EVT_COMBOBOX, self.handle_chapter_selection)
        self.Bind(wx.EVT_CLOSE, self.handle_close_event)
        self.Bind(wx.EVT_CHAR_HOOK, self.handle_key_press)

        self.text_display.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

        self.input_buffer = []
        self.input_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.handle_input_timer, self.input_timer)

        self.load_tabs_states()

        self.refresh_parallel_references()
        self.text_display.SetFocus()
        self.set_font_size()
        self.update_tab_titles()

    @property
    def current_tab(self):
        if self.tabs and 0 <= self.current_tab_index < len(self.tabs):
            return self.tabs[self.current_tab_index]
        return None

    def load_available_translations_for_tab(self, tab):
        if not os.path.exists(TRANSLATIONS_PATH):
            return []
        all_translations = [
            name for name in os.listdir(TRANSLATIONS_PATH)
            if os.path.isdir(os.path.join(TRANSLATIONS_PATH, name))
        ]
        tab.translation_mapping = {
            re.sub(r"^[A-Za-z]+(\s*-\s*)", "", t).strip(): t
            for t in all_translations
        }
        return list(tab.translation_mapping.keys())

    def load_tabs_states(self):
        tabs_states = self.settings.get_setting("tabs_states", [])
        current_tab_index = self.settings.get_setting("current_tab_index", 0)

        if not tabs_states:
            self.create_new_tab()
            return

        for i, tab_state in enumerate(tabs_states):
            new_tab = BibleTab(self.settings, tab_state)
            self.tabs.append(new_tab)

        if current_tab_index < len(self.tabs):
            self.current_tab_index = current_tab_index
        else:
            self.current_tab_index = 0

        current_tab = self.tabs[self.current_tab_index]

        available_translations = self.load_available_translations()
        saved_translation = current_tab.state.get("translation", "")
        if saved_translation and saved_translation in available_translations:
            original_translation = current_tab.translation_mapping.get(saved_translation, saved_translation)
            current_tab.bible_data = self.settings.get_translation_data(original_translation)
            current_tab.parallel_refs = self.settings.get_parallel_references(original_translation)
            current_tab.is_loaded = True
            self.translation_combo.SetValue(saved_translation)
        self.load_current_tab_data()
        if len(tabs_states) > 1:
            self.start_background_tab_loading(current_tab_index)

    def start_background_tab_loading(self, current_tab_index):
        def load_tab_in_thread(tab):
            try:
                available_translations = self.load_available_translations_for_tab(tab)
                translation = tab.state.get("translation", "")
                if translation and available_translations:
                    original_translation = tab.translation_mapping.get(translation, translation)
                    tab.bible_data = self.settings.get_translation_data(original_translation)
                    tab.parallel_refs = self.settings.get_parallel_references(original_translation)
                    tab.is_loaded = True
            except Exception as e:
                print(f"Error loading tab data in thread: {e}")
            finally:
                tab.loading_event.set()
        for i, tab in enumerate(self.tabs):
            if i != current_tab_index:
                thread = threading.Thread(
                    target=load_tab_in_thread, 
                    args=(tab,),
                    daemon=True
                )
                tab.loading_thread = thread
                thread.start()

    def save_tabs_states(self):
        self.update_current_session_settings()
        tabs_states = []
        for tab in self.tabs:
            tabs_states.append(tab.save_state())

        self.settings.set_setting("tabs_states", tabs_states)
        self.settings.set_setting("current_tab_index", self.current_tab_index)
        self.settings.save_settings()

    def create_new_tab(self, initial_state=None):
        current_translation = None
        if self.tabs and 0 <= self.current_tab_index < len(self.tabs):
            current_tab = self.tabs[self.current_tab_index]
            current_translation = current_tab.state.get("translation", "")

        new_tab = BibleTab(self.settings, initial_state)
        self.tabs.append(new_tab)
        self.current_tab_index = len(self.tabs) - 1
        available_translations = self.load_available_translations()

        self.load_current_tab_data()
    
        if initial_state:
            self.apply_tab_state(initial_state)
        else:
            if not current_translation and available_translations:
                current_translation = available_translations[0]

            if current_translation:
                self.translation_combo.SetValue(current_translation)
                self.refresh_translation_comboboxes()
                new_tab.state["translation"] = current_translation

                if self.book_combo.GetCount() > 0:
                    self.book_combo.SetSelection(0)
                    self.refresh_chapter_combobox()
                if self.chapter_combo.GetCount() > 0:
                    self.chapter_combo.SetSelection(0)
                    self.display_chapter_text()

        self.update_current_session_settings()
        self.refresh_parallel_references()
        self.update_tab_titles()

    def close_current_tab(self):
        if len(self.tabs) <= 1:
            self.Close()

            return
        self.update_current_session_settings()
        del self.tabs[self.current_tab_index]
        if self.current_tab_index >= len(self.tabs):
            self.current_tab_index = len(self.tabs) - 1
        self.load_current_tab_data()
        self.update_tab_titles()
        tab_title = self.get_current_tab_title()
        ui.message(tab_title)

    def get_current_tab_title(self):
        if not self.tabs:
            return _("Bible")

        current_tab = self.tabs[self.current_tab_index]
        book_name = current_tab.state.get("book_name", "")
        chapter = current_tab.state.get("chapter", "")
        translation = current_tab.state.get("translation", "")

        if book_name and chapter:
            tab_title = f"{book_name} {chapter}, {translation}"
        else:
            tab_title = _("Bible")
        if len(self.tabs) > 1:
            tab_title += f" [{_('Tab')} {self.current_tab_index + 1} {_('of')} {len(self.tabs)}]"

        return tab_title

    def switch_to_tab(self, index):
        if not self.tabs or len(self.tabs) == 0:
            ui.message(_("No open tabs"))
            return
        if index < 0 or index >= len(self.tabs):
            ui.message(_("Tab with number {tab_number} does not exist.").format(tab_number=index + 1))
            return
        if index == self.current_tab_index:
            ui.message(_("Tab already active."))
            return
        self.current_tab_index = index
        self.load_current_tab_data()
        self.update_current_session_settings()
        self.update_tab_titles()
        self.refresh_parallel_references()
        ui.message(self.get_current_tab_title())

    def switch_to_next_tab(self):
        if len(self.tabs)<=1:
            ui.message(_("No open tabs."))
            return
        next_index = (self.current_tab_index + 1) % len(self.tabs)
        self.switch_to_tab(next_index)

    def switch_to_previous_tab(self):
        if len(self.tabs)<=1:
            ui.message(_("No open tabs."))
            return
        prev_index = (self.current_tab_index - 1) % len(self.tabs)
        self.switch_to_tab(prev_index)

    def update_current_session_settings(self):
        if self.tabs:
            current_tab = self.tabs[self.current_tab_index]
            current_tab.state.update(
                {
                    "book_index": self.book_combo.GetSelection(),
                    "chapter_index": self.chapter_combo.GetSelection(),
                    "verse_number": self.get_current_verse(),
                    "translation": self.translation_combo.GetValue(),
                    "book_name": self.book_combo.GetValue(),
                    "chapter": self.chapter_combo.GetValue(),
                }
            )

    def load_current_tab_data(self):
        if not self.tabs:
            return
        current_tab = self.tabs[self.current_tab_index]
        target_translation = current_tab.state.get("translation", "")
        if target_translation:
            available_translations = self.load_available_translations()
            if target_translation in available_translations:
                original_translation = current_tab.translation_mapping.get(target_translation, target_translation)
                current_tab.bible_data = self.settings.get_translation_data(original_translation)
                current_tab.parallel_refs = self.settings.get_parallel_references(original_translation)
                current_tab.is_loaded = True
            else:
                if available_translations:
                    current_tab.state["translation"] = available_translations[0]
                    original_translation = current_tab.translation_mapping.get(available_translations[0], available_translations[0])
                    current_tab.bible_data = self.settings.get_translation_data(original_translation)
                    current_tab.parallel_refs = self.settings.get_parallel_references(original_translation)
                    current_tab.is_loaded = True
        else:
            available_translations = self.load_available_translations()
            if available_translations:
                current_tab.state["translation"] = available_translations[0]
                original_translation = current_tab.translation_mapping.get(available_translations[0], available_translations[0])
                current_tab.bible_data = self.settings.get_translation_data(original_translation)
                current_tab.parallel_refs = self.settings.get_parallel_references(original_translation)
                current_tab.is_loaded = True
        self.apply_tab_state(current_tab.state)

    def apply_tab_state(self, state):
        if self.translation_combo.GetCount() == 0:
            available_translations = self.load_available_translations()
            if available_translations:
                self.translation_combo.SetItems(available_translations)
        translation = state.get("translation", "")
        if translation and translation in self.translation_combo.GetItems():
            self.translation_combo.SetValue(translation)
        elif self.translation_combo.GetCount() > 0:
            self.translation_combo.SetSelection(0)
            translation = self.translation_combo.GetValue()

        self.refresh_translation_comboboxes()
        book_index = state.get("book_index", 0)
        chapter_index = state.get("chapter_index", 0)
        verse_number = state.get("verse_number", 1)

        if book_index < self.book_combo.GetCount():
            self.book_combo.SetSelection(book_index)
        else:
            self.book_combo.SetSelection(0)

        self.refresh_chapter_combobox()

        if chapter_index < self.chapter_combo.GetCount():
            self.chapter_combo.SetSelection(chapter_index)
        else:
            self.chapter_combo.SetSelection(0)

        self.display_chapter_text()
        self.set_cursor_to_verse_number(verse_number)
        self.update_tab_titles()

    def refresh_translation_comboboxes(self):
        if not self.current_tab:
            return
        if self.translation_combo.GetCount() == 0:
            available_translations = self.load_available_translations()
            if available_translations:
                self.translation_combo.SetItems(available_translations)
                current_value = self.translation_combo.GetValue()
                if not current_value and available_translations:
                    self.translation_combo.SetValue(available_translations[0])
        translation = self.translation_combo.GetValue()

        if translation:
            original_translation = self.current_tab.translation_mapping.get(translation)

            if not original_translation:
                if self.current_tab.translation_mapping:
                    first_key = list(self.current_tab.translation_mapping.keys())[0]
                    original_translation = self.current_tab.translation_mapping[first_key]
                    self.translation_combo.SetValue(first_key)
                    translation = first_key
                else:
                    return
            if original_translation:
                self.load_bible_data_for_translation(original_translation)
                books = self.load_books_from_translation(original_translation)

                if books:
                    self.book_combo.Set(books)
                    self.refresh_translation_options()
                    if self.current_tab and self.current_tab.state.get("book_index", 0) < len(books):
                        book_index = self.current_tab.state.get("book_index", 0)
                        self.book_combo.SetSelection(book_index)
                    self.refresh_chapter_combobox()

    def update_tab_titles(self):
        tab_title = self.get_current_tab_title()
        window_title = f"{_('Bible')} - {tab_title}"
        self.SetTitle(window_title)

    def handle_key_press(self, event):
        key_code = event.GetKeyCode()

        if event.ControlDown():
            if key_code in (ord("T"), ord("t")):
                self.display_reference_dialog(open_in_new_tab=True)
                return
            elif key_code in (ord("W"), ord("w"), wx.WXK_F4):
                self.close_current_tab()
                return
            elif key_code == wx.WXK_TAB:
                if event.ShiftDown():
                    self.switch_to_previous_tab()
                else:
                    self.switch_to_next_tab()
                return
            elif key_code == ord("F"):
                self.display_find_dialog()
                return
            elif key_code == ord("L"):
                self.display_reference_dialog(open_in_new_tab=False)
                return
            elif ord("1") <= key_code <= ord("9"):
                tab_index = key_code - ord("1")
                self.switch_to_tab(tab_index)
                return

        if key_code == wx.WXK_ESCAPE:
            self.Close()
            return

        focused_widget = self.FindFocus()
        if focused_widget == self.text_display:
            if event.ControlDown() and key_code in (
                ord("C"),
                ord("c"),
                ord("B"),
                ord("b"),
                ord("T"),
                ord("t"),
            ):
                event.Skip()
                return

            if key_code >= ord("0") and key_code <= ord("9"):
                self.input_buffer.append(chr(key_code))
                self.input_timer.Start(500, wx.TIMER_ONE_SHOT)
            elif (
                key_code == wx.WXK_NUMPAD_ADD
                or (event.ControlDown() and key_code == ord("+"))
                or key_code == wx.WXK_ADD
            ):
                self.increase_text_font_size()
            elif (
                key_code == wx.WXK_NUMPAD_SUBTRACT
                or (event.ControlDown() and key_code == ord("-"))
                or key_code == wx.WXK_SUBTRACT
            ):
                self.decrease_text_font_size()
            elif event.ControlDown() and key_code == wx.WXK_PAGEUP:
                self.focus_and_speak_verse(verse_offset=-10)
            elif event.ControlDown() and key_code == wx.WXK_PAGEDOWN:
                self.focus_and_speak_verse(verse_offset=10)
            elif key_code == wx.WXK_PAGEUP:
                self.focus_and_speak_verse(verse_offset=-5)
            elif key_code == wx.WXK_PAGEDOWN:
                self.focus_and_speak_verse(verse_offset=5)
            elif event.ShiftDown() and (key_code == ord("C") or key_code == ord("c")):
                self.navigate_to_previous_chapter()
            elif key_code == ord("C") or key_code == ord("c"):
                self.navigate_to_next_chapter()
            elif event.ShiftDown() and (key_code == ord("B") or key_code == ord("b")):
                self.navigate_to_previous_book()
            elif key_code == ord("B") or key_code == ord("b"):
                self.navigate_to_next_book()
            elif event.ShiftDown() and (key_code == ord("T") or key_code == ord("t")):
                self.navigate_to_previous_translation()
            elif key_code == ord("T") or key_code == ord("t"):
                self.navigate_to_next_translation()
            else:
                event.Skip()
        else:
            event.Skip()

    def handle_close_event(self, event):
        self.save_tabs_states()
        self.Destroy()

    def refresh_translation_comboboxes(self):
        if not self.current_tab:
            return

        if self.translation_combo.GetCount() == 0:
            available_translations = self.load_available_translations()
            if available_translations:
                self.translation_combo.SetItems(available_translations)
                if not self.translation_combo.GetValue() and available_translations:
                    self.translation_combo.SetValue(available_translations[0])

        translation = self.translation_combo.GetValue()
        if translation:
            original_translation = self.current_tab.translation_mapping.get(translation)
            if not original_translation:
                if self.current_tab.translation_mapping:
                    first_key = list(self.current_tab.translation_mapping.keys())[0]
                    original_translation = self.current_tab.translation_mapping[first_key]
                    self.translation_combo.SetValue(first_key)
                    translation = first_key
                else:
                    return

            if original_translation:
                self.load_bible_data_for_translation(original_translation)
                books = self.load_books_from_translation(original_translation)
                if books:
                    self.book_combo.Set(books)
                    self.refresh_translation_options()

                    if self.current_tab and self.current_tab.state.get("book_index", 0) < len(books):
                        book_index = self.current_tab.state.get("book_index", 0)
                        self.book_combo.SetSelection(book_index)

                    self.refresh_chapter_combobox()

    def handle_translation_selection(self, event):
        self.saved_book_index = self.book_combo.GetSelection()
        self.saved_chapter_index = self.chapter_combo.GetSelection()
        self.saved_verse_number = self.get_current_verse()

        self.refresh_parallel_references()

        self.refresh_translation_comboboxes()
        self.refresh_translation_options()
        self.set_cursor_to_verse_number(self.saved_verse_number)
        self.update_current_session_settings()
        self.update_tab_titles()

    def get_current_verse_ref(self):
        current_verse = self.get_current_verse()
        if current_verse is None:
            return None

        selected_book_index = self.book_combo.GetSelection()
        if selected_book_index == wx.NOT_FOUND:
            return None

        chapter = self.chapter_combo.GetValue()
        return f"{selected_book_index}.{chapter}.{current_verse}"

    def on_context_menu(self, event):
        verse_ref = self.get_current_verse_ref()
        menu = wx.Menu()

        copy_item = menu.Append(wx.ID_COPY, _("Copy"))
        self.Bind(wx.EVT_MENU, self.on_copy, copy_item)

        menu.AppendSeparator()

        if verse_ref and self.current_tab:
            refs = self.current_tab.parallel_refs.get(verse_ref, [])
            if refs:
                parallel_item = menu.Append(
                    wx.ID_ANY, _("Parallel references") + f" ({len(refs)})"
                )
                self.Bind(
                    wx.EVT_MENU,
                    lambda e: self.show_parallel_references_dialog(verse_ref),
                    parallel_item,
                )
            else:
                no_refs_item = menu.Append(wx.ID_ANY, _("No parallel references"))
                no_refs_item.Enable(False)
        else:
            no_verse_item = menu.Append(wx.ID_ANY, _("No verse selected"))
            no_verse_item.Enable(False)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_copy(self, event):
        start, end = self.text_display.GetSelection()
        selected_text = ""
        reference = ""
        book_name = ""
        chapter = ""
        verse_range = ""

        selected_book_index = self.book_combo.GetSelection()
        if selected_book_index != wx.NOT_FOUND:
            book_name = self.book_combo.GetString(selected_book_index)
            chapter = self.chapter_combo.GetValue()

        if start != end:
            selected_text = self.text_display.GetStringSelection()
            if book_name and chapter:
                verse_numbers = re.findall(r"^\d+", selected_text, re.MULTILINE)
                if verse_numbers:
                    verse_numbers = [int(num) for num in verse_numbers]
                    first_verse = verse_numbers[0]
                    last_verse = verse_numbers[-1]
                    verse_range = (
                        str(first_verse)
                        if first_verse == last_verse
                        else f"{first_verse}-{last_verse}"
                    )
                selected_text = re.sub(
                    r"^\d+\.\s*", "", selected_text, flags=re.MULTILINE
                )
        else:
            current_verse = self.get_current_verse()
            if current_verse:
                books = list(self.current_tab.bible_data.keys())
                if 0 <= selected_book_index < len(books):
                    book_key = books[selected_book_index]
                    chapter_data = self.current_tab.bible_data[book_key].get(
                        chapter, {}
                    )
                    selected_text = chapter_data.get(str(current_verse), "")
                    verse_range = str(current_verse)

        if book_name and chapter and verse_range:
            reference = f"\n\n{book_name} {chapter}:{verse_range}"

        if selected_text:
            full_text = selected_text.strip() + reference
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(full_text))
                wx.TheClipboard.Close()
                ui.message(_("Copied."))

    def show_parallel_references_dialog(self, current_ref):
        if not self.current_tab:
            return
        refs = self.current_tab.parallel_refs.get(current_ref, [])
        valid_refs = [ref for ref in refs if self.is_valid_reference(ref)]
        dialog = ParallelReferencesDialog(
            self, _("Parallel references"), current_ref, valid_refs, self, self.settings
        )
        dialog.ShowModal()

    def load_available_translations(self):
        if not os.path.exists(TRANSLATIONS_PATH):
            return []
        all_translations = [
            name for name in os.listdir(TRANSLATIONS_PATH)
            if os.path.isdir(os.path.join(TRANSLATIONS_PATH, name))
        ]
        if self.current_tab:
            self.current_tab.translation_mapping = {
                re.sub(r"^[A-Za-z]+(\s*-\s*)", "", t).strip(): t
                for t in all_translations
            }
            return list(self.current_tab.translation_mapping.keys())
        else:
            return []

    def is_valid_reference(self, ref):
        if not self.current_tab:
            return False
        bible_data = self.current_tab.bible_data
        parts = ref.split(".")
        if len(parts) < 3:
            return False

        try:
            book_idx = int(parts[0])
            chapter = parts[1]
            verse_part = parts[2]

            books = list(bible_data.keys())
            if book_idx < 0 or book_idx >= len(books):
                return False

            book_key = books[book_idx]
            if chapter not in bible_data.get(book_key, {}):
                return False

            chapter_data = bible_data[book_key][chapter]

            if "-" in verse_part:
                verse_start, verse_end = map(int, verse_part.split("-"))
                return str(verse_start) in chapter_data
            else:
                return verse_part in chapter_data

        except:
            return False

    def get_formatted_verse_text(self, ref, include_verse_number=False):
        if not self.current_tab:
            return ""
        bible_data = self.current_tab.bible_data
        parts = ref.split(".")
        if len(parts) < 3:
            return ""

        try:
            book_idx = int(parts[0])
            chapter = parts[1]
            verse_part = parts[2]

            books = list(bible_data.keys())
            if book_idx < 0 or book_idx >= len(books):
                return ""

            book_key = books[book_idx]
            if chapter not in bible_data[book_key]:
                return ""

            chapter_data = bible_data[book_key][chapter]

            is_range = "-" in verse_part

            if is_range:
                verse_start, verse_end = map(int, verse_part.split("-"))
                verses = []
                for verse_num in range(verse_start, verse_end + 1):
                    verse_str = str(verse_num)
                    if verse_str in chapter_data:
                        verses.append(f"{verse_str}. {chapter_data[verse_str]}")
                return "\n".join(verses)
            else:
                verse_str = verse_part
                if verse_str in chapter_data:
                    if include_verse_number:
                        return f"{verse_str}. {chapter_data[verse_str]}"
                    else:
                        return chapter_data[verse_str]
                return ""

        except Exception as e:
            print(f"Error in get_formatted_verse_text: {e}")
            return ""

    def get_full_chapter_text(self, book_idx, chapter):
        if not self.current_tab:
            return ""
        bible_data = self.current_tab.bible_data
        books = list(bible_data.keys())
        if book_idx < 0 or book_idx >= len(books):
            return ""
        book_key = books[book_idx]
        if chapter not in bible_data[book_key]:
            return ""
        chapter_data = bible_data[book_key][chapter]
        verses = [f"{verse}. {text}" for verse, text in chapter_data.items()]
        return "\n".join(verses)

    def refresh_chapter_combobox(self):
        if not self.current_tab:
            return
        bible_data = self.current_tab.bible_data
        selected_book_index = self.book_combo.GetSelection()
        if selected_book_index != wx.NOT_FOUND:
            selected_book_key = list(bible_data.keys())[selected_book_index]
            chapters = list(bible_data[selected_book_key].keys())
            chapters.sort(key=int)
            self.chapter_combo.Set(chapters)
            if (
                self.current_tab
                and self.current_tab.state.get("chapter_index", 0)
                < self.chapter_combo.GetCount()
            ):
                chapter_index = self.current_tab.state.get("chapter_index", 0)
                self.chapter_combo.SetSelection(chapter_index)
            else:
                self.chapter_combo.SetSelection(0)

            self.display_chapter_text()
            self.update_tab_titles()
        else:
            self.chapter_combo.Set([])
            self.text_display.SetValue(_("Please select a book and chapter."))

    def display_chapter_text(self):
        if not self.current_tab:
            return
        bible_data = self.current_tab.bible_data
        selected_book_index = self.book_combo.GetSelection()
        selected_chapter_index = self.chapter_combo.GetSelection()
        if (
            selected_book_index != wx.NOT_FOUND
            and selected_chapter_index != wx.NOT_FOUND
        ):
            selected_book_key = list(bible_data.keys())[selected_book_index]
            chapters = sorted(bible_data[selected_book_key].keys(), key=int)
            selected_chapter = chapters[selected_chapter_index]
            chapter_data = bible_data.get(selected_book_key, {}).get(
                selected_chapter, {}
            )
            if chapter_data:
                verses = [f"{verse}. {text}" for verse, text in chapter_data.items()]
                full_text = "\n".join(verses)
                self.text_display.SetValue(f"\n{full_text}\n")
                verse_number = (
                    self.current_tab.state.get("verse_number", 1)
                    if self.current_tab
                    else 1
                )

                self.set_cursor_to_verse_number(verse_number)
            else:
                self.text_display.SetValue(_("Text not found."))
        else:
            self.text_display.SetValue(_("Please select a book and chapter."))

    def refresh_translation_options(self):
        if not self.current_tab:
            return
        current_translation = self.translation_combo.GetValue()
        selected_book_index = self.book_combo.GetSelection()

        all_translations = self.load_available_translations()

        current_full_translation = self.current_tab.translation_mapping.get(
            current_translation, current_translation
        )
        current_translation_books_count = (
            len(self.load_books_from_translation(current_full_translation))
            if current_translation
            else 66
        )

        translations = []
        for display_name in all_translations:
            full_name = self.current_tab.translation_mapping[display_name]
            book_count = len(self.load_books_from_translation(full_name))

            if (
                current_translation_books_count == 66
                and selected_book_index != wx.NOT_FOUND
                and selected_book_index < 39
            ):
                if book_count == 66:
                    translations.append(display_name)
            elif current_translation_books_count == 27:
                translations.append(display_name)
            else:
                if book_count >= 27:
                    translations.append(display_name)

        self.translation_combo.Set(translations)

        if current_translation in translations:
            self.translation_combo.SetValue(current_translation)
        else:
            if translations:
                self.translation_combo.SetSelection(0)
            else:
                self.translation_combo.Clear()

    def load_books_from_translation(self, translation):
        if not self.current_tab:
            return []
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        book_files = [
            file
            for file in os.listdir(translation_path)
            if file.endswith(".json") and file != "parallel.json"
        ]
        book_files.sort()
        books = [file.split(". ", 1)[-1].replace(".json", "") for file in book_files]
        self.current_tab.book_mapping = {
            index: book for index, book in enumerate(books)
        }
        return list(self.current_tab.book_mapping.values())

    def load_bible_data_for_translation(self, translation):
        if not self.current_tab:
            return
        self.current_tab.bible_data = self.settings.get_translation_data(translation)

    def refresh_parallel_references(self):
        if not self.current_tab:
            return
        current_translation = self.translation_combo.GetValue()
        if not current_translation:
            self.current_tab.parallel_refs = {}
            return

        original_translation_name = self.current_tab.translation_mapping.get(
            current_translation, current_translation
        )

        self.current_tab.parallel_refs = self.settings.get_parallel_references(
            original_translation_name
        )

    def navigate_to_verse_link(self, book_index, chapter, verse, open_in_main=True):
        if open_in_main:
            if self.current_tab:
                self.current_tab.state.update(
                    {
                        "book_index": book_index,
                        "chapter_index": int(chapter) - 1,
                        "verse_number": int(verse),
                        "translation": self.translation_combo.GetValue(),
                        "book_name": self.book_combo.GetString(book_index),
                        "chapter": str(chapter),
                    }
                )
            self.book_combo.SetSelection(book_index)
            self.refresh_chapter_combobox()
            selected_book_key = list(self.current_tab.bible_data.keys())[book_index]
            chapters = [
                str(ch)
                for ch in sorted(
                    self.current_tab.bible_data[selected_book_key].keys(), key=int
                )
            ]
            chapter_index = chapters.index(str(chapter))
            self.chapter_combo.SetSelection(chapter_index)
            self.display_chapter_text()
            wx.CallAfter(self.set_cursor_to_verse_number, int(verse))
            self.text_display.SetFocus()
        else:
            self.create_new_tab()
            self.current_tab.state.update(
                {
                    "book_index": book_index,
                    "chapter_index": int(chapter) - 1,
                    "verse_number": int(verse),
                    "translation": self.translation_combo.GetValue(),
                    "book_name": self.book_combo.GetString(book_index),
                    "chapter": str(chapter),
                }
            )
            self.book_combo.SetSelection(book_index)
            self.refresh_chapter_combobox()
            selected_book_key = list(self.current_tab.bible_data.keys())[book_index]
            chapters = [
                str(ch)
                for ch in sorted(
                    self.current_tab.bible_data[selected_book_key].keys(), key=int
                )
            ]
            chapter_index = chapters.index(str(chapter))
            self.chapter_combo.SetSelection(chapter_index)
            self.display_chapter_text()
            wx.CallAfter(self.set_cursor_to_verse_number, int(verse))
            self.text_display.SetFocus()

        self.update_tab_titles()

    def handle_book_selection(self, event):
        if not self.current_tab:
            return

        self.refresh_chapter_combobox()

        self.chapter_combo.SetSelection(0)
        self.display_chapter_text()
        self.update_current_session_settings()
        self.update_tab_titles()

    def handle_chapter_selection(self, event):
        if not self.current_tab:
            return

        selected_chapter_index = self.chapter_combo.GetSelection()
        if selected_chapter_index != wx.NOT_FOUND:
            self.current_tab.state["verse_number"] = 1
            self.display_chapter_text()
            self.update_current_session_settings()
            self.update_tab_titles()

    def navigate_to_previous_chapter(self):
        if not self.current_tab:
            return
        selected_book_index = self.book_combo.GetSelection()
        selected_chapter_index = self.chapter_combo.GetSelection()
        if (
            selected_book_index == wx.NOT_FOUND
            or selected_chapter_index == wx.NOT_FOUND
        ):
            return

        selected_book_key = list(self.current_tab.bible_data.keys())[
            selected_book_index
        ]
        chapters = sorted(
            self.current_tab.bible_data[selected_book_key].keys(), key=int
        )

        if selected_chapter_index > 0:
            self.chapter_combo.SetSelection(selected_chapter_index - 1)
        else:
            if selected_book_index > 0:
                previous_book_index = selected_book_index - 1
                self.book_combo.SetSelection(previous_book_index)
                self.refresh_chapter_combobox()

                previous_book_key = list(self.current_tab.bible_data.keys())[
                    previous_book_index
                ]
                previous_chapters = sorted(
                    self.current_tab.bible_data[previous_book_key].keys(), key=int
                )
                last_chapter_index = len(previous_chapters) - 1

                self.chapter_combo.SetSelection(last_chapter_index)
            else:
                self.chapter_combo.SetSelection(0)

        self.display_chapter_text()
        self.set_cursor_to_verse_number(1)
        self.handle_chapter_selection(None)
        current_book_name = self.book_combo.GetString(self.book_combo.GetSelection())
        current_chapter = self.chapter_combo.GetValue()
        ui.message(f"{current_book_name}, {current_chapter}")

    def navigate_to_next_chapter(self):
        if not self.current_tab:
            return
        selected_book_index = self.book_combo.GetSelection()
        selected_chapter_index = self.chapter_combo.GetSelection()
        if (
            selected_book_index == wx.NOT_FOUND
            or selected_chapter_index == wx.NOT_FOUND
        ):
            return

        selected_book_key = list(self.current_tab.bible_data.keys())[
            selected_book_index
        ]
        chapters = sorted(
            self.current_tab.bible_data[selected_book_key].keys(), key=int
        )

        if selected_chapter_index < len(chapters) - 1:
            self.chapter_combo.SetSelection(selected_chapter_index + 1)
        else:
            if selected_book_index < len(self.current_tab.bible_data) - 1:
                next_book_index = selected_book_index + 1
                self.book_combo.SetSelection(next_book_index)
                self.refresh_chapter_combobox()

                self.chapter_combo.SetSelection(0)
            else:
                self.chapter_combo.SetSelection(len(chapters) - 1)

        self.display_chapter_text()
        self.set_cursor_to_verse_number(1)
        self.handle_chapter_selection(None)
        current_book_name = self.book_combo.GetString(self.book_combo.GetSelection())
        current_chapter = self.chapter_combo.GetValue()
        ui.message(f"{current_book_name}, {current_chapter}")

    def navigate_to_next_translation(self):
        if not self.current_tab:
            return
        current_translation = self.translation_combo.GetValue()
        translations = self.translation_combo.GetItems()
        if not translations:
            return
        current_index = (
            translations.index(current_translation)
            if current_translation in translations
            else -1
        )
        next_index = (current_index + 1) % len(translations)
        self.translation_combo.SetSelection(next_index)
        new_translation = translations[next_index]
        self.handle_translation_selection(None)
        ui.message(new_translation)
        self.focus_and_speak_verse()

    def navigate_to_previous_translation(self):
        if not self.current_tab:
            return
        current_translation = self.translation_combo.GetValue()
        translations = self.translation_combo.GetItems()
        if not translations:
            return
        current_index = (
            translations.index(current_translation)
            if current_translation in translations
            else -1
        )
        previous_index = (current_index - 1) % len(translations)
        self.translation_combo.SetSelection(previous_index)
        new_translation = translations[previous_index]
        self.handle_translation_selection(None)
        ui.message(new_translation)
        self.focus_and_speak_verse()

    def navigate_to_next_book(self):
        if not self.current_tab:
            return
        current_book_index = self.book_combo.GetSelection()
        book_count = self.book_combo.GetCount()
        if book_count == 0:
            return
        next_book_index = (current_book_index + 1) % book_count
        self.book_combo.SetSelection(next_book_index)
        new_book_name = self.book_combo.GetString(next_book_index)
        self.handle_book_selection(None)
        ui.message(new_book_name)

    def navigate_to_previous_book(self):
        if not self.current_tab:
            return
        current_book_index = self.book_combo.GetSelection()
        book_count = self.book_combo.GetCount()
        if book_count == 0:
            return
        previous_book_index = (current_book_index - 1) % book_count
        self.book_combo.SetSelection(previous_book_index)
        new_book_name = self.book_combo.GetString(previous_book_index)
        self.handle_book_selection(None)
        ui.message(new_book_name)

    def get_current_verse(self):
        if not self.current_tab:
            return 1
        current_pos = self.text_display.GetInsertionPoint()
        text_value = self.text_display.GetValue()

        verses = []
        for match in re.finditer(r"^(\d+)\.\s", text_value, re.MULTILINE):
            verse_number = int(match.group(1))
            start_pos = match.start()
            adjusted_start_pos = start_pos + verse_number
            verses.append((adjusted_start_pos, verse_number))

        if not verses:
            return 1

        verses.sort(key=lambda x: x[0])

        current_verse = 1
        for pos, verse_number in verses:
            if pos <= current_pos:
                current_verse = verse_number
            else:
                break

        return current_verse

    def set_cursor_to_verse_number(self, verse_number=None, verse_offset=0):
        if verse_number is None:
            verse_number = self.get_current_verse()
        if verse_number is None:
            verse_number = verse_offset
        else:
            verse_number += verse_offset

        verse_pattern = re.compile(rf"^{verse_number}\.\s", re.MULTILINE)
        text_value = self.text_display.GetValue()
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start() + verse_number
            self.text_display.SetInsertionPoint(verse_start)
            self.text_display.ShowPosition(verse_start)

    def focus_and_speak_verse(self, verse_number=None, verse_offset=0):
        if verse_number is None:
            verse_number = self.get_current_verse()
        if verse_number is None:
            verse_number = verse_offset
        else:
            verse_number += verse_offset

        verse_pattern = re.compile(rf"^{verse_number}\.\s", re.MULTILINE)
        text_value = self.text_display.GetValue()
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start()
            line_end = text_value.find("\n", verse_start)
            if line_end == -1:
                line_end = len(text_value)
            self.text_display.SetInsertionPoint(verse_start + verse_number)
            verse_text = text_value[verse_start:line_end].strip()
            ui.message(verse_text)

    def handle_input_timer(self, event):
        verse_number = int("".join(self.input_buffer))
        self.focus_and_speak_verse(verse_number)
        self.input_buffer = []

    def set_font_size(self):
        font = self.text_display.GetFont()
        font.SetPointSize(self.settings.get_setting("font_size"))
        self.text_display.SetFont(font)

    def increase_text_font_size(self):
        self.settings.set_setting(
            "font_size", self.settings.get_setting("font_size") + 1
        )
        ui.message(f"{_('Font size')}: {self.settings.get_setting('font_size')}")
        self.set_font_size()

    def decrease_text_font_size(self):
        if self.settings.get_setting("font_size") > 1:
            self.settings.set_setting(
                "font_size", self.settings.get_setting("font_size") - 1
            )
            ui.message(f"{_('Font size')}: {self.settings.get_setting('font_size')}")
            self.set_font_size()

    def display_find_dialog(self):
        if not self.current_tab:
            return
        self.find_dialog = FindInBibleDialog(
            self,
            _("Search in Bible"),
            self.current_tab.bible_data,
            self.find_data,
            self.settings.get_setting("font_size"),
            self.current_tab.translation_mapping,
        )
        self.find_dialog.Show()

    def display_reference_dialog(self, open_in_new_tab=False):
        if not self.current_tab:
            return
        current_translation = self.translation_combo.GetValue()
        
        dialog_title = _("New Tab") if open_in_new_tab else _("Go to")
        
        dialog = ReferenceDialog(
            self,
            dialog_title,
            self.current_tab.bible_data,
            current_translation,
            self.settings,
            open_in_new_tab=open_in_new_tab,
        )
        if dialog.ShowModal() == wx.ID_OK:
            book_index, chapter, verse, open_in_new_tab = (
                dialog.get_selected_verse_info()
            )
            self.navigate_to_verse_link(
                book_index, chapter, verse, open_in_main=not open_in_new_tab
            )
        dialog.Destroy()


class FindInBibleDialog(wx.Dialog):
    def __init__(
        self, parent, title, bible_data, find_data, font_size, translation_mapping
    ):
        display_size = wx.DisplaySize()
        width = int(display_size[0] * 0.9)
        height = int(display_size[1] * 0.9)
        style = wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title=title, size=(width, height), style=style)
        self.Centre()
        self.current_search_text = ""
        self.bible_data = bible_data
        self.find_data = find_data
        self.parent = parent
        self.settings = parent.settings
        self.search_history = self.settings.get_setting("search_history")
        self.translation_mapping = translation_mapping
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        search_section = wx.StaticBoxSizer(wx.VERTICAL, panel)
        search_grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        search_grid.AddGrowableCol(1, 1)

        search_label = wx.StaticText(panel, label=_("Text for search:"))
        self.text_ctrl = wx.ComboBox(panel, style=wx.TE_PROCESS_ENTER | wx.CB_DROPDOWN)
        self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self.handle_find_button)
        self.text_ctrl.Append(self.search_history)
        search_grid.Add(search_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        search_grid.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        category_label = wx.StaticText(panel, label=_("Category for search:"))
        self.category_combo = wx.ComboBox(
            panel, choices=[_("All books"), _("None")], style=wx.CB_READONLY
        )
        self.category_combo.Bind(wx.EVT_COMBOBOX, self.handle_category_selection)
        search_grid.Add(category_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        search_grid.Add(self.category_combo, 1, wx.EXPAND | wx.ALL, 5)

        books_label = wx.StaticText(panel, label=_("Books for search:"))
        self.books_list = list(self.bible_data.keys())
        self.book_list = wx.ListBox(
            panel, choices=self.books_list, style=wx.LB_MULTIPLE
        )
        self.book_list.SetMinSize((-1, 150))

        for i in range(self.book_list.GetCount()):
            self.book_list.SetSelection(i)

        search_grid.Add(books_label, 0, wx.ALIGN_TOP | wx.ALL, 5)
        search_grid.Add(self.book_list, 1, wx.EXPAND | wx.ALL, 5)

        search_section.Add(search_grid, 1, wx.EXPAND | wx.ALL, 5)

        options_sizer = wx.StaticBoxSizer(wx.VERTICAL, panel)
        options_grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=10)

        self.whole_word_checkbox = wx.CheckBox(panel, label=_("Whole word"))
        self.whole_word_checkbox.SetValue(self.settings.get_setting("whole_word"))
        self.whole_word_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)
        options_grid.Add(self.whole_word_checkbox, 0, wx.ALL, 5)

        self.case_sensitive_checkbox = wx.CheckBox(panel, label=_("Case sensitive"))
        self.case_sensitive_checkbox.SetValue(
            self.settings.get_setting("case_sensitive")
        )
        self.case_sensitive_checkbox.Bind(
            wx.EVT_CHECKBOX, self.handle_search_option_change
        )
        options_grid.Add(self.case_sensitive_checkbox, 0, wx.ALL, 5)

        self.regex_checkbox = wx.CheckBox(panel, label=_("Regular expressions"))
        self.regex_checkbox.SetValue(self.settings.get_setting("use_regex"))
        self.regex_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)
        options_grid.Add(self.regex_checkbox, 0, wx.ALL, 5)

        gemini_api_key = self.settings.get_setting("gemini_api_key")
        if gemini_api_key:
            self.ai_search_checkbox = wx.CheckBox(panel, label=_("AI Search"))
            self.ai_search_checkbox.SetValue(self.settings.get_setting("ai_search"))
            self.ai_search_checkbox.Bind(
                wx.EVT_CHECKBOX, self.handle_search_option_change
            )
            options_grid.Add(self.ai_search_checkbox, 0, wx.ALL, 5)

        options_sizer.Add(options_grid, 0, wx.EXPAND | wx.ALL, 5)

        self.find_button = wx.Button(panel, label=_("Search"))
        self.find_button.Bind(wx.EVT_BUTTON, self.handle_find_button)
        options_sizer.Add(self.find_button, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        results_sizer = wx.BoxSizer(wx.VERTICAL)

        results_label = wx.StaticText(panel, label=_("Search results"))
        results_sizer.Add(results_label, 0, wx.ALL, 5)
        self.results_ctrl = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.TE_RICH2
        )
        self.results_ctrl.Bind(wx.EVT_KEY_DOWN, self.handle_results_key_press)

        self.results_ctrl.SetName(_("Search results content"))

        results_sizer.Add(self.results_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(search_section, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(results_sizer, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        self.text_ctrl.MoveAfterInTabOrder(self.find_button)
        self.category_combo.MoveAfterInTabOrder(self.text_ctrl)
        self.book_list.MoveAfterInTabOrder(self.category_combo)

        self.whole_word_checkbox.MoveAfterInTabOrder(self.book_list)
        self.case_sensitive_checkbox.MoveAfterInTabOrder(self.whole_word_checkbox)
        self.regex_checkbox.MoveAfterInTabOrder(self.case_sensitive_checkbox)

        if gemini_api_key:
            self.ai_search_checkbox.MoveAfterInTabOrder(self.regex_checkbox)
            self.find_button.MoveAfterInTabOrder(self.ai_search_checkbox)
        else:
            self.find_button.MoveAfterInTabOrder(self.regex_checkbox)

        self.results_ctrl.MoveAfterInTabOrder(self.find_button)

        self.text_ctrl.MoveAfterInTabOrder(self.results_ctrl)

        self.Bind(wx.EVT_CHAR_HOOK, self.handle_key_down)
        self.Bind(wx.EVT_CLOSE, self.handle_dialog_close)
        self.text_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.text_ctrl.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
        self.text_ctrl.SetFocus()

        self.apply_font_size(font_size)

        self.book_mapping = {index: book for index, book in enumerate(self.books_list)}
        self.update_category_combo()
        self.category_combo.SetValue(self.settings.get_setting("category_selection"))
        self.handle_category_selection(None)

    def handle_response(self, response):
        if not self.IsShown():
            return

        if hasattr(self, "response_handled") and self.response_handled:
            return
        self.response_handled = True

        formatted_response = (
            self.format_response(response) if response else _("No results found.")
        )

        wx.CallAfter(self.display_verses_from_current_translation, formatted_response)

        if formatted_response == _("No results found."):
            wx.CallAfter(ui.message(("No results found.")))

        self.response_handled = False
        if hasattr(self, "search_performed"):
            self.search_performed = False

    def format_response(self, response):
        try:
            results = (
                response.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if not results:
                return _("No results found.")
            formatted_results = results.replace(". ", ".\n")
            return formatted_results
        except Exception as e:
            return _("Error processing response.")

    def perform_ai_search(self, search_text, selected_books):
        if hasattr(self, "search_performed") and self.search_performed:
            return

        self.search_performed = True
        ui.message(_("Searching, please wait..."))
        current_translation = self.parent.translation_combo.GetValue()
        books_list = ", ".join(selected_books)

        prompt = f"""
        Perform Bible search in {current_translation} translation for query: "{search_text}"
        Strict requirements:
        1. Use ONLY book names from this exact list: {books_list}
        2. Use verse and chapter numbering based only on {current_translation} translation
        3. Response MUST be in a readable format with each verse on a new line, including book name, chapter, verse number, and verse text.
        4. Each line MUST start with the book name, chapter, and verse number, followed by the relevant text.
        5. Book names MUST exactly match the names provided in the list.
        6. The response MUST be in the same language as the query.
        7. Do NOT include any additional commentary or explanations, only the verses.
        8. If possible, return only the verses without any additional text.
    
        Example for {selected_books[0]}:
        Даниїла 9:1 - Першого року Дарія, сина Агасверового, з насіння мідянського, що запанував над царством халдейським,
        Даниїла 9:2 - того року я, Даниїл, зрозумів з книг число літ, про яке було слово Господнє до пророка Єремії, щоб сповнилося сімдесят літ на руїни Єрусалиму.
        """
        thread = threading.Thread(
            target=self.generate_text_with_sound, args=(prompt, self.handle_response)
        )
        thread.start()

    def generate_text_with_sound(self, prompt, callback):
        self.sound_event = Event()

        def sound_indicator():
            while not self.sound_event.is_set() and self.IsShown():
                wx.CallAfter(winsound.Beep, 400, 100)
                time.sleep(1)

        sound_thread = threading.Thread(target=sound_indicator)
        sound_thread.start()

        wx.CallAfter(winsound.Beep, 800, 200)

        try:
            API_KEY = self.settings.get_setting("gemini_api_key")
            conn = http.client.HTTPSConnection(
                "generativelanguage.googleapis.com", timeout=90
            )
            headers = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]})

            conn.request(
                "POST",
                "/v1beta/models/gemini-2.0-flash:generateContent",
                payload,
                headers,
            )
            res = conn.getresponse()
            data = res.read()
            response = json.loads(data.decode("utf-8"))
            wx.CallAfter(callback, response)

        except Exception as e:
            wx.CallAfter(callback, None)

        finally:
            self.sound_event.set()
            sound_thread.join()
            conn.close()

    def display_verses_from_current_translation(self, formatted_results):
        wx.CallAfter(winsound.Beep, 1000, 300)
        try:
            if formatted_results and formatted_results != _("No results found."):
                verse_pattern = re.compile(r"^[А-ЯЇІЄҐа-яїієґ\w\s]+ \d+:\d+ -")
                lines = formatted_results.split("\n")
                verse_lines = [line for line in lines if verse_pattern.match(line)]

                verse_count = len(verse_lines)
                result_text = f"{_('Number of verses found')}: {verse_count}\n\n{formatted_results}"
                self.results_ctrl.SetValue(result_text)
                self.results_ctrl.SetFocus()
            else:
                self.results_ctrl.SetValue(_("No results found."))
        except Exception as e:
            self.results_ctrl.SetValue(_("Error displaying results."))

    def apply_font_size(self, font_size):
        font = self.GetFont()
        font.SetPointSize(font_size)
        self.SetFont(font)
        self.text_ctrl.SetFont(font)
        self.book_list.SetFont(font)
        self.whole_word_checkbox.SetFont(font)
        self.case_sensitive_checkbox.SetFont(font)
        self.regex_checkbox.SetFont(font)

        if hasattr(self, "ai_search_checkbox"):
            self.ai_search_checkbox.SetFont(font)

        self.find_button.SetFont(font)
        self.results_ctrl.SetFont(font)
        self.category_combo.SetFont(font)

    def on_focus(self, event):
        self.text_ctrl.SetValue(self.current_search_text)
        event.Skip()

    def on_kill_focus(self, event):
        self.current_search_text = self.text_ctrl.GetValue()
        event.Skip()

    def handle_find_button(self, event=None):
        search_text = self.text_ctrl.GetValue().strip()
        selected_books = [
            self.book_list.GetString(i) for i in self.book_list.GetSelections()
        ]

        if not search_text:
            ui.message(_("Please enter text to search."))
            return

        if not selected_books:
            ui.message(_("No book selected for search."))
            return

        if search_text not in self.settings.get_setting("search_history"):
            search_history = self.settings.get_setting("search_history")
            search_history.insert(0, search_text)
            self.settings.set_setting("search_history", search_history[:10])
            self.text_ctrl.Clear()
            self.text_ctrl.Append(search_history)

        whole_word = self.settings.get_setting("whole_word")
        case_sensitive = self.settings.get_setting("case_sensitive")
        use_regex = self.settings.get_setting("use_regex")
        ai_search = self.settings.get_setting("ai_search")

        if use_regex:
            try:
                re.compile(search_text)
            except re.error as e:
                ui.message(("Invalid regular expression!"))
                return

        if ai_search:
            result = self.perform_ai_search(search_text, selected_books)
            if result:
                self.results_ctrl.SetValue(result)
                self.results_ctrl.SetFocus()
        else:
            found_verses = []
            for book_name in selected_books:
                chapters = self.bible_data[book_name]
                for chapter_key, verses in chapters.items():
                    for verse_num, verse in verses.items():
                        verse_text = verse.lower() if not case_sensitive else verse
                        search_text_check = (
                            search_text.lower() if not case_sensitive else search_text
                        )
                        if use_regex:
                            if re.search(search_text_check, verse_text):
                                found_verses.append(
                                    f"{book_name} {chapter_key}:{verse_num} - {verse}"
                                )
                        else:
                            if (
                                whole_word and search_text_check in verse_text.split()
                            ) or (not whole_word and search_text_check in verse_text):
                                found_verses.append(
                                    f"{book_name} {chapter_key}:{verse_num} - {verse}"
                                )

            if found_verses:
                result = (
                    f"{_('Number of verses found')}: {len(found_verses)}\n\n"
                    + "\n".join(found_verses)
                    + "\n"
                )
                self.results_ctrl.SetValue(result)
                self.results_ctrl.SetFocus()
            else:
                ui.message(_("No results found."))

    def handle_category_selection(self, event):
        selected_category = self.category_combo.GetValue()
        if selected_category == _("All books"):
            for i in range(self.book_list.GetCount()):
                self.book_list.SetSelection(i)
        elif selected_category == _("None"):
            for i in range(self.book_list.GetCount()):
                self.book_list.Deselect(i)
        elif selected_category == _("Old Testament"):
            for i in range(self.book_list.GetCount()):
                self.book_list.Deselect(i)
            for i in range(39):
                self.book_list.SetSelection(i)
        elif selected_category == _("New Testament"):
            for i in range(self.book_list.GetCount()):
                self.book_list.Deselect(i)
            for i in range(39, 66):
                self.book_list.SetSelection(i)

        self.book_list.SetSelection(0)

        if selected_category in [_("None"), _("New Testament")]:
            self.book_list.Deselect(0)
        else:
            self.book_list.SetSelection(0)

        self.settings.set_setting("category_selection", selected_category)

    def handle_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

    def handle_search_option_change(self, event):
        checkbox = event.GetEventObject()
        if checkbox == self.whole_word_checkbox:
            self.settings.set_setting("whole_word", checkbox.GetValue())
        elif checkbox == self.case_sensitive_checkbox:
            self.settings.set_setting("case_sensitive", checkbox.GetValue())
        elif checkbox == self.regex_checkbox:
            self.settings.set_setting("use_regex", checkbox.GetValue())
        elif (
            hasattr(self, "ai_search_checkbox") and checkbox == self.ai_search_checkbox
        ):
            self.settings.set_setting("ai_search", checkbox.GetValue())

    def handle_dialog_close(self, event):
        self.Destroy()

    def handle_results_key_press(self, event):
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()

        if key_code == wx.WXK_RETURN:
            self.handle_current_verse_info(open_in_new_tab=ctrl_down)
            return

        event.Skip()

    def handle_current_verse_info(self, open_in_new_tab=False):
        current_pos = self.results_ctrl.GetInsertionPoint()
        text_to_cursor = self.results_ctrl.GetRange(0, current_pos)
        lines = text_to_cursor.split("\n")
        current_line = lines[-1]
        text_after_cursor = self.results_ctrl.GetRange(
            current_pos, self.results_ctrl.GetLastPosition()
        )
        full_line = current_line + text_after_cursor.split("\n")[0]

        match = re.match(r"^([\w\' ]+ [^:]+):(\d+(?:-\d+)?) - .*", full_line)
        if match:
            book_chapter, verse_range = match.groups()
            book, chapter = book_chapter.rsplit(" ", 1)
            verse_number = verse_range.split("-")[0]
            book_index = self.get_book_index_by_name(book)

            if book_index is not None:
                if open_in_new_tab:
                    self.parent.update_current_session_settings()
                    self.parent.create_new_tab()

                self.parent.navigate_to_verse_link(
                    book_index, chapter, verse_number, open_in_main=True
                )
                self.Close()
        else:
            if len(lines) > 1:
                previous_line = lines[-2]
                match = re.match(
                    r"^([\w\' ]+ [^:]+):(\d+(?:-\d+)?) - .*", previous_line
                )
                if match:
                    book_chapter, verse_range = match.groups()
                    book, chapter = book_chapter.rsplit(" ", 1)
                    verse_number = verse_range.split("-")[0]
                    book_index = self.get_book_index_by_name(book)

                    if book_index is not None:
                        if open_in_new_tab:
                            self.parent.update_current_session_settings()
                            self.parent.create_new_tab()

                        self.parent.navigate_to_verse_link(
                            book_index, chapter, verse_number, open_in_main=True
                        )
                        self.Close()
                    else:
                        ui.message(_("The cursor is not on a verse."))
                else:
                    ui.message(_("The cursor is not on a verse."))
            else:
                ui.message(_("The cursor is not on a verse."))

    def get_book_index_by_name(self, book_name):
        for index, book in self.book_mapping.items():
            if book == book_name:
                return index
        return None

    def navigate_to_verse_link_in_parent(self, book_index, chapter, verse):
        self.parent.navigate_to_verse_link(book_index, chapter, verse)

    def update_category_combo(self):
        current_translation = self.parent.translation_combo.GetValue()
        current_translation_books_count = (
            len(
                self.parent.load_books_from_translation(
                    self.translation_mapping[current_translation]
                )
            )
            if current_translation
            else 66
        )
        if current_translation_books_count == 66:
            categories = [
                _("All books"),
                _("None"),
                _("Old Testament"),
                _("New Testament"),
            ]
        else:
            categories = [_("All books"), _("None")]
        self.category_combo.Set(categories)


class ParallelReferencesDialog(wx.Dialog):
    def __init__(self, parent, title, current_ref, references, bible_frame, settings):
        display_size = wx.DisplaySize()
        width = int(display_size[0] * 0.9)
        height = int(display_size[1] * 0.5)
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER & ~wx.CLOSE_BOX
        super(ParallelReferencesDialog, self).__init__(
            parent, title=title, size=(width, height), style=style
        )
        self.Centre()
        self.bible_frame = bible_frame
        self.current_ref = current_ref
        self.references = references
        self.current_index = 0
        self.update_window_title()
        self.input_buffer = []
        self.input_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.handle_input_timer, self.input_timer)

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        ref_list_label = wx.StaticText(panel, label=_("Select a reference:"))
        main_sizer.Add(ref_list_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)

        reference_choices = [self.format_short_reference(ref) for ref in references]
        self.reference_combo = wx.ComboBox(
            panel, choices=reference_choices, style=wx.CB_READONLY
        )
        main_sizer.Add(self.reference_combo, 0, wx.EXPAND | wx.ALL, 10)

        self.reference_combo.SetSelection(0)
        self.on_selection_changed(None)

        self.selected_text_display = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        main_sizer.Add(self.selected_text_display, 2, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

        font_size = settings.get_setting("font_size")
        self.set_font_size(font_size)

        self.reference_combo.Bind(wx.EVT_COMBOBOX, self.on_selection_changed)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)
        self.reference_combo.SetFocus()

    def set_font_size(self, font_size):
        font = self.selected_text_display.GetFont()
        font.SetPointSize(font_size)
        self.selected_text_display.SetFont(font)

    def update_window_title(self):
        current_ref_text = self.format_short_reference(self.current_ref)
        self.SetTitle(
            f"{current_ref_text} - {_('Parallel references')} {self.current_index + 1} {_('of')} {len(self.references)}"
        )

    def format_short_reference(self, ref):
        parts = ref.split(".")
        if len(parts) < 3:
            return ref
        try:
            book_idx = int(parts[0])
            chapter = parts[1]
            verse = parts[2]
            if 0 <= book_idx < self.bible_frame.book_combo.GetCount():
                book_name = self.bible_frame.book_combo.GetString(book_idx)
                return f"{book_name} {chapter}:{verse}"
        except:
            pass
        return ref

    def on_selection_changed(self, event):
        if event is None:
            selection = 0
        else:
            selection = event.GetSelection()
        self.current_index = selection
        self.update_window_title()
        wx.CallLater(100, self.update_selected_text_display, self.current_index)

    def update_selected_text_display(self, index):
        if index == -1:
            return
        ref = self.references[index]
        parts = ref.split(".")
        if len(parts) < 3:
            return
        book_idx = int(parts[0])
        chapter = parts[1]
        verse_part = parts[2]

        full_chapter_text = self.bible_frame.get_full_chapter_text(book_idx, chapter)
        if not full_chapter_text:
            return

        self.selected_text_display.SetValue(full_chapter_text)

        verse_text = self.bible_frame.get_formatted_verse_text(
            ref, include_verse_number=True
        )
        if verse_text:
            message_text = re.sub(
                r"^\d+\.\s*", "", verse_text, flags=re.MULTILINE
            ).strip()
            ui.message(message_text)
        self.set_cursor_to_verse(verse_part)

    def set_cursor_to_verse(self, verse_part):
        if "-" in verse_part:
            verse_number = int(verse_part.split("-")[0])
        else:
            verse_number = int(verse_part)

        text_value = self.selected_text_display.GetValue()
        verse_pattern = re.compile(rf"^{verse_number}\.\s", re.MULTILINE)
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start() + len(f"{verse_number}.")
            self.selected_text_display.SetInsertionPoint(verse_start)
            self.selected_text_display.ShowPosition(verse_start)

    def handle_input_timer(self, event):
        if self.input_buffer:
            verse_number = int("".join(self.input_buffer))
            self.focus_and_speak_verse(verse_number)
            self.input_buffer = []

    def focus_and_speak_verse(self, verse_number):
        text_value = self.selected_text_display.GetValue()
        verse_pattern = re.compile(rf"^{verse_number}\.\s", re.MULTILINE)
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start() + len(f"{verse_number}.")
            self.selected_text_display.SetInsertionPoint(verse_start)
            self.selected_text_display.ShowPosition(verse_start)

            verse_text = self.get_verse_text_by_number(verse_number)
            ui.message(verse_text)

    def get_verse_text_by_number(self, verse_number):
        text_value = self.selected_text_display.GetValue()
        verse_pattern = re.compile(
            rf"^{verse_number}\.\s.*?(?=\n\d+\.|\Z)", re.MULTILINE
        )
        match = verse_pattern.search(text_value)
        if match:
            return match.group(0)
        return None

    def get_current_verse(self):
        current_pos = self.selected_text_display.GetInsertionPoint()
        text_value = self.selected_text_display.GetValue()

        verses = []
        for match in re.finditer(r"^(\d+)\.\s", text_value, re.MULTILINE):
            verse_number = int(match.group(1))
            start_pos = match.start()
            verses.append((start_pos, verse_number))

        if not verses:
            return 1

        verses.sort()

        current_verse = 1
        for start_pos, verse_number in verses:
            if current_pos >= start_pos:
                next_index = verses.index((start_pos, verse_number)) + 1
                if next_index < len(verses):
                    next_start_pos, _ = verses[next_index]
                    if current_pos < next_start_pos:
                        current_verse = verse_number
                else:
                    current_verse = verse_number

        return current_verse

    def on_key_press(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.Close()
        elif key_code == wx.WXK_RETURN:
            open_in_new_tab = event.ControlDown()
            self.on_open(open_in_new_tab)
        elif key_code >= ord("0") and key_code <= ord("9"):
            self.input_buffer.append(chr(key_code))
            self.input_timer.Start(500, wx.TIMER_ONE_SHOT)
        elif event.ControlDown() and key_code == wx.WXK_PAGEUP:
            self.focus_and_speak_verse(self.get_current_verse() - 10)
        elif event.ControlDown() and key_code == wx.WXK_PAGEDOWN:
            self.focus_and_speak_verse(self.get_current_verse() + 10)
        elif key_code == wx.WXK_PAGEUP:
            self.focus_and_speak_verse(self.get_current_verse() - 5)
        elif key_code == wx.WXK_PAGEDOWN:
            self.focus_and_speak_verse(self.get_current_verse() + 5)
        else:
            event.Skip()

    def on_open(self, open_in_new_tab=False):
        index = self.reference_combo.GetSelection()
        if index != -1:
            ref = self.references[index]
            parts = ref.split(".")
            if len(parts) >= 3:
                book_index = int(parts[0])
                chapter = parts[1]
                verse = parts[2]
                self.bible_frame.navigate_to_verse_link(
                    book_index=book_index,
                    chapter=chapter,
                    verse=verse,
                    open_in_main=not open_in_new_tab,
                )
        self.Close()


class ReferenceDialog(wx.Dialog):
    def __init__(
        self,
        parent,
        title,
        bible_data,
        current_translation,
        settings,
        open_in_new_tab=False,
    ):
        display_size = wx.DisplaySize()
        width = int(display_size[0] * 0.4)
        height = int(display_size[1] * 0.3)
        style = wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        super(ReferenceDialog, self).__init__(
            parent, title=title, size=(width, height), style=style
        )
        self.Centre()
        self.bible_data = bible_data
        self.current_translation = current_translation
        self.book_abbreviations = self.load_book_abbreviations_mapping()
        self.settings = settings
        self.open_in_new_tab = open_in_new_tab
        self.result = None
        if not self.settings.get_setting("reference_history"):
            self.settings.set_setting("reference_history", [])
        self.reference_history = self.settings.get_setting("reference_history")

        verse_reference_label = wx.StaticText(self, label=_("Enter reference:"))
        self.verse_input = wx.ComboBox(self, style=wx.TE_PROCESS_ENTER | wx.CB_DROPDOWN)
        self.verse_input.Bind(wx.EVT_TEXT_ENTER, self.handle_enter_key)
        self.verse_input.Append(self.reference_history)

        self.default_button = wx.Button(self, label=_("Default"))
        self.default_button.Bind(wx.EVT_BUTTON, self.handle_default_button)

        self.ok_button = wx.Button(self, label=_("Open"))
        self.ok_button.Bind(wx.EVT_BUTTON, self.handle_ok_button)

        self.cancel_button = wx.Button(self, label=_("Cancel"))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.handle_cancel_button)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer.Add(verse_reference_label, 0, wx.ALL, 5)
        bottom_sizer.Add(self.verse_input, 0, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.default_button, 0, wx.ALL, 5)
        button_sizer.Add(self.ok_button, 0, wx.ALL, 5)
        button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        bottom_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER, 5)
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_CHAR_HOOK, self.handle_key_press_in_dialog)
        self.apply_font_size(self.settings.get_setting("font_size"))

    def apply_font_size(self, font_size):
        font = self.GetFont()
        font.SetPointSize(font_size)
        self.SetFont(font)
        self.verse_input.SetFont(font)
        self.default_button.SetFont(font)
        self.ok_button.SetFont(font)
        self.cancel_button.SetFont(font)

    def load_book_abbreviations_mapping(self):
        with open(BOOK_ABBREVIATIONS_FILE, "r", encoding="utf-8") as f:
            abbreviations = json.load(f)
            return {k.lower(): v for k, v in abbreviations.items()}

    def handle_enter_key(self, event):
        self.handle_ok_button(event)

    def handle_ok_button(self, event):
        verse_reference = self.verse_input.GetValue().strip()
        if not self.parse_verse_reference(verse_reference):
            ui.message(_("Please check input text."))
            return
        if verse_reference not in self.reference_history:
            self.reference_history.insert(0, verse_reference)
            self.reference_history = self.reference_history[:10]
            self.verse_input.Clear()
            self.verse_input.Append(self.reference_history)
            self.settings.set_setting("reference_history", self.reference_history)
        self.result = (
            self.book_index,
            self.chapter,
            self.verse_start,
            self.open_in_new_tab,
        )
        self.EndModal(wx.ID_OK)

    def handle_default_button(self, event):
        self.result = (0, 1, 1, self.open_in_new_tab)
        self.EndModal(wx.ID_OK)

    def handle_cancel_button(self, event):
        self.EndModal(wx.ID_CANCEL)

    def parse_verse_reference(self, verse_reference):
        pattern = re.compile(r"^(\w+)\.?\s*(\d+)(?:[,:]\s*(\d+)(?:-(\d+))?)?$")
        match = pattern.match(verse_reference)
        if match:
            book_abbr, chapter, verse_start, verse_end = match.groups()
            book_abbr = book_abbr.lower()
            if book_abbr not in self.book_abbreviations:
                ui.message(_("No book matches the abbreviation {book_abbr}.").format(book_abbr=book_abbr))
                return False

            book_index = self.book_abbreviations[book_abbr]
            books = list(self.bible_data.keys())
            if book_index >= len(books):
                ui.message(_("The book of {book_name} is not available in the current translation.").format(book_name=book_abbr))
                return False

            book_key = books[book_index]
            available_chapters = list(self.bible_data[book_key].keys())
            if chapter not in available_chapters:
                ui.message(_("There is no chapter {chapter} in the book of {book}.").format(chapter=chapter, book=book_key))
                return False

            chapter_data = self.bible_data[book_key][chapter]
            if verse_start:
                verse_start_int = int(verse_start)
                if str(verse_start_int) not in chapter_data:
                    ui.message(_("There is no verse {verse} in {book} chapter {chapter}.").format(
                        verse=verse_start_int, book=book_key, chapter=chapter))
                    return False

                if verse_end:
                    verse_end_int = int(verse_end)
                    if str(verse_end_int) not in chapter_data:
                        ui.message(_("Verse {verse} not found in {book} {chapter}").format(
                            verse=verse_end_int, book=book_key, chapter=chapter))
                        return False

                    if verse_start_int > verse_end_int:
                        ui.message(_("Invalid verse range: start verse cannot be greater than end verse"))
                        return False
                else:
                    verse_end_int = verse_start_int
            else:
                verse_start_int = 1
                verse_end_int = 1

            self.book_index = book_index
            self.chapter = int(chapter)
            self.verse_start = verse_start_int
            self.verse_end = verse_end_int
            return True

        ui.message(_("Invalid Bible reference format."))
        return False

    def get_selected_verse_info(self):
        return self.result

    def handle_key_press_in_dialog(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()