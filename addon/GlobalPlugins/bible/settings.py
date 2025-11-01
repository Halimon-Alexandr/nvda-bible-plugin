import globalVars
import json
import os
import requests
import wx
import gui

user_config_dir = globalVars.appArgs.configPath
settings_file = os.path.join(user_config_dir, 'bible.json')
TRANSLATIONS_PATH = os.path.join(user_config_dir, "bibleData/translations")
PLANS_PATH = os.path.join(user_config_dir, "bibleData/plans/uk")


class Settings:
    def __init__(self):
        self.settings_file = settings_file
        self.settings = {}
        self.bible_cache = {}
        self.parallel_cache = {}
        self.available_translations = []
        self.load_settings()
        self.migrate_old_settings()
        self.load_available_translations()

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
                "reference_history": []
            }
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def load_available_translations(self):
        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            folder_path = "translations"
            branch = "master"
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder_path}?ref={branch}"
            response = requests.get(api_url)
            github_translations = []
            if response.status_code == 200:
                files = response.json()
                for file in files:
                    if file['name'].endswith('.zip'):
                        translation_name = file['name'].replace('.zip', '')
                        github_translations.append(translation_name)
                    elif file['type'] == 'dir':
                        github_translations.append(file['name'])
        except Exception:
            github_translations = []

        local_translations = []
        if os.path.exists(TRANSLATIONS_PATH):
            try:
                local_translations = [name for name in os.listdir(TRANSLATIONS_PATH)
                                    if os.path.isdir(os.path.join(TRANSLATIONS_PATH, name))]
            except Exception:
                pass

        self.github_translations = github_translations
        self.local_translations = local_translations
        all_translations = list(set(github_translations + local_translations))
        all_translations.sort()
        self.available_translations = all_translations
        return all_translations

    def is_translation_local(self, translation_name):
        return translation_name in self.local_translations

    def is_translation_on_github(self, translation_name):
        return translation_name in self.github_translations

    def delete_local_translation(self, translation_name):
        try:
            translation_path = os.path.join(TRANSLATIONS_PATH, translation_name)
            if os.path.exists(translation_path):
                import shutil
                shutil.rmtree(translation_path)
                if translation_name in self.local_translations:
                    self.local_translations.remove(translation_name)
                if translation_name in self.bible_cache:
                    del self.bible_cache[translation_name]
                if translation_name in self.parallel_cache:
                    del self.parallel_cache[translation_name]
                self.load_available_translations()
                return True
            return False
        except Exception:
            return False

    def get_available_translations(self):
        return self.available_translations

    def download_translation(self, translation_name):
        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            branch = "master"
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/translations?ref={branch}"
            response = requests.get(api_url)
            if response.status_code != 200:
                return False
            files = response.json()
            download_url = None
            for file_info in files:
                if (file_info['name'].endswith('.zip') and
                    file_info['name'].replace('.zip', '') == translation_name):
                    download_url = file_info['download_url']
                    break
            if not download_url:
                return False
            zip_response = requests.get(download_url)
            if zip_response.status_code != 200:
                return False
            import tempfile
            import zipfile
            import shutil
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(zip_response.content)
                tmp_path = tmp_file.name
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir)
                    expected_folder = os.path.join(tmp_dir, translation_name)
                    if os.path.exists(expected_folder) and os.path.isdir(expected_folder):
                        translation_path = os.path.join(TRANSLATIONS_PATH, translation_name)
                        if os.path.exists(translation_path):
                            shutil.rmtree(translation_path)
                        shutil.move(expected_folder, translation_path)
                    else:
                        items = os.listdir(tmp_dir)
                        if len(items) == 1 and os.path.isdir(os.path.join(tmp_dir, items[0])):
                            found_folder = os.path.join(tmp_dir, items[0])
                            translation_path = os.path.join(TRANSLATIONS_PATH, translation_name)
                            if os.path.exists(translation_path):
                                shutil.rmtree(translation_path)
                            shutil.move(found_folder, translation_path)
                        else:
                            translation_path = os.path.join(TRANSLATIONS_PATH, translation_name)
                            if os.path.exists(translation_path):
                                shutil.rmtree(translation_path)
                            os.makedirs(translation_path)
                            for item in items:
                                shutil.move(os.path.join(tmp_dir, item), translation_path)
                    if translation_name not in self.local_translations:
                        self.local_translations.append(translation_name)
                    return True
            finally:
                os.unlink(tmp_path)
        except Exception:
            return False

    def load_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        if not os.path.exists(translation_path):
            if gui.messageBox(
                f"Переклад '{translation}' не знайдено локально. Завантажити з GitHub?",
                "Завантаження перекладу",
                wx.YES_NO | wx.ICON_QUESTION
            ) == wx.YES:
                if self.download_translation(translation):
                    gui.messageBox(f"Переклад '{translation}' успішно завантажено!", "Успіх", wx.OK | wx.ICON_INFORMATION)
                else:
                    gui.messageBox(f"Не вдалося завантажити переклад '{translation}'", "Помилка", wx.OK | wx.ICON_ERROR)
                    return {}
        bible_data = {}
        try:
            book_files = [file for file in os.listdir(translation_path) if file.endswith('.json')]
            for book_file in book_files:
                book_path = os.path.join(translation_path, book_file)
                with open(book_path, 'r', encoding='utf-8') as f:
                    book_data = json.load(f)
                    book_key = book_file.split('. ', 1)[-1].replace('.json', '')
                    bible_data[book_key] = book_data
            self.bible_cache[translation] = bible_data
        except Exception:
            pass
        return bible_data

    def get_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        bible_data = {}
        try:
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
        except Exception:
            pass
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
