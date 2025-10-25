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
        self.parallel_cache = {}
        self.load_settings()
        self.migrate_old_settings()

    def migrate_old_settings(self):
        if "translation" in self.settings and "book_index" in self.settings:
            self.settings.setdefault("tabs_states", []).append({
                "translation": self.settings.get("translation", ""),
                "book_index": self.settings.get("book_index", 0),
                "chapter_index": self.settings.get("chapter_index", 0),
                "verse_number": self.settings.get("verse_number", 0)
            })

        if "link_history" in self.settings:
            self.settings.setdefault("reference_history", []).extend(
                self.settings["link_history"]
            )
            del self.settings["link_history"]
        for key in ["translation", "book_index", "chapter_index", "verse_number"]:
            if key in self.settings:
                del self.settings[key]
        self.save_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "tabs_states": [],
    "current_tab_index": 0,
                "font_size": 12,
                "auto_check_updates": True,
                "whole_word": False,
                "case_sensitive": False,
                "category_selection": "All books",
                "use_regex": False,
                "gemini_api_key": None,
                "ai_search": False,
                "search_history": [],
                "reference_history": [],
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
        """Завантажує дані перекладу разом з паралельними посиланнями"""
        if translation in self.bible_cache:
            return self.bible_cache[translation]
        
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        bible_data = {}

        book_files = [file for file in os.listdir(translation_path) 
                     if file.endswith('.json') and file != 'parallel.json']
        for book_file in book_files:
            book_path = os.path.join(translation_path, book_file)
            with open(book_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
                book_key = book_file.split('. ', 1)[-1].replace('.json', '')
                bible_data[book_key] = book_data
        parallel_file = os.path.join(translation_path, 'parallel.json')
        if os.path.exists(parallel_file):
            with open(parallel_file, 'r', encoding='utf-8') as f:
                parallel_data = json.load(f)
                self.parallel_cache[translation] = parallel_data

        self.bible_cache[translation] = bible_data
        return bible_data

    def get_parallel_references(self, translation):
        if translation in self.parallel_cache:
            return self.parallel_cache[translation]

        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        parallel_file = os.path.join(translation_path, 'parallel.json')

        if os.path.exists(parallel_file):
            with open(parallel_file, 'r', encoding='utf-8') as f:
                parallel_data = json.load(f)
                self.parallel_cache[translation] = parallel_data
                return parallel_data

        return {}

    def clear_bible_cache(self):
        self.bible_cache = {}
        self.parallel_cache = {}

    def get_tabs_states(self):
        return self.get_setting("tabs_states", [])

    def set_tabs_states(self, states):
        self.set_setting("tabs_states", states)
