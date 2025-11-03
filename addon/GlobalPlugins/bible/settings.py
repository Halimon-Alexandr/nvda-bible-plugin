import globalVars
import json
import os
import requests
import wx

user_config_dir = globalVars.appArgs.configPath
settings_file = os.path.join(user_config_dir, 'bible.json')
TRANSLATIONS_PATH = os.path.join(user_config_dir, "bibleData/translations")
PLANS_PATH = os.path.join(user_config_dir, "bibleData/plans")


class Settings:
    def __init__(self):
        self.settings_file = settings_file
        self.settings = {}
        self.bible_cache = {}
        self.parallel_cache = {}
        self.available_translations = []
        self.available_plans = []
        self.load_settings()
        self.migrate_old_settings()
        self.load_available_translations()
        self.load_available_plans()

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
                "current_reading_plan": None,
                "current_plan_day": 1
            }
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def load_available_plans(self):
        self.available_plans = []
        try:
            if os.path.exists(PLANS_PATH):
                for filename in os.listdir(PLANS_PATH):
                    if filename.endswith('.json'):
                        plan_name = filename.replace('.json', '')
                        self.available_plans.append(plan_name)
                self.available_plans.sort()
                self.cleanup_reading_plan_progress(self.available_plans)
        except Exception as e:
            print(f"Error loading plan {e}")
        return self.available_plans

    def get_available_plans(self):
        return self.available_plans

    def get_reading_plan_data(self, plan_name):
        try:
            plan_path = os.path.join(PLANS_PATH, f"{plan_name}.json")
            if not os.path.exists(plan_path):
                return None
            
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            return plan_data
        except Exception as e:
            print(f"Error loading plan {plan_name}: {e}")
            return None

    def get_current_reading_plan(self):
        return self.get_setting("current_reading_plan")

    def set_current_reading_plan(self, plan_name):
        self.set_setting("current_reading_plan", plan_name)
        self.save_settings()

    def get_current_plan_day(self):
        return self.get_setting("current_plan_day", 1)

    def set_current_plan_day(self, day):
        self.set_setting("current_plan_day", day)
        self.save_settings()

    def get_plan_progress(self, plan_name):
        plan_progress = self.get_setting("plan_progress", {})
        return plan_progress.get(plan_name, {"current_day": 1, "completed_days": []})

    def set_plan_progress(self, plan_name, progress_data):
        plan_progress = self.get_setting("plan_progress", {})
        plan_progress[plan_name] = progress_data
        self.set_setting("plan_progress", plan_progress)
        self.save_settings()

    def download_reading_plan(self, plan_name):
        try:
            repo_owner = "Halimon-Alexandr"
            repo_name = "nvda-bible-plugin"
            branch = "master"
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/reading_plans/uk?ref={branch}"
            response = requests.get(api_url)
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
            
            plan_response = requests.get(download_url)
            if plan_response.status_code != 200:
                return False

            plan_path = os.path.join(PLANS_PATH, f"{plan_name}.json")
            os.makedirs(os.path.dirname(plan_path), exist_ok=True)

            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan_response.text)
            self.load_available_plans()
            return True
            
        except Exception as e:
            print(f"Error loading plan {plan_name}: {e}")
            return False

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
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def load_translation_data(self, translation):
        if translation in self.bible_cache:
            return self.bible_cache[translation]
        translation_path = os.path.join(TRANSLATIONS_PATH, translation)
        if not os.path.exists(translation_path):
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

    
    def get_reading_plan_progress(self, plan_name):
        progress_data = self.get_setting("reading_plan_progress", {})
        return progress_data.get(plan_name, {})
    
    def set_reading_plan_progress(self, plan_name, progress):
        progress_data = self.get_setting("reading_plan_progress", {})
        progress_data[plan_name] = progress
        self.set_setting("reading_plan_progress", progress_data)
        self.save_settings()
    
    def get_last_unread_day(self, plan_name, total_days):
        progress = self.get_reading_plan_progress(plan_name)
        for day in range(1, total_days + 1):
            day_str = str(day)
            if day_str not in progress:
                return day
            day_progress = progress[day_str]
            if not all(day_progress.values()):
                return day
        return total_days

    def cleanup_reading_plan_progress(self, available_plans):
        progress_data = self.get_setting("reading_plan_progress", {})
        plans_with_progress = list(progress_data.keys())
        for plan_name in plans_with_progress:
            if plan_name not in available_plans:
                del progress_data[plan_name]
        self.set_setting("reading_plan_progress", progress_data)
        self.save_settings()