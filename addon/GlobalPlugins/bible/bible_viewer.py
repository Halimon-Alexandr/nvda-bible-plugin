import threading
import time
import ui
import wx
import os
import http.client
import winsound
import json
import re
import gettext
import languageHandler
from threading import Event

plugin_dir = os.path.dirname(__file__)
TRANSLATIONS_PATH = os.path.join(plugin_dir, 'translations')

BOOK_ABBREVIATIONS_FILE = os.path.join(plugin_dir, 'book_abbreviations.json')
LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(plugin_dir)), 'locale')

def _(message):
    language = languageHandler.getLanguage()

    try:
        translation = gettext.translation('nvda', localedir=LOCALE_DIR, languages=[language])
    except FileNotFoundError:
        translation = gettext.NullTranslations()

    return translation.gettext(message)

class BibleFrame(wx.Frame):
    def __init__(self, parent, title, settings):
        display_size = wx.DisplaySize()
        super(BibleFrame, self).__init__(parent, title=title, size=(display_size[0], display_size[1]))

        self.settings = settings
        self.panel = wx.Panel(self)
        self.find_data = wx.FindReplaceData()
        self.find_dialog = None
        self.bible_data = {}
        self.book_mapping = {}
        self.book_count = 66
        self.translation_mapping = {}

        self.book_label = wx.StaticText(self.panel, label=_("Book")+":")
        self.book_combo = wx.ComboBox(self.panel, style=wx.CB_READONLY)
        self.chapter_label = wx.StaticText(self.panel, label=_("Chapter")+":")
        self.chapter_combo = wx.ComboBox(self.panel, style=wx.CB_READONLY)
        self.translation_label = wx.StaticText(self.panel, label=_("Translation")+":")
        self.translation_combo = wx.ComboBox(self.panel, choices=self.load_available_translations(), style=wx.CB_READONLY)

        self.text_display = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(self.book_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        top_sizer.Add(self.book_combo, 2, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(self.chapter_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        top_sizer.Add(self.chapter_combo, 1, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(self.translation_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        top_sizer.Add(self.translation_combo, 2, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(self.text_display, 1, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(main_sizer)

        self.translation_combo.Bind(wx.EVT_COMBOBOX, self.handle_translation_selection)
        self.book_combo.Bind(wx.EVT_COMBOBOX, self.handle_book_selection)
        self.chapter_combo.Bind(wx.EVT_COMBOBOX, self.handle_chapter_selection)
        self.Bind(wx.EVT_CLOSE, self.handle_close_event)
        self.Bind(wx.EVT_CHAR_HOOK, self.handle_key_press)

        self.input_buffer = []
        self.input_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.handle_input_timer, self.input_timer)

        self.refresh_translation_comboboxes()
        self.restore_settings()

        self.set_focus_to_text_display()

        self.set_font_size()


    def set_focus_to_text_display(self):
        self.text_display.SetFocus()


    def load_available_translations(self):
        selected_translations = self.settings.get_setting("selected_translations", [])

        self.translation_mapping = {re.sub(r'^[A-Za-z]+(\s*-\s*)', '', t).strip(): t for t in selected_translations}
        return list(self.translation_mapping.keys())

    def refresh_translation_comboboxes(self):
        translation = self.translation_combo.GetValue()
        if translation:
            original_translation = self.translation_mapping[translation]
            self.load_bible_data_for_translation(original_translation)
            books = self.load_books_from_translation(original_translation)
            self.book_combo.Set(books)
            self.refresh_translation_options()
            if len(books) == 27 and self.settings.get_setting("book_index") >= 39:
                self.book_combo.SetSelection(self.settings.get_setting("book_index") - 39)
            else:
                self.book_combo.SetSelection(self.settings.get_setting("book_index"))
            self.refresh_chapter_combobox()

    def refresh_chapter_combobox(self):
        selected_book_index = self.book_combo.GetSelection()
        if selected_book_index != wx.NOT_FOUND:
            selected_book_key = list(self.bible_data.keys())[selected_book_index]
            chapters = list(self.bible_data[selected_book_key].keys())
            chapters.sort(key=int)
            self.chapter_combo.Set(chapters)
            self.chapter_combo.SetSelection(self.settings.get_setting("chapter_index"))
            self.display_chapter_text()
            self.set_window_title()
        else:
            self.chapter_combo.Set([])
            self.text_display.SetValue(_("Please select a book and chapter."))


    def display_chapter_text(self):
        selected_book_index = self.book_combo.GetSelection()
        selected_chapter_index = self.chapter_combo.GetSelection()
        if selected_book_index != wx.NOT_FOUND and selected_chapter_index != wx.NOT_FOUND:
            selected_book_key = list(self.bible_data.keys())[selected_book_index]
            chapters = sorted(self.bible_data[selected_book_key].keys(), key=int)
            selected_chapter = chapters[selected_chapter_index]
            chapter_data = self.bible_data.get(selected_book_key, {}).get(selected_chapter, {})
            if chapter_data:
                verses = [f"{verse}. {text}" for verse, text in chapter_data.items()]
                full_text = "\n".join(verses)
                self.text_display.SetValue(f"\n{full_text}\n")
                verse_number = self.settings.get_setting("verse_number")
                self.set_cursor_to_verse_number(verse_number)
            else:
                self.text_display.SetValue(_("Text not found."))
        else:
            self.text_display.SetValue(_("Please select a book and chapter."))
    def set_window_title(self):
        book_name = self.book_combo.GetValue()
        chapter = self.chapter_combo.GetValue()
        translation_label = self.translation_combo.GetValue()
        if book_name and chapter:
            title = f"{_('Bible')}, {_('Book')}: {book_name}, {_('Chapter')}: {chapter}, {translation_label}"
        else:
            title = f"{_('Bible')}, {translation_label}"
        self.SetTitle(title)

    def restore_settings(self):
        translation_value = self.settings.get_setting("translation")
        book_index_value = self.settings.get_setting("book_index")
        chapter_index_value = self.settings.get_setting("chapter_index")
        font_size_value = self.settings.get_setting("font_size")

        available_translations = self.load_available_translations()
        if translation_value not in available_translations:
            if available_translations:
                translation_value = available_translations[0]
            else:
                translation_value = ""

        self.translation_combo.SetValue(translation_value)
        self.book_combo.SetSelection(book_index_value)
        self.chapter_combo.SetSelection(chapter_index_value)
        self.set_font_size()

        self.refresh_translation_comboboxes()

    def save_current_state(self):
        self.settings.set_setting("translation", self.translation_combo.GetValue())
        self.settings.set_setting("book_index", self.book_combo.GetSelection())
        self.settings.set_setting("chapter_index", self.chapter_combo.GetSelection())
        self.settings.set_setting("verse_number", self.get_current_verse())

        self.settings.save_settings()


    def handle_translation_selection(self, event):
        self.saved_book_index = self.book_combo.GetSelection()
        self.saved_chapter_index = self.chapter_combo.GetSelection()
        self.saved_verse_number = self.get_current_verse()

        self.refresh_translation_comboboxes()
        self.refresh_translation_options()
        self.set_window_title()

        self.set_cursor_to_verse_number(self.saved_verse_number)

    def handle_book_selection(self, event):
        self.settings.set_setting("book_index", self.book_combo.GetSelection())
        self.settings.set_setting("chapter_index", 0)
        self.settings.set_setting("verse_number", None)

        self.refresh_chapter_combobox()
        self.set_window_title()

    def handle_chapter_selection(self, event):
        selected_chapter_index = self.chapter_combo.GetSelection()
        if selected_chapter_index != wx.NOT_FOUND:
            self.settings.set_setting("chapter_index", selected_chapter_index)
            self.settings.set_setting("verse_number", 1)
        self.display_chapter_text()
        self.set_window_title()

    def handle_close_event(self, event):
        self.save_current_state()
        self.Destroy()

    def handle_key_press(self, event):
        key_code = event.GetKeyCode()
        focused_widget = self.FindFocus()

        if focused_widget == self.text_display:
            if key_code == wx.WXK_ESCAPE:
                self.save_current_state()
                self.Close()
            elif event.ControlDown() and key_code == ord('F'):
                self.display_find_dialog()
            elif key_code >= ord('0') and key_code <= ord('9'):
                self.input_buffer.append(chr(key_code))
                self.input_timer.Start(500, wx.TIMER_ONE_SHOT)
            elif event.ControlDown() and key_code == ord('L'):
                self.display_verse_link_dialog()
            elif key_code == wx.WXK_NUMPAD_ADD or (event.ControlDown() and key_code == ord('+')):
                self.increase_text_font_size()
            elif key_code == wx.WXK_NUMPAD_SUBTRACT or (event.ControlDown() and key_code == ord('-')):
                self.decrease_text_font_size()
            elif event.ControlDown() and key_code == wx.WXK_PAGEUP:
                self.focus_and_speak_verse(verse_offset=-10)
            elif event.ControlDown() and key_code == wx.WXK_PAGEDOWN:
                self.focus_and_speak_verse(verse_offset=10)
            elif key_code == wx.WXK_PAGEUP:
                self.set_cursor_to_verse_number(verse_offset=-5)
            elif key_code == wx.WXK_PAGEDOWN:
                self.set_cursor_to_verse_number(verse_offset=5)
            else:
                event.Skip()
        else:
            if key_code == wx.WXK_ESCAPE:
                self.save_current_state()
                self.Close()
            elif event.AltDown() and key_code == wx.WXK_F4:
                self.save_current_state()
                self.Close()
            elif event.ControlDown() and key_code == ord('F'):
                self.display_find_dialog()
            elif event.ControlDown() and key_code == ord('L'):
                self.display_verse_link_dialog()
            elif key_code == wx.WXK_NUMPAD_ADD or (event.ControlDown() and key_code == ord('+')):
                self.increase_text_font_size()
            elif key_code == wx.WXK_NUMPAD_SUBTRACT or (event.ControlDown() and key_code == ord('-')):
                self.decrease_text_font_size()
            else:
                event.Skip()

    def handle_input_timer(self, event):
        verse_number = int(''.join(self.input_buffer))
        self.focus_and_speak_verse(verse_number)
        self.input_buffer = []

    def display_find_dialog(self):
        self.find_dialog = FindInBibleDialog(self, _("Search in Bible"), self.bible_data, self.find_data, self.settings.get_setting("font_size"))
        self.find_dialog.Show()

    def get_current_verse(self):
        current_pos = self.text_display.GetInsertionPoint()
        text_to_cursor = self.text_display.GetRange(0, current_pos)
        lines = text_to_cursor.split("\n")

        for line in reversed(lines):
            match = re.match(r"^(\d+)\.\s", line)
            if match:
                verse_number = int(match.group(1))
                return verse_number + 1

        return None

    def focus_and_speak_verse(self, verse_number=None, verse_offset=0):
        if verse_number is None:
            verse_number = self.get_current_verse()
        if verse_number is None:
            verse_number = verse_offset
        else:
            verse_number += verse_offset

        verse_pattern = re.compile(rf'^{verse_number}\.\s', re.MULTILINE)
        text_value = self.text_display.GetValue()
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start()
            line_end = text_value.find('\n', verse_start)
            if line_end == -1:
                line_end = len(text_value)
            self.text_display.SetInsertionPoint(verse_start + verse_number)
            verse_text = text_value[verse_start :line_end].strip()
            ui.message(verse_text)

    def set_cursor_to_verse_number(self, verse_number=None, verse_offset=0):
        if verse_number is None:
            verse_number = self.get_current_verse()
        if verse_number is None:
            verse_number = verse_offset
        else:
            verse_number += verse_offset

        verse_pattern = re.compile(rf'^{verse_number}\.\s', re.MULTILINE)
        text_value = self.text_display.GetValue()
        match = verse_pattern.search(text_value)
        if match:
            verse_start = match.start() + verse_number
            self.text_display.SetInsertionPoint(verse_start)


    def refresh_translation_options(self):
        current_translation = self.translation_combo.GetValue()
        selected_book_index = self.book_combo.GetSelection()

        all_translations = self.load_available_translations()
        current_translation_books_count = len(self.load_books_from_translation(self.translation_mapping[current_translation])) if current_translation else 66

        translations = []
        if current_translation_books_count == 66 and selected_book_index != wx.NOT_FOUND and selected_book_index < 39:
            translations = [t for t in all_translations if len(self.load_books_from_translation(self.translation_mapping[t])) == 66]
        elif current_translation_books_count == 27:
            translations = all_translations
        else:
            translations = [t for t in all_translations if len(self.load_books_from_translation(self.translation_mapping[t])) >= 27]

        self.translation_combo.Set(translations)

        if current_translation in translations:
            self.translation_combo.SetValue(current_translation)
        else:
            if translations:
                self.translation_combo.SetSelection(0)
            else:
                self.translation_combo.Clear()

    def load_books_from_translation(self, translation):
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        book_files = [file for file in os.listdir(translation_path) if file.endswith('.json')]
        book_files.sort()
        books = [file.split('. ', 1)[-1].replace('.json', '') for file in book_files]
        self.book_mapping = {index: book for index, book in enumerate(books)}
        return list(self.book_mapping.values())

    def load_bible_data_for_translation(self, translation):
        self.bible_data = self.settings.get_translation_data(translation)

    def display_verse_link_dialog(self):
        current_translation = self.translation_combo.GetValue()
        dialog = VerseLinkDialog(self, _("Link Navigation"), self.bible_data, current_translation, self.settings)
        if dialog.ShowModal() == wx.ID_OK:
            book_index, chapter, verse = dialog.get_selected_verse_info()
            open_in_main = dialog.is_open_in_main_selected()
            self.navigate_to_verse_link(book_index, chapter, verse, open_in_main)
        dialog.Destroy()

    def navigate_to_verse_link(self, book_index, chapter, verse, open_in_main=True):
        if open_in_main:
            self.settings.set_setting("book_index", book_index)
            self.settings.set_setting("chapter_index", int(chapter) - 1)
            self.settings.set_setting("verse_number", int(verse))
            self.refresh_translation_comboboxes()
            if self.book_combo.GetCount() > 0 and self.settings.get_setting("book_index") == -1:
                self.settings.set_setting("book_index", 0)
                self.book_combo.SetSelection(0)
                self.refresh_chapter_combobox()
            if self.chapter_combo.GetCount() > 0 and self.settings.get_setting("chapter_index") == -1:
                self.settings.set_setting("chapter_index", 0)
                self.chapter_combo.SetSelection(0)
                self.display_chapter_text()
            wx.CallAfter(self.set_cursor_to_verse_number, self.settings.get_setting("verse_number"))
            self.set_focus_to_text_display()
        else:
            verse_text = dialog.get_verse_text_range(book_index, chapter, verse)
            self.verse_text_display.SetValue(verse_text)

    def navigate_to_verse(self, verse_link):
        pattern = re.compile(r'^(\w+)\s+(\d+),\s*(\d+)$')
        match = pattern.match(verse_link)
        if match:
            book_abbr, chapter, verse = match.groups()
            book_index = self.book_abbreviations.get(book_abbr, None)
            if book_index is not None:
                self.book_combo.SetSelection(book_index)
                self.chapter_combo.SetSelection(int(chapter) - 1)
                self.display_chapter_text()
                self.set_cursor_to_verse_number(int(verse))
                self.set_focus_to_text_display()

    def set_font_size(self):
        font = self.text_display.GetFont()
        font.SetPointSize(self.settings.get_setting("font_size"))
        self.text_display.SetFont(font)

    def increase_text_font_size(self):
        self.settings.set_setting("font_size", self.settings.get_setting("font_size") + 1)
        ui.message(f"{_('Font size')}: {self.settings.get_setting('font_size')}")
        self.set_font_size()
        self.save_current_state()


    def decrease_text_font_size(self):
        if self.settings.get_setting("font_size") > 1:
            self.settings.set_setting("font_size", self.settings.get_setting("font_size") - 1)
            ui.message(f"{_('Font size')}: {self.settings.get_setting('font_size')}")
            self.set_font_size()
            self.save_current_state()

class NotificationDialog(wx.Dialog):
    def __init__(self, parent, title, message):
        super(NotificationDialog, self).__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.message_label = wx.StaticText(self, label=message)
        self.ok_button = wx.Button(self, label="OK")
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.message_label, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(self.ok_button, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.SetSizer(main_sizer)
        self.Fit()

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

    def on_key_down(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()


class VerseLinkDialog(wx.Dialog):
    def __init__(self, parent, title, bible_data, current_translation, settings):
        display_size = wx.DisplaySize()
        super(VerseLinkDialog, self).__init__(parent, title=title, size=(display_size[0], display_size[1]*0.9))

        self.bible_data = bible_data
        self.current_translation = current_translation
        self.book_abbreviations = self.load_book_abbreviations_mapping()
        self.settings = settings

        if not self.settings.get_setting("link_history"):
            self.settings.set_setting("link_history", [])

        self.link_history = self.settings.get_setting("link_history")

        verse_link_label = wx.StaticText(self, label=_("Enter verse link:"))

        self.verse_input = wx.ComboBox(self, style=wx.TE_PROCESS_ENTER | wx.CB_DROPDOWN)
        self.verse_input.Bind(wx.EVT_TEXT_ENTER, self.handle_enter_key)
        self.verse_input.Append(self.link_history)

        self.open_in_main_checkbox = wx.CheckBox(self, label=_("Open in main window"))
        self.open_in_main_checkbox.SetValue(self.settings.get_setting("link_flag"))
        self.open_in_main_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_checkbox_change)

        self.ok_button = wx.Button(self, label=_("OK"))
        self.ok_button.Bind(wx.EVT_BUTTON, self.handle_ok_button)

        self.cancel_button = wx.Button(self, label=_("Cancel"))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.handle_cancel_button)

        self.verse_text_display = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.verse_text_display, 1, wx.EXPAND | wx.ALL, 5)

        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer.Add(verse_link_label, 0, wx.ALL, 5)
        bottom_sizer.Add(self.verse_input, 0, wx.EXPAND | wx.ALL, 5)
        bottom_sizer.Add(self.open_in_main_checkbox, 0, wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
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
        self.open_in_main_checkbox.SetFont(font)
        self.ok_button.SetFont(font)
        self.cancel_button.SetFont(font)
        self.verse_text_display.SetFont(font)

    def load_book_abbreviations_mapping(self):
        with open(BOOK_ABBREVIATIONS_FILE, 'r', encoding='utf-8') as f:
            abbreviations = json.load(f)
            return {k.lower(): v for k, v in abbreviations.items()}

    def handle_enter_key(self, event):
        self.handle_ok_button(event)

    def handle_ok_button(self, event):
        verse_link = self.verse_input.GetValue().strip()
        if self.parse_verse_link(verse_link):
            if not self.open_in_main_checkbox.GetValue():
                verse_text = self.get_verse_text_range(self.book_index, self.chapter, self.verse_start, self.verse_end)
                self.verse_text_display.SetValue(verse_text)
                self.focus_verse_text_display()
            else:
                self.EndModal(wx.ID_OK)

            if verse_link not in self.link_history:
                self.link_history.insert(0, verse_link)
                self.link_history = self.link_history[:10]
                self.verse_input.Clear()
                self.verse_input.Append(self.link_history)
                self.settings.set_setting("link_history", self.link_history)
        else:
            notification_dialog = NotificationDialog(self, _("Notification"), _("Invalid verse link format. Please refer to the documentation for more information."))
            notification_dialog.ShowModal()
            notification_dialog.Destroy()

    def handle_cancel_button(self, event):
        self.EndModal(wx.ID_CANCEL)

    def handle_checkbox_change(self, event):
        self.settings.set_setting("link_flag", self.open_in_main_checkbox.GetValue())

    def parse_verse_link(self, verse_link):
        pattern = re.compile(r'^(\w+)\.?\s*(\d+)(?:[,:]\s*(\d+)(?:-(\d+))?)?$')
        match = pattern.match(verse_link)
        if match:
            book_abbr, chapter, verse_start, verse_end = match.groups()
            book_abbr = book_abbr.lower()
            if book_abbr in self.book_abbreviations:
                self.book_index = self.book_abbreviations[book_abbr]
                self.chapter = int(chapter)
                self.verse_start = int(verse_start) if verse_start else 1
                self.verse_end = int(verse_end) if verse_end else self.verse_start
                return True
        return False

    def get_selected_verse_info(self):
        if self.open_in_main_checkbox.GetValue():
            return self.book_index, self.chapter, self.verse_start
        else:
            return self.book_index, self.chapter, self.verse_start, self.verse_end

    def is_open_in_main_selected(self):
        return self.open_in_main_checkbox.GetValue()

    def get_verse_text_range(self, book_index, chapter, verse_start, verse_end):
        selected_book_key = list(self.bible_data.keys())[book_index]
        chapters = list(self.bible_data[selected_book_key].keys())
        chapters.sort(key=int)
        selected_chapter = chapters[chapter - 1]
        chapter_data = self.bible_data.get(selected_book_key, {}).get(selected_chapter, {})
        if chapter_data:
            verse_texts = []
            for verse in range(verse_start, verse_end + 1):
                verse_text = chapter_data.get(str(verse), "")
                if verse_text:
                    verse_texts.append(f"{verse}. {verse_text}")
            if verse_texts:
                if verse_start == verse_end:
                    return f"{selected_book_key} {selected_chapter}:{verse_start}\n\n" + "\n".join(verse_texts)
                else:
                    return f"{selected_book_key} {selected_chapter}:{verse_start}-{verse_end}\n\n" + "\n".join(verse_texts)
        return _("Text not found.")

    def focus_verse_text_display(self):
        self.verse_text_display.SetFocus()

    def handle_key_press_in_dialog(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()


class FindInBibleDialog(wx.Dialog):
    def __init__(self, parent, title, bible_data, find_data, font_size):
        display_size = wx.DisplaySize()
        super().__init__(parent, title=title, size=(display_size[0], display_size[1]*0.9))
        self.current_search_text = ""
        self.bible_data = bible_data
        self.find_data = find_data
        self.parent = parent
        self.settings = parent.settings

        self.search_history = self.settings.get_setting("search_history")

        search_label = wx.StaticText(self, label=_("Text for search:"))
        self.text_ctrl = wx.ComboBox(self, style=wx.TE_PROCESS_ENTER | wx.CB_DROPDOWN)
        self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self.handle_find_button)
        self.text_ctrl.Append(self.search_history)

        category_label = wx.StaticText(self, label=_("Category for search:"))
        self.category_combo = wx.ComboBox(self, choices=[_("All books"), _("None")], style=wx.CB_READONLY)
        self.category_combo.Bind(wx.EVT_COMBOBOX, self.handle_category_selection)

        books_label = wx.StaticText(self, label=_("Books for search:"))
        self.books_list = list(self.bible_data.keys())
        self.book_list = wx.ListBox(self, choices=self.books_list, style=wx.LB_MULTIPLE)

        for i in range(self.book_list.GetCount()):
            self.book_list.SetSelection(i)

        self.book_list.SetSelection(0)

        self.whole_word_checkbox = wx.CheckBox(self, label=_("Whole word"))
        self.whole_word_checkbox.SetValue(self.settings.get_setting("whole_word"))
        self.whole_word_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)

        self.case_sensitive_checkbox = wx.CheckBox(self, label=_("Case sensitive"))
        self.case_sensitive_checkbox.SetValue(self.settings.get_setting("case_sensitive"))
        self.case_sensitive_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)

        self.regex_checkbox = wx.CheckBox(self, label=_("Regular expressions"))
        self.regex_checkbox.SetValue(self.settings.get_setting("use_regex"))
        self.regex_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)

        gemini_api_key = self.settings.get_setting("gemini_api_key")
        if gemini_api_key:
            self.ai_search_checkbox = wx.CheckBox(self, label=_("AI Search"))
            self.ai_search_checkbox.SetValue(self.settings.get_setting("ai_search"))
            self.ai_search_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_search_option_change)

        self.find_button = wx.Button(self, label=_("Search"))
        self.find_button.Bind(wx.EVT_BUTTON, self.handle_find_button)

        self.results_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.results_ctrl.Bind(wx.EVT_KEY_DOWN, self.handle_results_key_press)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        options_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Search options")), wx.VERTICAL)

        main_sizer.Add(self.results_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        search_sizer.Add(search_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        search_sizer.Add(self.text_ctrl, 2, wx.EXPAND | wx.ALL, 5)

        search_sizer.Add(category_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        search_sizer.Add(self.category_combo, 1, wx.EXPAND | wx.ALL, 5)

        search_sizer.Add(books_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        search_sizer.Add(self.book_list, 1, wx.EXPAND | wx.ALL, 5)

        options_sizer.Add(self.whole_word_checkbox, 0, wx.ALL, 5)
        options_sizer.Add(self.case_sensitive_checkbox, 0, wx.ALL, 5)
        options_sizer.Add(self.regex_checkbox, 0, wx.ALL, 5)

        if gemini_api_key:
            options_sizer.Add(self.ai_search_checkbox, 0, wx.ALL, 5)

        options_sizer.Add(self.find_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        search_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)

        self.Bind(wx.EVT_CHAR_HOOK, self.handle_key_down)
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

        if hasattr(self, 'response_handled') and self.response_handled:
            return
        self.response_handled = True

        formatted_response = self.format_response(response) if response else _("No results found.")

        wx.CallAfter(self.display_verses_from_current_translation, formatted_response)
    
        if formatted_response == _("No results found."):
            wx.CallAfter(self.show_notification, _("Unfortunately, nothing was found. Please try adjusting your search query."))
    
        self.response_handled = False
        if hasattr(self, 'search_performed'):
            self.search_performed = False
    
    def format_response(self, response):
        try:
            results = response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not results:
                return _("No results found.")

            return results

        except Exception as e:
            return _("Error processing response.")


    def show_notification(self, message):
        if not hasattr(self, 'notification_shown') or not self.notification_shown:
            notification_dialog = NotificationDialog(self, _("Notification"), message)
            notification_dialog.ShowModal()
            notification_dialog.Destroy()
            self.notification_shown = True

    def perform_ai_search(self, search_text, selected_books):
        if hasattr(self, 'search_performed') and self.search_performed:
            return
    
        self.search_performed = True
    
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
        thread = threading.Thread(target=self.generate_text_with_sound, args=(prompt, self.handle_response))
        thread.start()


    def generate_text_with_sound(self, prompt, callback):
        
        self.sound_event = Event()
        
        def sound_indicator():
            while not self.sound_event.is_set() and self.IsShown():
                wx.CallAfter(winsound.Beep, 500, 100)
                time.sleep(1)
        
        sound_thread = threading.Thread(target=sound_indicator)
        sound_thread.start()
        
        wx.CallAfter(winsound.Beep, 800, 200)
        
        try:
            API_KEY = self.settings.get_setting("gemini_api_key")
            conn = http.client.HTTPSConnection("generativelanguage.googleapis.com", timeout=90)
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': API_KEY
            }
            payload = json.dumps({
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            })

            conn.request("POST", "/v1beta/models/gemini-2.0-flash:generateContent", payload, headers)
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
                verse_pattern = re.compile(r'^[А-ЯЇІЄҐа-яїієґ\w\s]+ \d+:\d+ -')
                lines = formatted_results.split('\n')
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

        if hasattr(self, 'ai_search_checkbox'):
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
        selected_books = [self.book_list.GetString(i) for i in self.book_list.GetSelections()]

        if not search_text:
            notification_dialog = NotificationDialog(self, _("Notification"), _("The search field is empty! Please enter text first."))
            notification_dialog.ShowModal()
            notification_dialog.Destroy()
            return

        if not selected_books:
            notification_dialog = NotificationDialog(self, _("Notification"), _("No book selected for search. Please select at least one."))
            notification_dialog.ShowModal()
            notification_dialog.Destroy()
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
                notification_dialog = NotificationDialog(self, _("Error"), _("Invalid regular expression!"))
                notification_dialog.ShowModal()
                notification_dialog.Destroy()
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
                        search_text_check = search_text.lower() if not case_sensitive else search_text
                        if use_regex:
                            if re.search(search_text_check, verse_text):
                                found_verses.append(f"{book_name} {chapter_key}:{verse_num} - {verse}")
                        else:
                            if (whole_word and search_text_check in verse_text.split()) or (not whole_word and search_text_check in verse_text):
                                found_verses.append(f"{book_name} {chapter_key}:{verse_num} - {verse}")

            if found_verses:
                result = f"{_('Number of verses found')}: {len(found_verses)}\n\n" + "\n".join(found_verses) + "\n"
                self.results_ctrl.SetValue(result)
                self.results_ctrl.SetFocus()
            else:
                notification_dialog = NotificationDialog(self, _("Notification"), _("Unfortunately, nothing was found. Please try adjusting your search query."))
                notification_dialog.ShowModal()
                notification_dialog.Destroy()

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
        elif hasattr(self, 'ai_search_checkbox') and checkbox == self.ai_search_checkbox:
            self.settings.set_setting("ai_search", checkbox.GetValue())


    def handle_dialog_close(self, event):
        self.Destroy()

    def handle_results_key_press(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.handle_current_verse_info()
        event.Skip()

    def handle_current_verse_info(self):
        current_pos = self.results_ctrl.GetInsertionPoint()
        text_to_cursor = self.results_ctrl.GetRange(0, current_pos)
        lines = text_to_cursor.split("\n")
        current_line = lines[-1]
        text_after_cursor = self.results_ctrl.GetRange(current_pos, self.results_ctrl.GetLastPosition())
        full_line = current_line + text_after_cursor.split("\n")[0]

        match = re.match(r'^([\w\' ]+ [^:]+):(\d+(?:-\d+)?) - .*', full_line)
        if match:
            book_chapter, verse_range = match.groups()
            book, chapter = book_chapter.rsplit(' ', 1)

            verse_number = verse_range.split('-')[0]

            book_index = self.get_book_index_by_name(book)
            if book_index is not None:
                self.parent.navigate_to_verse_link(book_index, int(chapter), int(verse_number))
                self.EndModal(wx.ID_OK)
        else:
            if len(lines) > 1:
                previous_line = lines[-2]
                match = re.match(r'^([\w\' ]+ [^:]+):(\d+(?:-\d+)?) - .*', previous_line)
                if match:
                    book_chapter, verse_range = match.groups()
                    book, chapter = book_chapter.rsplit(' ', 1)

                    verse_number = verse_range.split('-')[0]

                    book_index = self.get_book_index_by_name(book)
                    if book_index is not None:
                        self.parent.navigate_to_verse_link(book_index, int(chapter), int(verse_number))
                        self.EndModal(wx.ID_OK)

    def get_book_index_by_name(self, book_name):
        for index, book in self.book_mapping.items():
            if book == book_name:
                return index
        return None

    def navigate_to_verse_link_in_parent(self, book_index, chapter, verse):
        self.parent.navigate_to_verse_link(book_index, chapter, verse)

    def update_category_combo(self):
        current_translation = self.parent.translation_combo.GetValue()
        current_translation_books_count = len(self.parent.load_books_from_translation(self.parent.translation_mapping[current_translation])) if current_translation else 66

        if current_translation_books_count == 66:
            categories = [_("All books"), _("None"), _("Old Testament"), _("New Testament")]
        else:
            categories = [_("All books"), _("None")]

        self.category_combo.Set(categories)
