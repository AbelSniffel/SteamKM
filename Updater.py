# Updater.py
import requests
import os
import sys
import logging
import tempfile
import platform
import subprocess
from time import time
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QProgressBar, QTextEdit, QApplication, QGroupBox, QHBoxLayout, QCheckBox
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage
from Version import CURRENT_BUILD
from Config import ConfigManager, DEFAULT_BRANCH, VERTICAL_SPACING, HORIZONTAL_SPACING, ICON_BUTTON_WIDTH, TITLE_HEIGHT
from packaging.version import parse
from Icons import REFRESH_ICON
from Themes import Theme
from UI_Handler import apply_merged_edges

logging.basicConfig(level=logging.DEBUG)

GITHUB_URL = "https://api.github.com/repos/AbelSniffel/SteamKM/releases"
CHANGELOG_URL = "https://raw.githubusercontent.com/AbelSniffel/SteamKM/main/CHANGELOG.md"
FORCE_DEV_BRANCH_VISIBLE = False # Set to True to force show dev branch without having a github token (aka a public build)
RUNNING_FROM_SOURCE = not getattr(sys, 'frozen', False)

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'SteamKM_DevTools'))
    from github_token import GITHUB_TOKEN  # type: ignore
except ImportError:
    GITHUB_TOKEN = None

def github_request(url):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp

def get_releases():
    return github_request(GITHUB_URL).json()

def filter_versions(releases, branch):
    if branch == "release":
        return [r["tag_name"] for r in releases if "-" not in r["tag_name"]]
    return [r["tag_name"] for r in releases if f"-{branch}" in r["tag_name"].lower()]

def check_for_updates(config=None):
    config_manager = ConfigManager()
    selected_branch = config_manager.get("selected_branch")
    try:
        releases = get_releases()
        versions = filter_versions(releases, selected_branch.lower())
        if not versions:
            return CURRENT_BUILD
        latest_version = versions[0]
        return latest_version if parse(latest_version) > parse(CURRENT_BUILD) else CURRENT_BUILD
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
        QMessageBox.critical(None, "Update Error", str(e))
        return CURRENT_BUILD

def download_update(latest_version, progress_callback):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    temp_dir = os.path.join(tempfile.gettempdir(), "SteamKM_Update")
    os.makedirs(temp_dir, exist_ok=True)
    try:
        # Find asset in all releases
        releases = get_releases()
        for release in releases:
            if release["tag_name"] == latest_version:
                for asset in release.get("assets", []):
                    if asset.get("name") == "SteamKM.exe":
                        download_url = asset.get("browser_download_url")
                        file_size = asset.get("size", 0)
                        if not file_size:
                            raise Exception("Failed to get file size.")
                        progress_callback(0, file_size)
                        current_executable = os.path.realpath(
                            sys.executable if not RUNNING_FROM_SOURCE else os.path.join(os.path.dirname(__file__), "SteamKM.exe")
                        )
                        temp_update_path = os.path.join(temp_dir, f"SteamKM_{latest_version}.exe")
                        with open(temp_update_path, 'wb') as f, requests.get(download_url, headers=headers, stream=True) as r:
                            r.raise_for_status()
                            downloaded_size = 0
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    progress_callback(downloaded_size, file_size)
                        create_updater_script(current_executable, temp_update_path, latest_version)
                        return True
        raise Exception(f"No matching asset found for version {latest_version}")
    except Exception as e:
        logging.error(f"Failed to download update: {e}")
        raise e

def create_updater_script(current_executable, update_file, version):
    if RUNNING_FROM_SOURCE:
        return
    is_windows = platform.system() == 'Windows'
    temp_dir = tempfile.gettempdir()
    if is_windows:
        updater_path = os.path.join(temp_dir, "SteamKM_updater.bat")
        # Batch file for Windows
        updater_script = f"""@echo off
timeout /t 1 >nul
setlocal
set EXE="{current_executable}"
set UPDATE="{update_file}"
set BACKUP="%EXE%.bak"
if exist %BACKUP% del /f /q %BACKUP%
copy /y %EXE% %BACKUP%
copy /y %UPDATE% %EXE%
start "" %EXE%
endlocal
"""
        with open(updater_path, 'w') as f:
            f.write(updater_script)
    else:
        updater_path = os.path.join(temp_dir, "SteamKM_updater.py")
        updater_script = f'''
import os
import sys
import time
import shutil
import subprocess

def perform_update():
    current_exe = r"{current_executable}"
    update_file = r"{update_file}"
    backup_path = current_exe + ".bak"
    time.sleep(1)
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy2(current_exe, backup_path)
    except Exception as e:
        print(f"Backup failed: {{e}}")
        return False
    try:
        shutil.copy2(update_file, current_exe)
        os.chmod(current_exe, 0o755)
        subprocess.Popen([current_exe])
        return True
    except Exception as e:
        print(f"Update failed: {{e}}")
        try:
            shutil.copy2(backup_path, current_exe)
        except:
            pass
        return False

if __name__ == "__main__":
    perform_update()
'''
        with open(updater_path, 'w') as f:
            f.write(updater_script)
        os.chmod(updater_path, 0o755)

def start_updater():
    if RUNNING_FROM_SOURCE:
        QMessageBox.information(None, "Development Mode",
            "Update simulation complete. In production, the updater would now restart the application.")
        return True
    temp_dir = tempfile.gettempdir()
    is_windows = platform.system() == 'Windows'
    if is_windows:
        updater_path = os.path.join(temp_dir, "SteamKM_updater.bat")
    else:
        updater_path = os.path.join(temp_dir, "SteamKM_updater.py")
    if not os.path.exists(updater_path):
        logging.error("Updater script not found!")
        return False
    try:
        if is_windows:
            subprocess.Popen([updater_path], shell=True)
        else:
            subprocess.Popen([sys.executable, updater_path])
        return True
    except Exception as e:
        logging.error(f"Failed to start updater: {e}")
        return False

class AutomaticUpdateCheck(QThread):
    update_status_signal = Signal(str, bool)
    def __init__(self, parent=None, cache=None):
        super().__init__(parent)
        self.cache = cache if cache is not None else {}
        self.config_manager = ConfigManager()
        self.selected_branch = self.config_manager.get("selected_branch", DEFAULT_BRANCH)
        self.cleanup_old_files()
    def run(self):
        self.check_updates()
    def check_updates(self):
        self.update_status_signal.emit("Checking Updates", True)
        try:
            branch = self.selected_branch.lower()
            cache_key = f"releases_{branch}"
            try:
                releases = get_releases()
                self.cache[cache_key] = releases
                versions = filter_versions(releases, branch)
                latest_version = versions[0] if versions else CURRENT_BUILD
                if "changelog" not in self.cache:
                    try:
                        changelog_response = requests.get(CHANGELOG_URL)
                        if changelog_response.status_code == 200:
                            self.cache["changelog"] = changelog_response.text
                    except Exception as e:
                        logging.error(f"Failed to fetch changelog: {e}")
                if parse(latest_version) > parse(CURRENT_BUILD):
                    self.update_status_signal.emit(f"Update Available: {latest_version}", True)
                else:
                    self.update_status_signal.emit("Up to date", True)
            except Exception as e:
                logging.error(f"Error fetching releases: {e}")
                latest_version = check_for_updates()
                if parse(latest_version) > parse(CURRENT_BUILD):
                    self.update_status_signal.emit(f"Update Available: {latest_version}", True)
                else:
                    self.update_status_signal.emit("Up to date", True)
        except Exception as e:
            logging.error(f"Update Check Error: {e}")
            self.update_status_signal.emit("Failed Update Check", True)
    def cleanup_old_files(self):
        temp_dir = os.path.join(tempfile.gettempdir(), "SteamKM_Update")
        if os.path.exists(temp_dir):
            try:
                cutoff_time = time() - (7 * 86400)
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
            except Exception as e:
                logging.error(f"Failed to clean up old update files: {e}")

class DownloadThread(QThread):
    progress_signal = Signal(int, int, float)
    finished_signal = Signal(bool)
    error_signal = Signal(str)
    def __init__(self, latest_version):
        super().__init__()
        self.latest_version = latest_version
        self.start_time = time()
        self.is_cancelled = False
    def run(self):
        try:
            self.finished_signal.emit(download_update(self.latest_version, self.update_progress))
        except Exception as e:
            self.error_signal.emit(str(e))
    def update_progress(self, downloaded, total):
        if self.is_cancelled:
            return
        elapsed_time = time() - self.start_time
        download_speed = downloaded / elapsed_time if elapsed_time > 0 else 0
        estimated_time = (total - downloaded) / download_speed if download_speed > 0 else 0
        display_downloaded = max(downloaded, total * 0.05) if downloaded > 0 else 0
        self.progress_signal.emit(display_downloaded, total, estimated_time)

class ChangelogFetchThread(QThread):
    """Thread for fetching changelog in the background to keep UI responsive"""
    finished_signal = Signal(str)
    error_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            response = requests.get(CHANGELOG_URL)
            if response.status_code == 200:
                self.finished_signal.emit(response.text)
            else:
                self.error_signal.emit(f"Failed to fetch changelog: HTTP {response.status_code}")
        except Exception as e:
            self.error_signal.emit(f"Failed to fetch changelog: {e}")

class UpdateDialog(QDialog):
    update_signal = Signal(str, bool)
    def __init__(self, parent=None, cache=None):
        super().__init__(parent)
        self.setWindowTitle("Update Menu")
        self.resize(500, 650)
        self.current_version = CURRENT_BUILD
        self.latest_version = None
        self.download_thread = None
        self.initializing = True
        self.config_manager = ConfigManager()
        self.auto_update_check = self.config_manager.get("auto_update_check", True)
        self.cache = cache if cache is not None else {}
        self.changelog_fetch_thread = None  # Store the fetch thread instance
        # Get merge_edges setting from parent if available
        self.merge_edges = getattr(self.parent(), "merge_edges", False) if self.parent() else False
        self.setup_ui()
        self.load_saved_branch()
        self.initializing = False
        if "changelog" in self.cache:
            self.handle_changelog_response(self.cache["changelog"])
        else:
            self.changelog_text.setPlainText("Fetching changelog...")
            QTimer.singleShot(100, self.fetch_changelog)
        self.refresh_releases_ui()
        # Apply merged edges style
        #self.apply_merged_edges_style() # Don't like the look of it, disabled for now
        
    def load_saved_branch(self):
        saved_branch = self.config_manager.get("selected_branch", DEFAULT_BRANCH)
        idx = self.branch_combo.findText(saved_branch.capitalize())
        if idx >= 0:
            self.branch_combo.setCurrentIndex(idx)
    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(self, "Confirm Close",
                "Download is in progress. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cancel_download()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    def set_pending_update_ui(self):
        self.update_menu_label.setText("Install pending, please close the program")
        for w in [self.check_updates_button, self.download_button, self.version_combo, self.cancel_button, self.progress_bar]:
            w.setVisible(False)
        self.close_button.setVisible(True)
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        version_group, version_layout = QGroupBox(), QHBoxLayout()
        version_group.setLayout(version_layout)
        version_layout.addWidget(QLabel(f"Current Version: <b>{self.current_version}</b>"))
        version_layout.addStretch()
        version_layout.addWidget(QLabel("Select Branch:"), alignment=Qt.AlignRight)
        self.branch_combo = QComboBox()
        branches = ["Release", "Beta", "Dev"] if GITHUB_TOKEN or FORCE_DEV_BRANCH_VISIBLE else ["Release", "Beta"]
        self.branch_combo.addItems(branches)
        self.branch_combo.currentIndexChanged.connect(self.on_branch_changed)
        version_layout.addWidget(self.branch_combo)
        check_update_group, check_update_layout = QGroupBox(), QVBoxLayout()
        check_update_group.setLayout(check_update_layout)
        self.update_menu_label = QLabel("Checking for updates...", alignment=Qt.AlignCenter)
        check_update_layout.addWidget(self.update_menu_label)
        button_layout = QHBoxLayout()
        self.check_updates_button = QPushButton("Check", fixedWidth=75)
        self.check_updates_button.clicked.connect(self.manual_update_check)
        button_layout.addWidget(self.check_updates_button)
        self.download_button = QPushButton("Download", visible=False)
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        self.version_combo = QComboBox(visible=False)
        self.version_combo.currentIndexChanged.connect(self.on_version_selected)
        button_layout.addWidget(self.version_combo)
        self.cancel_button = QPushButton("Cancel", fixedWidth=75, visible=False)
        self.cancel_button.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_button)
        self.close_button = QPushButton("Close SteamKM", fixedWidth=120)
        self.close_button.clicked.connect(QApplication.quit)
        self.close_button.setVisible(False)
        button_layout.addWidget(self.close_button)
        check_update_layout.addLayout(button_layout)
        self.progress_bar = QProgressBar(visible=False)
        check_update_layout.addWidget(self.progress_bar)
        footer_layout = QHBoxLayout()
        self.auto_update_checkbox = QCheckBox("Enable Automatic Update Check")
        self.auto_update_checkbox.setChecked(self.auto_update_check)
        self.auto_update_checkbox.stateChanged.connect(self.toggle_auto_update_check)
        footer_layout.addWidget(self.auto_update_checkbox)
        footer_layout.addWidget(QLabel("SteamKM by Stick-bon"), alignment=Qt.AlignRight)
        changelog_group, changelog_layout = QGroupBox(), QVBoxLayout()
        changelog_group.setLayout(changelog_layout)
        # --- Add label and refresh button in a horizontal layout ---
        changelog_header_layout = QHBoxLayout()
        changelog_header_layout.setSpacing(HORIZONTAL_SPACING)  # Add default spacing initially
        # Title for "Changelog"
        self.changelog_label = QLabel("Changelog", alignment=Qt.AlignCenter, fixedHeight=TITLE_HEIGHT)
        self.changelog_label.setObjectName("Title")
        changelog_header_layout.addWidget(self.changelog_label)
        # Add refresh button to the right of the label
        self.changelog_refresh_button = QPushButton()
        self.changelog_refresh_button.setFixedSize(ICON_BUTTON_WIDTH, TITLE_HEIGHT)
        self.set_refresh_icon()
        self.changelog_refresh_button.setToolTip("Refresh changelog")
        self.changelog_refresh_button.setCursor(Qt.PointingHandCursor)
        self.changelog_refresh_button.setFlat(True)
        self.changelog_refresh_button.clicked.connect(self.force_fetch_changelog)
        changelog_header_layout.addWidget(self.changelog_refresh_button)
        changelog_layout.addLayout(changelog_header_layout)
        # --- End header row ---
        self.changelog_text = QTextEdit(readOnly=True, objectName="ChangeLog")
        changelog_layout.addWidget(self.changelog_text)
        main_layout.addWidget(version_group)
        main_layout.addWidget(check_update_group)
        main_layout.addWidget(changelog_group)
        main_layout.setSpacing(VERTICAL_SPACING)
        main_layout.addLayout(footer_layout)
    def set_refresh_icon(self):
        """Set the refresh icon for the changelog refresh button using the current theme color."""
        # Use parent's theme if available, else fallback to dark
        theme_name = getattr(self.parent(), "theme", "dark") if self.parent() else "dark"
        using_custom_colors = getattr(self.parent(), "using_custom_colors", False) if self.parent() else False
        custom_colors = getattr(self.parent(), "custom_colors", None) if self.parent() else None
        theme = Theme(theme_name, custom_colors if using_custom_colors else None)
        color = theme.get_icon_color()
        icon_data = REFRESH_ICON.replace("{{COLOR}}", color)
        self.changelog_refresh_button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon_data.encode()))))
    def toggle_auto_update_check(self):
        self.auto_update_check = self.auto_update_checkbox.isChecked()
        self.config_manager.set("auto_update_check", self.auto_update_check)
        if self.auto_update_check:
            self.update_menu_label.setText("Searching for updates...")
            self.update_signal.emit("Checking Updates", True)
            self.refresh_releases_ui()
        else:
            # Show cached update status if available, otherwise show disabled message
            branch = self.branch_combo.currentText().lower()
            cache_key = f"releases_{branch}"
            if cache_key in self.cache:
                self.handle_releases_response(self.cache[cache_key])
            else:
                self.update_menu_label.setText("Automatic update checks are disabled")
                self.check_updates_button.setVisible(True)
                self.version_combo.setVisible(False)
                self.download_button.setVisible(False)
    def on_branch_changed(self):
        if not self.initializing:
            if self.auto_update_check:
                self.update_menu_label.setText("Loading new branch...")
                self.update_signal.emit("Checking Branch", True)
            self.config_manager.set("selected_branch", self.branch_combo.currentText().lower())
            self.parent().selected_branch = self.config_manager.get("selected_branch")
            self.parent().show_update_message = self.config_manager.get("show_update_message", False)
            self.refresh_releases_ui()
    def manual_update_check(self):
        self.update_menu_label.setText("Searching for Updates...")
        self.update_signal.emit("Checking Updates", True)
        branch = self.branch_combo.currentText().lower()
        cache_key = f"releases_{branch}"
        if cache_key in self.cache:
            del self.cache[cache_key]
        self.changelog_text.setPlainText("Fetching changelog...")
        self.fetch_changelog()
        QTimer.singleShot(100, self.fetch_releases)
    def refresh_releases_ui(self):
        if self.config_manager.get("show_update_message", False):
            self.set_pending_update_ui()
            return
        branch = self.branch_combo.currentText().lower()
        cache_key = f"releases_{branch}"
        if cache_key in self.cache:
            self.handle_releases_response(self.cache[cache_key])
        elif self.auto_update_check:
            QTimer.singleShot(100, self.fetch_releases)
        else:
            # Show cached update status if available, otherwise show disabled message
            if cache_key in self.cache:
                self.handle_releases_response(self.cache[cache_key])
            else:
                self.update_menu_label.setText("Automatic update checks are disabled")
                self.check_updates_button.setVisible(True)
                self.version_combo.setVisible(False)
                self.download_button.setVisible(False)
    def fetch_releases(self):
        branch = self.branch_combo.currentText().lower()
        cache_key = f"releases_{branch}"
        if cache_key in self.cache:
            self.handle_releases_response(self.cache[cache_key])
        else:
            try:
                releases = get_releases()
                self.cache[cache_key] = releases
                self.handle_releases_response(releases)
            except Exception as e:
                self.update_menu_label.setText("Failed to check for updates. Please try again later.")
                self.update_signal.emit("Failed Update Check", True)
    def handle_releases_response(self, releases):
        branch = self.branch_combo.currentText().lower()
        versions = filter_versions(releases, branch)
        self.version_combo.setFixedWidth(75 if branch == "release" else 105)
        self.version_combo.clear()
        if versions:
            latest_version_for_branch = versions[0]
            self.version_combo.addItems(versions)
            self.version_combo.setVisible(True)
            self.download_button.setVisible(True)
            self.update_menu_label.setText("Select a version to download")
            # Emit update status for all cases
            if parse(latest_version_for_branch) > parse(self.current_version):
                self.update_signal.emit(f"Update Available: {latest_version_for_branch}", True)
            else:
                self.update_signal.emit("Up to date", True)
        else:
            self.update_menu_label.setText(f"No downloads available for {branch.capitalize()} branch")
            self.update_signal.emit("No downloads available", True)
            self.version_combo.setVisible(False)
            self.download_button.setVisible(False)
    def fetch_changelog(self):
        if "changelog" in self.cache:
            self.handle_changelog_response(self.cache["changelog"])
        else:
            self.changelog_text.setPlainText("Fetching changelog...")
            QApplication.processEvents()
            self.changelog_refresh_button.setEnabled(False)  # Disable refresh during fetch
            self.start_changelog_fetch()

    def start_changelog_fetch(self):
        """Start fetching changelog in a background thread"""
        # Clean up any existing thread
        if self.changelog_fetch_thread and self.changelog_fetch_thread.isRunning():
            self.changelog_fetch_thread.wait()
            
        # Create and configure new thread
        self.changelog_fetch_thread = ChangelogFetchThread()
        self.changelog_fetch_thread.finished_signal.connect(self.handle_changelog_fetch_finished)
        self.changelog_fetch_thread.error_signal.connect(self.handle_changelog_fetch_error)
        
        # Start the thread
        self.changelog_fetch_thread.start()
    
    def handle_changelog_fetch_finished(self, changelog_text):
        """Handle successful changelog fetch"""
        self.cache["changelog"] = changelog_text
        self.handle_changelog_response(changelog_text)
        
        # Clean up thread when done
        if self.changelog_fetch_thread:
            self.changelog_fetch_thread.deleteLater()
            self.changelog_fetch_thread = None
        self.changelog_refresh_button.setEnabled(True)  # Re-enable refresh

    def handle_changelog_fetch_error(self, error_message):
        """Handle changelog fetch error"""
        self.changelog_text.setPlainText(error_message)
        
        # Clean up thread when done
        if self.changelog_fetch_thread:
            self.changelog_fetch_thread.deleteLater()
            self.changelog_fetch_thread = None
        self.changelog_refresh_button.setEnabled(True)  # Re-enable refresh

    def force_fetch_changelog(self):
        """Force fetch the changelog from remote and update UI."""
        if not self.changelog_refresh_button.isEnabled():
            return  # Prevent spamming while fetch is in progress
        self.changelog_text.setPlainText("Fetching changelog...")
        # Force the UI to update immediately
        QApplication.processEvents()
        
        # Remove cached changelog if present
        if "changelog" in self.cache:
            del self.cache["changelog"]
        
        # Start fetch in background thread
        self.changelog_refresh_button.setEnabled(False)  # Disable refresh during fetch
        self.start_changelog_fetch()
    
    def handle_changelog_response(self, changelog_text):
        html_lines = []
        for line in changelog_text.split('\n'):
            if line.startswith("0."):
                html_lines.append(f"<h3>{line}</h3>")
            elif line.startswith("+"):
                html_lines.append(f"<p><span style='color: green;'><b>+</b></span> {line[2:]}</p>")
            elif line.startswith("*"):
                html_lines.append(f"<p><span style='color: #ffa500;'><b>*</b></span> {line[2:]}</p>")
            elif line.startswith("-"):
                html_lines.append(f"<p><span style='color: red;'><b>-</b></span> {line[2:]}</p>")
            else:
                html_lines.append(f"<p><b>{line}</b></p>")
        self.changelog_text.setHtml("\n".join(html_lines))
    def on_version_selected(self, index):
        selected_version_text = self.version_combo.itemText(index)
        self.download_button.setText("Update")
        if not selected_version_text:
            self.download_button.setEnabled(False)
            return
        if parse(selected_version_text) < parse(self.current_version):
            self.download_button.setText("Rollback")
        elif parse(selected_version_text) == self.current_version:
            self.download_button.setText("Already Installed")
        self.download_button.setEnabled(selected_version_text != self.current_version)
    def start_download(self):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A download is already in progress.")
            return
        if selected_version := self.version_combo.currentText():
            self.latest_version = selected_version
            self.update_menu_label.setText(f"Preparing to download {self.latest_version}...")
            for w in [self.check_updates_button, self.version_combo, self.download_button]:
                w.setVisible(False)
            self.cancel_button.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.download_thread = DownloadThread(self.latest_version)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)
            self.download_thread.error_signal.connect(self.download_error)
            self.download_thread.start()
        else:
            QMessageBox.warning(self, "Update Error", "No version selected for download.")
    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.update_menu_label.setText("Download cancelled.")
            self.download_thread.is_cancelled = True
            self.download_thread.progress_signal.disconnect()
            self.download_thread.finished_signal.disconnect()
            self.download_thread.error_signal.disconnect()
            self.download_thread.terminate()
            self.download_thread.wait()
            self.download_thread = None
            for w in [self.check_updates_button, self.version_combo, self.download_button]:
                w.setVisible(True)
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
        else:
            QMessageBox.warning(self, "Download Not Running", "No download is currently running.")
    def download_error(self, error_message):
        for w in [self.check_updates_button, self.version_combo, self.download_button]:
            w.setVisible(True)
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.update_menu_label.setText("Download Error")
        QMessageBox.critical(self, "Download Error", error_message)
    def update_progress(self, downloaded, total, estimated_time):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(downloaded)
        if estimated_time > 0:
            self.update_menu_label.setText(
                f"Downloaded: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB (Estimated Time: {int(estimated_time)} seconds)"
            )
        else:
            self.update_menu_label.setText(f"Download Size: {total / (1024 * 1024):.2f} MB")
    def download_finished(self, success):
        if success:
            self.config_manager.set("show_update_message", True)
            self.close_button.setText("Restart SteamKM")
            self.close_button.clicked.disconnect(QApplication.quit)
            self.close_button.clicked.connect(self.perform_update)
            self.set_pending_update_ui()
            self.parent().show_update_message = self.config_manager.get("show_update_message", False)
        else:
            QMessageBox.warning(self, "Download Failed", f"Update {self.latest_version} failed to download.")
        self.download_thread.deleteLater()
        self.download_thread = None
    def perform_update(self):
        if start_updater():
            QApplication.quit()
        else:
            QMessageBox.critical(self, "Update Error",
                "Failed to start the update process. Please try again or download manually.")
    def apply_merged_edges_style(self):
        """Apply the styling for merged/separate edges based on current merge_edges setting"""
        # Find the changelog header layout
        changelog_header_layout = None
        for layout in self.findChildren(QHBoxLayout):
            if layout.indexOf(self.changelog_refresh_button) != -1:
                changelog_header_layout = layout
                break
        
        # Define widget pairs for merged edges styling
        widget_pairs = [
            (self.changelog_label, self.changelog_refresh_button, 
             changelog_header_layout, "Title-UnifiedUI", "FlatLeftEdge")
        ]
        
        # Apply the styling using the centralized function
        apply_merged_edges(widget_pairs, self.merge_edges)
        
        # Force style refresh for affected widgets
        for widget in [self.changelog_label, self.changelog_refresh_button]:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()