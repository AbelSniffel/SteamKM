import os
import requests
import webbrowser
import re
import logging
import difflib
from pathlib import Path
from bs4 import BeautifulSoup
from PySide6.QtCore import QThread, Signal, QMutex
from CustomWidgets import create_scrollable_message_dialog

class SteamFetchManager:
    def __init__(self, parent, table_widget, games, icons_folder):
        self.parent = parent
        self.table_widget = table_widget
        self.games = games
        self.icons_folder = icons_folder
        self.steam_fetcher = None
        self.status_label = None  # Will be set from Main.py
        self.fetch_button = None  # Will be set from Main.py
        self.is_fetching = False
        
        self.pending_updates = {}
        self.update_mutex = QMutex()
    
    def set_status_label(self, label):
        """Set the status label that will display fetch progress"""
        self.status_label = label
    
    def set_fetch_button(self, button):
        """Set the fetch button that will toggle between fetch and cancel"""
        self.fetch_button = button
    
    def cancel_steam_fetch(self):
        """Cancel an active fetch operation"""
        if self.steam_fetcher and self.steam_fetcher.isRunning():
            self.steam_fetcher.stop()
            self.update_status_text("Canceling fetch operation...\nPlease wait.")
    
    def update_status_text(self, text):
        """Update the status label with current fetch status"""
        if self.status_label:
            self.status_label.setText(text)
    
    def set_fetch_button_state(self, is_fetching):
        """Update the fetch button state based on whether a fetch operation is active"""
        if self.fetch_button:
            self.is_fetching = is_fetching
            if is_fetching:
                self.fetch_button.setText("Cancel Fetch")
                self.fetch_button.setToolTip("Cancel the current Steam data fetch operation")
                self.fetch_button.clicked.disconnect()
                self.fetch_button.clicked.connect(self.cancel_steam_fetch)
            else:
                self.fetch_button.setText("Fetch Steam Data")
                self.fetch_button.setToolTip("Fetch or update Steam data for games")
                self.fetch_button.clicked.disconnect()
                self.fetch_button.clicked.connect(self.parent.open_steam_fetch_menu)
    
    def filter_incomplete_games(self):
        incomplete_games = {}

        for game_id, game_data in self.games.items():
            app_id_missing = not game_data.get("app_id", "").strip()
            icon_path = game_data.get("icon_path", "")
            icon_missing = not icon_path or not os.path.exists(icon_path)
            review_missing = "review_data" not in game_data
            developer_missing = "developer" not in game_data or not game_data.get("developer", "").strip()
            
            if app_id_missing or icon_missing or review_missing or developer_missing:
                incomplete_games[game_id] = game_data
                
        return incomplete_games
    
    def start_steam_fetch(self, update_reviews_only=False, specific_games=None):
        self.update_mutex.lock()
        self.pending_updates.clear()
        self.update_mutex.unlock()

        # Always filter for incomplete games, even for imported/new games
        if specific_games is not None:
            # Only fetch for incomplete games among the provided set
            games_to_process = self.filter_incomplete_games_from_dict(specific_games)
        elif not update_reviews_only:
            games_to_process = self.filter_incomplete_games()
            if not games_to_process:
                self.update_status_text("")
                dialog, _ = create_scrollable_message_dialog(
                    parent=self.parent,
                    title="Steam Data",
                    message="Couldn't find any missing data to fetch",
                    content=["All games appear to have complete data"],
                    min_width=400,
                    min_height=150
                )
                dialog.exec()
                return
        else:
            games_to_process = self.games

        # Change button to Cancel mode before starting the thread
        self.set_fetch_button_state(True)

        self.steam_fetcher = SteamGameFetcher(
            games_to_process,
            self.icons_folder,
            update_reviews_only=update_reviews_only,
            batch_mode=(update_reviews_only or specific_games is not None)
        )
        self.steam_fetcher.progress_signal.connect(self.update_steam_data)
        self.steam_fetcher.finished_signal.connect(self.steam_fetch_finished)
        self.steam_fetcher.update_text_signal.connect(self.update_status_text)
        self.steam_fetcher.start()

    def filter_incomplete_games_from_dict(self, games_dict):
        """Filter incomplete games from a provided dictionary (used for imports/edits)"""
        incomplete_games = {}
        for game_id, game_data in games_dict.items():
            app_id_missing = not game_data.get("app_id", "").strip()
            icon_path = game_data.get("icon_path", "")
            icon_missing = not icon_path or not os.path.exists(icon_path)
            review_missing = "review_data" not in game_data
            developer_missing = "developer" not in game_data or not game_data.get("developer", "").strip()
            if app_id_missing or icon_missing or review_missing or developer_missing:
                incomplete_games[game_id] = game_data
        return incomplete_games

    # Remove fetch_for_new_games and fetch_for_edited_games, or make them thin wrappers:
    def fetch_for_new_games(self, new_games_dict):
        self.start_steam_fetch(specific_games=new_games_dict)

    def fetch_for_edited_games(self, modified_games_dict):
        self.start_steam_fetch(specific_games=modified_games_dict)
    
    def update_steam_data(self, game_id, app_id, icon_path, review_data, developer):
        if game_id in self.games:
            self.update_mutex.lock()
            
            game_data = self.games[game_id]
            
            if self.steam_fetcher and self.steam_fetcher.batch_mode:
                self.pending_updates[game_id] = {
                    "app_id": app_id,
                    "icon_path": icon_path if icon_path else game_data.get("icon_path", ""),
                    "review_data": review_data if review_data else game_data.get("review_data", {}),
                    "developer": developer if developer else game_data.get("developer", "")
                }
            else:
                game_data["app_id"] = app_id
                if icon_path:
                    game_data["icon_path"] = icon_path
                if review_data:
                    game_data["review_data"] = review_data
                if developer:
                    game_data["developer"] = developer
                
                if hasattr(self.parent, 'save_key_data'):
                    self.parent.save_key_data()
                if hasattr(self.parent, 'refresh_game_list'):
                    self.parent.refresh_game_list()
            
            self.update_mutex.unlock()
    
    def apply_pending_updates(self):
        if not self.pending_updates:
            return
            
        self.update_mutex.lock()
        
        try:
            for game_id, update_data in self.pending_updates.items():
                if game_id in self.games:
                    game_data = self.games[game_id]
                    game_data["app_id"] = update_data["app_id"]
                    
                    if update_data["icon_path"]:
                        game_data["icon_path"] = update_data["icon_path"]
                    
                    if update_data["review_data"]:
                        game_data["review_data"] = update_data["review_data"]
                    
                    if update_data["developer"]:
                        game_data["developer"] = update_data["developer"]
            
            self.pending_updates.clear()
            
            if hasattr(self.parent, 'save_key_data'):
                self.parent.save_key_data()
            
            if hasattr(self.parent, 'refresh_game_list'):
                self.parent.refresh_game_list()
                
        finally:
            self.update_mutex.unlock()
    
    def steam_fetch_finished(self, failed_titles):
        was_canceled = self.steam_fetcher and not self.steam_fetcher.running
        
        self.apply_pending_updates()
        
        # Change button back to Fetch mode after the thread finishes
        self.set_fetch_button_state(False)
        
        handle_steam_fetch_finished(self, failed_titles, self.parent, was_canceled)
    
    def update_steam_reviews(self):
        self.start_steam_fetch(update_reviews_only=True)
    
    def fetch_for_new_games(self, new_games_dict):
        self.start_steam_fetch(specific_games=new_games_dict)
    
    def fetch_for_edited_games(self, modified_games_dict):
        self.start_steam_fetch(specific_games=modified_games_dict)

class SteamGameFetcher(QThread):
    progress_signal = Signal(str, str, str, dict, str)
    finished_signal = Signal(list)
    update_text_signal = Signal(str)
    
    REQUEST_TIMEOUT = 10
    
    def __init__(self, games_dict, icons_folder, update_reviews_only=False, batch_mode=False):
        super().__init__()
        self.games_dict = games_dict
        self.icons_folder = icons_folder
        self.running = True
        self.failed_titles = []
        self.update_reviews_only = update_reviews_only
        self.batch_mode = batch_mode

    def stop(self):
        self.running = False

    def run(self):
        Path(self.icons_folder).mkdir(parents=True, exist_ok=True)
        
        total_games = len(self.games_dict)
        current_game = 0
        
        for game_id, game_data in self.games_dict.items():
            if not self.running:
                self.update_text_signal.emit("Fetch operation canceled!")
                break

            current_game += 1
            title = game_data.get("title", "Unknown")
            self.update_text_signal.emit(f"Fetching ({current_game}/{total_games}):\n{title}")

            try:
                if self.update_reviews_only:
                    handled, already_failed = self._process_reviews_only(game_id, game_data)
                    if handled:
                        continue
                    if already_failed:
                        # Already added to failed_titles, skip adding again
                        continue
                    
                app_id, need_title_search = self._get_valid_app_id(game_data)
                
                if need_title_search:
                    self._search_by_title(game_id, game_data)
                else:
                    icon_path = game_data.get("icon_path", "")
                    icon_missing = not icon_path or not os.path.exists(icon_path)
                    review_missing = "review_data" not in game_data
                    developer_missing = "developer" not in game_data
                    
                    if icon_missing or review_missing or developer_missing:
                        new_icon_path = ""
                        if icon_missing:
                            new_icon_path = self.fetch_game_icon(app_id) or ""
                        
                        developer = ""
                        if developer_missing:
                            developer = self.fetch_game_developer(app_id) or ""
                        
                        if review_missing or (icon_missing and new_icon_path):
                            review_data = self.fetch_steam_reviews(app_id) or {}
                            self.progress_signal.emit(game_id, app_id, new_icon_path, review_data, developer)
                        elif (icon_missing and new_icon_path) or developer_missing:
                            self.progress_signal.emit(game_id, app_id, new_icon_path, {}, developer)
                    
            except Exception as e:
                logging.error(f" fetching data for {title}: {e}")
                # Only add to failed_titles if not already present
                if title not in self.failed_titles:
                    self.failed_titles.append(title)

        self.finished_signal.emit(self.failed_titles)
    
    def _process_reviews_only(self, game_id, game_data):
        app_id = game_data.get("app_id", "").strip()
        if app_id:
            review_data = self.fetch_steam_reviews(app_id)
            if review_data:
                self.progress_signal.emit(game_id, app_id, game_data.get("icon_path", ""), review_data, "")
                return True, False  # handled, not failed
            else:
                if game_data["title"] not in self.failed_titles:
                    self.failed_titles.append(game_data["title"])
                return False, True  # not handled, already failed
        else:
            if game_data["title"] not in self.failed_titles:
                self.failed_titles.append(game_data["title"])
            return False, True  # not handled, already failed
        
    def _get_valid_app_id(self, game_data):
        app_id = game_data.get("app_id", "").strip()
        if not app_id:
            return None, True
            
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(url, timeout=self.REQUEST_TIMEOUT)
            data = response.json()
            
            if app_id not in data or not data[app_id]["success"]:
                return None, True
                
            old_app_id = game_data.get("_previous_app_id", "")
            game_data["_previous_app_id"] = app_id
            
            if old_app_id and old_app_id != app_id and "review_data" in game_data:
                game_data.pop("review_data", None)
                
            return app_id, False
            
        except Exception as e:
            logging.error(f" validating app_id {app_id}: {e}")
            return None, True
    
    def _search_by_title(self, game_id, game_data):
        try:
            title = game_data["title"]
            search_url = f"https://store.steampowered.com/api/storesearch/?term={title}&l=english&cc=US"
            response = requests.get(search_url, timeout=self.REQUEST_TIMEOUT)
            data = response.json()

            if data.get("total", 0) > 0:
                items = data["items"]
                # Try to find the best match
                # 1. Exact match (case-insensitive)
                exact_matches = [item for item in items if item["name"].strip().lower() == title.strip().lower()]
                if exact_matches:
                    best_item = exact_matches[0]
                else:
                    # 2. Closest match using difflib
                    names = [item["name"] for item in items]
                    close_matches = difflib.get_close_matches(title, names, n=1, cutoff=0.7)
                    if close_matches:
                        best_item = next(item for item in items if item["name"] == close_matches[0])
                    else:
                        # 3. Fallback to first result
                        best_item = items[0]

                app_id = str(best_item["id"])
                icon_path = self.fetch_game_icon(app_id) or ""
                review_data = self.fetch_steam_reviews(app_id) or {}
                developer = self.fetch_game_developer(app_id) or ""
                self.progress_signal.emit(game_id, app_id, icon_path, review_data, developer)
            else:
                self.failed_titles.append(title)
        except Exception as e:
            logging.error(f" searching for title {game_data['title']}: {e}")
            self.failed_titles.append(game_data['title'])

    def fetch_game_icon(self, app_id):
        if not app_id or app_id.strip() == "":
            return None
            
        try:
            details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(details_url, timeout=self.REQUEST_TIMEOUT)
            details = response.json()
            
            if app_id in details and details[app_id]["success"]:
                icon_url = details[app_id]["data"]["header_image"]
                icon_path = os.path.join(self.icons_folder, f"{app_id}.jpg")
                
                icon_response = requests.get(icon_url, timeout=self.REQUEST_TIMEOUT)
                with open(icon_path, 'wb') as f:
                    f.write(icon_response.content)
                
                return icon_path
        except Exception as e:
            logging.error(f" fetching icon for app_id {app_id}: {e}")
        
        return None
        
    def fetch_steam_reviews(self, app_id):
        try:
            api_url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&purchase_type=all&language=all&review_type=all&filter_by=summary"
            api_response = requests.get(api_url, timeout=self.REQUEST_TIMEOUT)
            
            if api_response.status_code == 200:
                api_data = api_response.json()
                
                if api_data.get('success') == 1 and 'query_summary' in api_data:
                    summary = api_data['query_summary']
                    review_count = summary.get('total_reviews', 0)
                    rating_text = summary.get('review_score_desc', '')
                    
                    if rating_text:
                        return {
                            'rating_text': rating_text,
                            'review_count': review_count
                        }
            
            url = f"https://store.steampowered.com/app/{app_id}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if soup.select('.agegate_text_container, .agegate_birthday_selector, #app_agegate'):
                session = bypass_age_gate(app_id)
                response = session.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if soup.select('.agegate_text_container, .agegate_birthday_selector, #app_agegate'):
                    return {
                        'rating_text': 'Age Restricted (Unable to Bypass)',
                        'review_count': None,
                        'age_restricted': True
                    }
            
            if response.status_code != 200:
                return None
            
            review_summary_divs = soup.select('div.user_reviews_summary_row')
            if not review_summary_divs:
                review_summary_divs = soup.select('.game_review_summary')
                if not review_summary_divs:
                    return None
            
            all_reviews_div = None
            for div in review_summary_divs:
                if hasattr(div, 'text') and 'All Reviews' in div.text:
                    all_reviews_div = div
                    break
                if hasattr(div, 'get') and div.get('data-tooltip-html'):
                    all_reviews_div = div
                    break
            
            if not all_reviews_div:
                if len(review_summary_divs) > 1:
                    all_reviews_div = review_summary_divs[1]
                elif review_summary_divs:
                    all_reviews_div = review_summary_divs[0]
                else:
                    return None
            
            review_text = all_reviews_div
            
            if hasattr(all_reviews_div, 'select_one'):
                summary_span = all_reviews_div.select_one('span.game_review_summary')
                if summary_span:
                    review_text = summary_span
            
            if hasattr(review_text, 'text'):
                rating_text = review_text.text.strip()
            else:
                rating_text = str(review_text).strip()
            
            tooltip_html = None
            if hasattr(review_text, 'get') and review_text.get('data-tooltip-html'):
                tooltip_html = review_text.get('data-tooltip-html')
            
            if not tooltip_html and hasattr(all_reviews_div, 'select_one'):
                tooltip_elements = all_reviews_div.select('[data-tooltip-html]')
                if tooltip_elements:
                    tooltip_html = tooltip_elements[0].get('data-tooltip-html')
            
            if not tooltip_html:
                review_stats = soup.select('.user_reviews_count')
                for stat in review_stats:
                    if hasattr(stat, 'text') and "reviews" in stat.text.lower():
                        tooltip_html = stat.text
            
            count = None
            
            if tooltip_html:
                count_patterns = [
                    r'the ([0-9,]+) user reviews',
                    r'([0-9,]+) reviews',
                    r'([0-9,.]+) user reviews',
                    r'of the ([0-9,]+) user',
                    r'based on ([0-9,]+)'
                ]
                
                for pattern in count_patterns:
                    match = re.search(pattern, tooltip_html)
                    if match:
                        try:
                            count_str = match.group(1).replace(',', '').replace('.', '')
                            count = int(count_str)
                            break
                        except ValueError:
                            continue
            
            if count is None:
                count_elements = soup.select('.user_reviews_count')
                for element in count_elements:
                    text = element.text if hasattr(element, 'text') else str(element)
                    match = re.search(r'([0-9,]+) reviews', text, re.IGNORECASE)
                    if match:
                        try:
                            count = int(match.group(1).replace(',', ''))
                            break
                        except ValueError:
                            continue
            
            return {
                'rating_text': rating_text,
                'review_count': count
            }
                
        except Exception as e:
            logging.error(f" fetching reviews for app_id {app_id}: {e}")
            
        return None

    def fetch_game_developer(self, app_id):
        if not app_id or app_id.strip() == "":
            return None
            
        try:
            details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(details_url, timeout=self.REQUEST_TIMEOUT)
            details = response.json()
            
            if app_id in details and details[app_id]["success"]:
                developers = details[app_id]["data"].get("developers", [])
                if developers:
                    return ", ".join(developers)
            
            url = f"https://store.steampowered.com/app/{app_id}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                dev_div = soup.select_one('.dev_row .summary')
                if dev_div:
                    return dev_div.text.strip()
                    
        except Exception as e:
            logging.error(f" fetching developer for app_id {app_id}: {e}")
        
        return None

def bypass_age_gate(app_id):
    session = requests.Session()
    
    session.cookies.set('birthtime', '-473392799')
    session.cookies.set('mature_content', '1')
    
    data = {
        'snr': '1_agecheck_agecheck__age-gate',
        'ageDay': '1',
        'ageMonth': '1',
        'ageYear': '1970'
    }
    
    verify_url = f'https://store.steampowered.com/agecheckset/app/{app_id}/'
    session.post(verify_url, data=data)
    
    return session

def get_rating_color(rating_text, percentage=None):
    if not rating_text:
        return "#808080"
        
    rating_text = rating_text.lower()
    
    if rating_text == "age restricted":
        return "#e07000"
        
    elif 'overwhelmingly positive' in rating_text: return "#35d450"
    elif 'very positive' in rating_text: return "#35d48c"
    elif 'positive' in rating_text: return "#1a9fff"
    elif 'mostly positive' in rating_text: return "#35d4bf"
    elif 'mixed' in rating_text: return "#b9a074"
    else: return "#f55c5c"

def format_rating_text(review_data):
    if not review_data:
        return "N/A"
        
    rating_text = review_data.get('rating_text', 'N/A')
    
    if review_data.get('age_restricted', False):
        return rating_text
    
    review_count = review_data.get('review_count')
    if review_count:
        return f"{rating_text} ({review_count:,})"
    
    return rating_text

def open_steam_store(app_id):
    webbrowser.open(f"https://store.steampowered.com/app/{app_id}/")

def handle_browser_open(games_data, selected_items, row_to_unique_id, parent=None):
    opened_apps = set()
    missing_app_ids = []
    
    for item in selected_items:
        row = item.row()
        unique_id = row_to_unique_id[row]
        game_data = games_data[unique_id]
        
        app_id = game_data.get("app_id", "").strip()
        if app_id:
            if app_id not in opened_apps:
                open_steam_store(app_id)
                opened_apps.add(app_id)
        else:
            missing_app_ids.append(game_data["title"])
    
    if missing_app_ids:
        # Use the scrollable dialog instead of QMessageBox
        dialog, _ = create_scrollable_message_dialog(
            parent=parent,
            title="Missing AppID",
            message="Couldn't find AppID for these games:",
            content=missing_app_ids,
            footer_text="Try using 'Fetch Steam Data' to get the AppIDs automatically."
        )
        dialog.exec()

def handle_steam_fetch_finished(fetch_manager, failed_titles, parent=None, was_canceled=False):
    """Handle completion of Steam fetch operation"""
    fetch_manager.update_status_text("")
    
    message_title = "Fetch Results"
    message = "Steam Data Fetch Results:"
    footer_text = None
    
    if was_canceled:
        message_title = "Fetch Canceled"
        message = "Steam Data Fetch Results:"
        footer_text = "Fetch operation was canceled.\nPartial data has been applied to your games."
    
    if failed_titles:
        if was_canceled:
            # Just show the failed titles in the scrollable area
            game_list = failed_titles
            footer_text = "Fetch operation was canceled.\nPartial data has been applied to your games."
        else:
            # Just show the failed titles in the scrollable area
            game_list = failed_titles
            footer_text = "Don't worry! You can still add the AppID manually and try again."
        
        # Use the scrollable dialog with footer text
        dialog, _ = create_scrollable_message_dialog(
            parent=parent,
            title=message_title,
            message="Failed to fetch data for these games:",
            content=game_list,
            footer_text=footer_text
        )
        dialog.exec()
    elif was_canceled:
        # Just show the canceled message
        dialog, _ = create_scrollable_message_dialog(
            parent=parent,
            title=message_title,
            message="Steam Data Fetch Results:",
            content=["No games failed to process."],
            footer_text="Fetch operation was canceled.\nPartial data has been applied to your games."
        )
        dialog.exec()