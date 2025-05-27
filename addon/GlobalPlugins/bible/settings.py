import globalVars
import json
import os

user_config_dir = globalVars.appArgs.configPath
settings_file = os.path.join(user_config_dir, 'bible.json')

plugin_dir = os.path.dirname(__file__)
TRANSLATIONS_PATH = os.path.join(plugin_dir, 'translations')

class Settings:
    def __init__(self):
        self.settings_file = settings_file
        self.settings = {}
        self.bible_cache = {}
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "translation": "",
                "book_index": 0,
                "chapter_index": 0,
                "verse_number": 1,
                "font_size": 12,
                "whole_word": False,
                "case_sensitive": False,
                "category_selection": "All books",
                "use_regex": False,
                "gemini_api_key": None,
                "ai_search": False,
                "search_history": [],
                "link_history": [],
                "link_flag": True,
                "selected_translations": []
            }
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def load_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]

        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        bible_data = {}
        book_files = [file for file in os.listdir(translation_path) if file.endswith('.json')]
        for book_file in book_files:
            book_path = os.path.join(translation_path, book_file)
            with open(book_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
                book_key = book_file.split('. ', 1)[-1].replace('.json', '')
                bible_data[book_key] = book_data

        self.bible_cache[translation] = bible_data
        return bible_data

    def get_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]

        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        bible_data = {}
        book_files = [file for file in os.listdir(translation_path) if file.endswith('.json')]
        for book_file in book_files:
            book_path = os.path.join(translation_path, book_file)
            with open(book_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
                book_key = book_file.split('. ', 1)[-1].replace('.json', '')
                bible_data[book_key] = book_data

        self.bible_cache[translation] = bible_data
        return bible_data

    def clear_bible_cache(self):
        self.bible_cache = {}
