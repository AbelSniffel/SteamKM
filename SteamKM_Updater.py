# SteamKM_Updater.py
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox, QPushButton, QProgressBar, QTextEdit
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from SteamKM_Version import CURRENT_BUILD
from SteamKM_Themes import BUTTON_HEIGHT
from packaging.version import parse, InvalidVersion
from time import time
import requests
import os
import sys
import logging

# Debug logging
logging.basicConfig(level=logging.DEBUG)

try:
    from github_token import GITHUB_TOKEN # type: ignore
    logging.debug("GitHub token loaded successfully.")
except ImportError:
    GITHUB_TOKEN = None
    logging.debug("GitHub token not found. Using unauthenticated requests.")

def check_for_updates(silent=False, branch="Beta"):
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(f"https://api.github.com/repos/AbelSniffel/SteamKM/releases/latest", headers=headers)
        response.raise_for_status()
        latest_version = response.json().get("tag_name", "0.0.0")
        logging.debug(f"Latest version from GitHub: {latest_version}")
        
        if parse(latest_version) > parse(CURRENT_BUILD):
            logging.debug(f"New version available: {latest_version}")
            return latest_version
        else:
            logging.debug(f"No new version available. Current build: {CURRENT_BUILD}, Latest version: {latest_version}")
            return CURRENT_BUILD  # Ensure it returns CURRENT_BUILD if no new version is available
    except (requests.exceptions.RequestException, InvalidVersion) as e:
        logging.error(f"Error checking for updates: {e}")
        if not silent:
            QMessageBox.critical(None, "Update Error", str(e))
        return None

def download_update(latest_version, progress_callback, branch="Beta"):
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        release_url = f"https://api.github.com/repos/AbelSniffel/SteamKM/releases/tags/{latest_version}"
        response = requests.get(release_url, headers=headers)
        response.raise_for_status()
        assets = response.json().get("assets", [])
        
        for asset in assets:
            if asset.get("name") == "SteamKM.exe":
                download_url = asset.get("browser_download_url")
                # Get the path of the current executable
                script_path = os.path.realpath(sys.executable)
                update_path = script_path + ".new"
                
                # Get the total file size
                file_size = int(asset.get("size", 0))
                if file_size == 0:
                    raise Exception("Failed to get file size.")
                
                # Initialize progress callback
                progress_callback(0, file_size)
                
                with open(update_path, 'wb') as f:
                    with requests.get(download_url, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        downloaded_size = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                progress_callback(downloaded_size, file_size)
                
                backup_path = script_path + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(script_path, backup_path)
                
                os.rename(update_path, script_path)
                
                logging.info(f"Update to version {latest_version} successful.")
                return True  # Indicate success
        
        logging.error(f"No matching asset found for version {latest_version}")
        raise Exception("No matching asset found for version {latest_version}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download update: {e}")
        raise e
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e

class UpdateDialog(QDialog):
    def __init__(self, parent=None, current_version=CURRENT_BUILD):
        super().__init__(parent)
        self.setWindowTitle("Update Manager")
        self.resize(400, 200)
        self.current_version = current_version
        self.latest_version = None
        self.download_thread = None
        self.setup_ui()
        self.changelog_text.setPlainText("Getting changelog...")  # Default Changelog text
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_changelog)
        self.timer.setSingleShot(True)
        self.timer.start(100) # Start timer for changelog fetch

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Module 1: Version and Branch Selection
        version_group = QGroupBox()
        version_layout = QVBoxLayout()
        version_label = QLabel(f"Current Version: <b>{self.current_version}</b>")
        version_layout.addWidget(version_label)

        branch_layout = QHBoxLayout()
        branch_label = QLabel("Selected Branch:")
        self.branch_combo = QComboBox()
        self.branch_combo.addItems(["Beta"]) 
        self.branch_combo.setCurrentText("Beta")
        self.branch_combo.setFixedSize(80, BUTTON_HEIGHT)
        self.branch_combo.currentIndexChanged.connect(self.fetch_changelog) # Fetch changelog when branch changes
        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self.branch_combo)
        version_layout.addLayout(branch_layout)
        version_group.setLayout(version_layout)
        main_layout.addWidget(version_group)

        # Module 2: Check for Updates
        check_update_group = QGroupBox()
        check_update_layout = QVBoxLayout()

        self.check_updates_button = QPushButton("Search")
        self.check_updates_button.setFixedSize(65, BUTTON_HEIGHT)
        self.check_updates_button.clicked.connect(self.check_updates)

        self.update_available_layout = QVBoxLayout()
        self.update_available_layout.setAlignment(Qt.AlignCenter)
        self.update_available_layout.setSpacing(10)

        self.update_label = QLabel("Check for Available Updates")
        self.update_label.setAlignment(Qt.AlignCenter)
        self.update_available_layout.addWidget(self.update_label)

        self.download_button = QPushButton("Download and Install")
        self.download_button.setFixedSize(160, BUTTON_HEIGHT)
        self.download_button.clicked.connect(self.download_update)
        self.download_button.setVisible(False)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(65, BUTTON_HEIGHT)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setVisible(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.check_updates_button)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.cancel_button)
        self.update_available_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.update_available_layout.addWidget(self.progress_bar)
        check_update_layout.addLayout(self.update_available_layout)
        check_update_group.setLayout(check_update_layout)
        main_layout.addWidget(check_update_group)

        # Temporary Progress Bar for Testing
        temp_progress_bar = QProgressBar()
        temp_progress_bar.setRange(0, 100)
        temp_progress_bar.setValue(35) # Virtual Progress
        temp_progress_bar.setVisible(False) # Set to True for testing
        self.update_available_layout.addWidget(temp_progress_bar)

        # Module 3: Changelog
        changelog_group = QGroupBox()
        changelog_layout = QVBoxLayout()
        changelog_label = QLabel("Changelog:")
        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setFixedHeight(200)
        changelog_layout.addWidget(changelog_label)
        changelog_layout.addWidget(self.changelog_text)
        changelog_group.setLayout(changelog_layout)
        main_layout.addWidget(changelog_group)

        # Created By Label
        created_by_label = QLabel("SteamKM by Stick-bon")
        created_by_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(created_by_label, alignment=Qt.AlignRight)

        self.setLayout(main_layout)

    def fetch_changelog(self):
        branch = self.branch_combo.currentText()
        try:
            response = requests.get(f"https://raw.githubusercontent.com/AbelSniffel/SteamKM/{branch}/CHANGELOG.md")
            if response.status_code == 200:
                self.changelog_text.setPlainText(response.text)
            else:
                self.changelog_text.setPlainText("Failed to fetch changelog.")
        except Exception as e:
            self.changelog_text.setPlainText(f"Failed to fetch changelog: {e}")

    def check_updates(self):
        branch = self.branch_combo.currentText()
        self.latest_version = check_for_updates(silent=True)
        if self.latest_version is None:
            self.update_label.setText("Failed to check for updates. Please try again later.")
        elif self.latest_version == self.current_version:
            self.update_label.setText("You're already on the latest build")
        else:
            self.update_label.setText(f"New Version: <b>{self.latest_version}</b>")
            self.download_button.setText("Download and Install")
            self.download_button.setVisible(True)

    def download_update(self):
        if self.latest_version and self.latest_version != self.current_version:
            self.update_label.setText("Starting Download...")
            self.download_button.setVisible(False)
            self.check_updates_button.setVisible(False)
            self.cancel_button.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress initially

            # Create a worker thread for downloading
            self.download_thread = DownloadThread(self.latest_version)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)
            self.download_thread.error_signal.connect(self.download_error)
            self.download_thread.start()
        else:
            QMessageBox.warning(self, "Update Error", "No update to download.")

    def cancel_download(self):
        if self.download_thread is not None and self.download_thread.isRunning():
            self.update_label.setText("Download cancelled.")
            self.download_thread.terminate()
            self.download_thread.wait()
            self.download_thread = None
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.check_updates_button.setVisible(True)
            self.download_button.setVisible(True)
        else:
            QMessageBox.warning(self, "Download Not Running", "No download is currently running.")

    def update_progress(self, downloaded, total, estimated_time):
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(downloaded)
            if estimated_time > 0:
                self.update_label.setText(f"Downloaded: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB\nEstimated Time: {int(estimated_time)} seconds")
            else:
                self.update_label.setText(f"Download Size: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB")

    def download_finished(self, success):
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.download_button.setVisible(True)
        if success:
            QMessageBox.information(self, "Download Complete", f"Update {self.latest_version} downloaded successfully. Please restart the program.")
        else:
            QMessageBox.warning(self, "Download Failed", f"Failed to download update {self.latest_version}.")

    def download_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.check_updates_button.setVisible(True)
        self.download_button.setVisible(True)
        QMessageBox.critical(self, "Download Error", error_message)

class DownloadThread(QThread):
    progress_signal = Signal(int, int, float) # (downloaded, total, estimated_time)
    finished_signal = Signal(bool)  # (success)
    error_signal = Signal(str)  # (error_message)

    def __init__(self, latest_version, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.start_time = None

    def run(self):
        try:
            self.start_time = time()
            success = download_update(self.latest_version, self.update_progress)
            self.finished_signal.emit(success)
        except Exception as e:
            self.error_signal.emit(str(e))

    def update_progress(self, downloaded, total):
        elapsed_time = time() - self.start_time if self.start_time else 0
        if elapsed_time > 0 and downloaded > 0:
            download_speed = downloaded / elapsed_time # bytes per second
            remaining_bytes = total - downloaded
            estimated_time = remaining_bytes / download_speed if download_speed > 0 else 0
        else:
            estimated_time = 0
        self.progress_signal.emit(downloaded, total, estimated_time)