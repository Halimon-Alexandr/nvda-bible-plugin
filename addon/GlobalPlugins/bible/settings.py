import re
import datetime
import globalVars
import languageHandler
import json
import os
import requests
import wx

user_config_dir = globalVars.appArgs.configPath
settings_file = os.path.join(user_config_dir, 'bible.json')
TRANSLATIONS_PATH = os.path.join(user_config_dir, "bibleData/translations")
PLANS_PATH = os.path.join(user_config_dir, "bibleData/plans")
plugin_dir = os.path.dirname(__file__)
BOOK_ABBREVIATIONS_FILE = os.path.join(plugin_dir, "book_abbreviations.json")

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.settings_file = settings_file
            self.settings = {}
            self.bible_cache = {}
            self.available_translations = []
            self.github_plans_cache = {}
            self.github_translations_cache = {}
            self.parallel_cache = {}
            self.plan_cache = {}
            self.load_settings()
            self.load_available_translations()
            self.load_available_plans()
            self.translation_mapping = self.load_available_translations_mapping()

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
                "current_reading_plan": None
            }
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def load_available_translations_mapping(self):
        if not os.path.exists(TRANSLATIONS_PATH):
            return {}

        all_translations = [
            name for name in os.listdir(TRANSLATIONS_PATH)
            if os.path.isdir(os.path.join(TRANSLATIONS_PATH, name))
        ]

        translation_mapping = {
            re.sub(r"^[A-Za-z]+(\s*-\s*)", "", t).strip(): t
            for t in all_translations
        }
        return translation_mapping

    def load_book_abbreviations_mapping(self, translation):
        full_translation_name = self.translation_mapping.get(translation, translation)

        translation_path = os.path.join(TRANSLATIONS_PATH, full_translation_name)

        abbreviations_file = os.path.join(translation_path, "book_abbreviations.json")

        if os.path.exists(abbreviations_file):
            with open(abbreviations_file, "r", encoding="utf-8") as f:
                abbreviations = json.load(f)
                return abbreviations
        else:
            with open(BOOK_ABBREVIATIONS_FILE, "r", encoding="utf-8") as f:
                abbreviations = json.load(f)
                return abbreviations

    def load_available_plans(self):
        self.available_plans = []
        if os.path.exists(PLANS_PATH):
            try:
                self.available_plans = [
                    filename.replace('.json', '')
                    for filename in os.listdir(PLANS_PATH)
                    if filename.endswith('.json')
                ]
                self.available_plans.sort()
                self.cleanup_reading_plan_progress(self.available_plans)
            except Exception:
                pass
        return self.available_plans

    def get_show_verse_numbers(self):
        return self.get_setting("show_verse_numbers", True)
    
    def set_show_verse_numbers(self, value):
        self.set_setting("show_verse_numbers", value)
    def get_available_plans(self):
        available_plans = []
        if os.path.exists(PLANS_PATH):
            try:
                available_plans = [
                    filename.replace('.json', '')
                    for filename in os.listdir(PLANS_PATH)
                    if filename.endswith('.json')
                ]
                available_plans.sort()
                self.cleanup_reading_plan_progress(available_plans)
            except Exception:
                pass
        return available_plans

    def delete_local_plan(self, plan_name):
        try:
            plan_path = os.path.join(PLANS_PATH, f"{plan_name}.json")
            if os.path.exists(plan_path):
                os.remove(plan_path)
                self.load_available_plans()
                return True
            return False
        except Exception:
            return False

    def get_reading_plan_data(self, plan_name):
        try:
            plan_path = os.path.join(PLANS_PATH, f"{plan_name}.json")
            if not os.path.exists(plan_path):
                return None
            with open(plan_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def get_current_reading_plan(self):
        return self.get_setting("current_reading_plan")

    def set_current_reading_plan(self, plan_name):
        self.set_setting("current_reading_plan", plan_name)
        self.save_settings()

    """
    def get_current_plan_day(self):
        return self.get_setting("current_plan_day", 1)

    def set_current_plan_day(self, day):
        self.set_setting("current_plan_day", day)
        self.save_settings()
    """

    def get_plan_progress(self, plan_name):
        plan_progress = self.get_setting("plan_progress", {})
        return plan_progress.get(plan_name, {"current_day": 1, "completed_days": []})

    def set_plan_progress(self, plan_name, progress_data):
        plan_progress = self.get_setting("plan_progress", {})
        plan_progress[plan_name] = progress_data
        self.set_setting("plan_progress", plan_progress)
        self.save_settings()

    def load_available_plans_from_github(self):
        current_lang = languageHandler.getLanguage().split('_')[0].lower()
        if current_lang in self.github_plans_cache:
            return self.github_plans_cache[current_lang]

        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            branch = "master"
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans?ref={branch}"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return []
            folders = response.json()
            available_lang_folders = [
                folder['name']
                for folder in folders
                if folder['type'] == 'dir'
            ]
            selected_lang = current_lang if current_lang in available_lang_folders else 'en'
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans/{selected_lang}?ref={branch}"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return []
            files = response.json()
            github_plans = [
                file['name'].replace('.json', '')
                for file in files
                if file['name'].endswith('.json')
            ]
            github_plans.sort()
            self.github_plans_cache[selected_lang] = github_plans
            return github_plans
        except Exception:
            return []

    def download_reading_plan(self, plan_name):
        if plan_name in self.plan_cache:
            plan_data = self.plan_cache[plan_name]
        else:
            try:
                repo_owner = "Halimon-Alexandr"
                repo_name = "nvda-bible-plugin"
                branch = "master"
                current_lang = languageHandler.getLanguage().split('_')[0].lower()
                api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans?ref={branch}"
                response = requests.get(api_url, timeout=10)
                if response.status_code != 200:
                    return False
                folders = response.json()
                available_lang_folders = [
                    folder['name']
                    for folder in folders
                    if folder['type'] == 'dir'
                ]
                selected_lang = current_lang if current_lang in available_lang_folders else 'en'
                api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans/{selected_lang}?ref={branch}"
                response = requests.get(api_url, timeout=10)
                if response.status_code != 200:
                    return False
                files = response.json()
                download_url = None
                for file_info in files:
                    if (file_info['name'].endswith('.json') and
                        file_info['name'].replace('.json', '') == plan_name):
                        download_url = file_info['download_url']
                        break
                if not download_url:
                    return False
                plan_response = requests.get(download_url, timeout=30)
                if plan_response.status_code != 200:
                    return False
                plan_data = plan_response.json()
                self.plan_cache[plan_name] = plan_data
            except Exception:
                return False
        try:
            plan_path = os.path.join(PLANS_PATH, f"{plan_name}.json")
            os.makedirs(os.path.dirname(plan_path), exist_ok=True)
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(self.plan_cache[plan_name], f, ensure_ascii=False, indent=4)
            self.load_available_plans()
            return True
        except Exception:
            return False

    def load_available_translations(self):
        if hasattr(self, 'github_translations_cache') and self.github_translations_cache:
            return self.available_translations

        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            folder_path = "translations"
            branch = "master"
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder_path}?ref={branch}"
            response = requests.get(api_url, timeout=10)
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
                local_translations = [
                    name for name in os.listdir(TRANSLATIONS_PATH)
                    if os.path.isdir(os.path.join(TRANSLATIONS_PATH, name))
                ]
            except Exception:
                pass

        self.github_translations_cache = github_translations
        self.local_translations = local_translations
        all_translations = list(set(github_translations + local_translations))
        all_translations.sort()
        self.available_translations = all_translations
        return all_translations

    def is_translation_local(self, translation_name):
        return translation_name in self.local_translations

    def is_translation_on_github(self, translation_name):
        return translation_name in self.github_translations_cache

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
            response = requests.get(api_url, timeout=10)
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

            zip_response = requests.get(download_url, stream=True, timeout=30)
            if zip_response.status_code != 200:
                return False

            import tempfile
            import zipfile
            import shutil

            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_path = tmp_file.name
                for chunk in zip_response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)

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

    def get_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]

        translation_path = os.path.join(TRANSLATIONS_PATH, translation)

        if not os.path.exists(translation_path):
            return {}

        bible_data = {}

        try:
            book_files = [
                file for file in os.listdir(translation_path)
                if file.endswith('.json') and file not in ['parallel.json', 'book_abbreviations.json']
            ]

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

        except Exception as e:
            print(f"Error loading translation data: {e}")

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

    def get_reading_plan_progress(self, plan_name):
        progress_data = self.get_setting("reading_plan_progress", {})
        return progress_data.get(plan_name, {})

    def set_reading_plan_progress(self, plan_name, progress):
        days_to_delete = []
        for day, day_progress in progress.items():
            if day == "start_date":
                continue

            has_true = any(day_progress.values())

            if not has_true:
                days_to_delete.append(day)

        for day in days_to_delete:
            del progress[day]

        progress_data = self.get_setting("reading_plan_progress", {})
        progress_data[plan_name] = progress
        self.set_setting("reading_plan_progress", progress_data)
        self.save_settings()

    def get_last_unread_day(self, plan_name, total_days):
        progress = self.get_reading_plan_progress(plan_name)
        plan_data = self.get_reading_plan_data(plan_name)
        if not plan_data:
            return 1

        for day_info in plan_data["days"]:
            day = day_info["day"]
            day_str = str(day)
            day_progress = progress.get(day_str, {})

            intro_key = "intro"
            is_intro_read = day_progress.get(intro_key, False)

            if not is_intro_read:
                return day

            readings = day_info.get("readings", [])
            all_read = True
            for reading in readings:
                book_num = reading["book"]
                chapter = reading["chapter"]
                verse = reading.get("verse")

                if verse is None:
                    reading_key = f"{book_num}_{chapter}_chapter"
                elif isinstance(verse, int):
                    reading_key = f"{book_num}_{chapter}_{verse}"
                elif isinstance(verse, str) and '-' in verse:
                    reading_key = f"{book_num}_{chapter}_{verse}"
                elif isinstance(verse, list) and len(verse) == 2:
                    start_verse, end_verse = verse
                    reading_key = f"{book_num}_{chapter}_{start_verse}-{end_verse}"
                else:
                    reading_key = f"{book_num}_{chapter}_{verse}"

                is_read = day_progress.get(reading_key, False)
                if not is_read:
                    all_read = False
                    break

            if not all_read:
                return day

        return 1

    def cleanup_reading_plan_progress(self, available_plans):
        progress_data = self.get_setting("reading_plan_progress", {})
        plans_with_progress = list(progress_data.keys())
        for plan_name in plans_with_progress:
            if plan_name not in available_plans:
                del progress_data[plan_name]
        self.set_setting("reading_plan_progress", progress_data)
        self.save_settings()

    def remove_reading_plan_progress(self, plan_name):
        progress_data = self.get_setting("reading_plan_progress", {})
        if plan_name in progress_data:
            del progress_data[plan_name]
            self.set_setting("reading_plan_progress", progress_data)
            self.save_settings()

        self.load_settings()

    def load_plan_from_github(self, plan_name):
        if plan_name in self.plan_cache:
            return self.plan_cache[plan_name]
        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            branch = "master"
            current_lang = languageHandler.getLanguage().split('_')[0].lower()
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans?ref={branch}"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return None
            folders = response.json()
            available_lang_folders = [
                folder['name']
                for folder in folders
                if folder['type'] == 'dir'
            ]
            selected_lang = current_lang if current_lang in available_lang_folders else 'en'
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/plans/{selected_lang}?ref={branch}"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return None
            files = response.json()
            download_url = None
            for file_info in files:
                if (file_info['name'].endswith('.json') and
                    file_info['name'].replace('.json', '') == plan_name):
                    download_url = file_info['download_url']
                    break
            if not download_url:
                return None
            plan_response = requests.get(download_url, timeout=30)
            if plan_response.status_code != 200:
                return None
            plan_data = plan_response.json()
            self.plan_cache[plan_name] = plan_data
            return plan_data
        except Exception:
            return None

    def get_plan_description(self, plan_name):
        plan_data = self.get_reading_plan_data(plan_name)
        if plan_data:
            return plan_data.get("cover", {}).get("description", "")

        plan_data = self.load_plan_from_github(plan_name)
        if plan_data:
            return plan_data.get("cover", {}).get("description", "")

        return ""
