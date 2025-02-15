# SteamKM_Updater.py
import requests
import os
import sys
import logging
import subprocess
from time import time
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QProgressBar, QTextEdit, QApplication, QGroupBox, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from SteamKM_Version import CURRENT_BUILD
from SteamKM_Config import load_config, save_config, DEFAULT_BRANCH
from packaging.version import parse

GITHUB_LINK = "https://api.github.com/repos/AbelSniffel/SteamKM/releases"
logging.basicConfig(level=logging.DEBUG)
DEV_BRANCH_VISIBLE = False # For manually setting Dev branch visible without needing GITHUB_TOKEN

try:
    from github_token import GITHUB_TOKEN
    logging.debug("GitHub token loaded successfully.")
except ImportError:
    GITHUB_TOKEN = None
    logging.debug("GitHub token not found. Using unauthenticated requests.")

def check_for_updates(config=None):
    config = config or load_config()
    selected_branch = config.get("selected_branch", DEFAULT_BRANCH)
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        response = requests.get(f"{GITHUB_LINK}/latest", headers=headers)
        response.raise_for_status()
        latest_version = response.json().get("tag_name", "0.0.0")
        logging.debug(f"Latest version from GitHub: {latest_version}")
        
        if selected_branch.lower() == "release":
            # For Release branch, only consider versions without any suffix (e.g., "0.7.0")
            if "-" not in latest_version:
                return latest_version if parse(latest_version) > parse(CURRENT_BUILD) else CURRENT_BUILD
            else:
                return CURRENT_BUILD
        else:
            # For Beta/Dev, allow versions with suffixes (e.g., "0.7.0-beta")
            return latest_version if parse(latest_version) > parse(CURRENT_BUILD) else CURRENT_BUILD
            
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
        QMessageBox.critical(None, "Update Error", str(e))
        return CURRENT_BUILD

def download_update(latest_version, progress_callback):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        response = requests.get(f"{GITHUB_LINK}/tags/{latest_version}", headers=headers)
        response.raise_for_status()
        assets = response.json().get("assets", [])
        for asset in assets:
            if asset.get("name") == "SteamKM.exe":
                download_url = asset.get("browser_download_url")
                script_path = os.path.realpath(sys.executable)
                update_path = script_path + ".new"
                file_size = asset.get("size", 0)
                if not file_size:
                    raise Exception("Failed to get file size.")
                progress_callback(0, file_size)
                with open(update_path, 'wb') as f, requests.get(download_url, headers=headers, stream=True) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress_callback(r.raw.tell(), file_size)
                backup_path = script_path + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(script_path, backup_path)
                os.rename(update_path, script_path)
                return True
        raise Exception(f"No matching asset found for version {latest_version}")
    except Exception as e:
        logging.error(f"Failed to download update: {e}")
        raise e

class AutomaticUpdateCheck(QThread):
    update_status_signal = Signal(str, bool) # Signal to emit status text and visibility

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cleanup_old_files()

    def run(self):
        self.check_updates()

    def check_updates(self):
        self.update_status_signal.emit("Checking Updates", True)
        try:
            latest_version = check_for_updates()
            if parse(latest_version) > parse(CURRENT_BUILD):
                self.update_status_signal.emit("Update Available", True)
            else:
                self.update_status_signal.emit("Up to date", True)
        except Exception as e:
            logging.error(f"Update Check Error: {e}")
            self.update_status_signal.emit("Failed Update Check", True)

    def cleanup_old_files(self):
        for file_path in [os.path.realpath(sys.executable) + ".bak", os.path.realpath(sys.executable) + ".new"]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.error(f"Removed {file_path}")
                    self.update_status_signal.emit("Removed Old SteamKM", True)
                except Exception as e:
                    logging.error(f"Failed to remove {file_path}: {e}")

class DownloadThread(QThread):
    progress_signal = Signal(int, int, float)
    finished_signal = Signal(bool)
    error_signal = Signal(str)

    def __init__(self, latest_version):
        super().__init__()
        self.latest_version = latest_version
        self.start_time = time()

    def run(self):
        try:
            self.finished_signal.emit(download_update(self.latest_version, self.update_progress))
        except Exception as e:
            self.error_signal.emit(str(e))

    def update_progress(self, downloaded, total):
        elapsed_time = time() - self.start_time
        download_speed = downloaded / elapsed_time if elapsed_time > 0 else 0
        estimated_time = (total - downloaded) / download_speed if download_speed > 0 else 0
        self.progress_signal.emit(downloaded, total, estimated_time)

class UpdateDialog(QDialog):
    update_signal = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Menu")
        self.resize(500, 650)
        self.current_version = CURRENT_BUILD
        self.latest_version = None
        self.download_thread = None
        self.initializing = True
        self.setup_ui()

        self.config = load_config()
        self.load_saved_branch()
        self.initializing = False

        if self.config.get("show_update_message", False):
            self.set_pending_update_ui()
        else:
            QTimer.singleShot(100, self.fetch_releases)

    def load_saved_branch(self):
        saved_branch = self.config.get("selected_branch", DEFAULT_BRANCH)
        if (index := self.branch_combo.findText(saved_branch.capitalize())) >= 0:
            self.branch_combo.setCurrentIndex(index)

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(self, "Confirm Close",
                                         "Download is in progress. Are you sure you want to close?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.cancel_download()  # Force stop the download
                event.accept()  # Allow the dialog to close
            else:
                event.ignore()  # Prevent the dialog from closing
        else:
            event.accept()  # Allow the dialog to close if no download is running

    def set_pending_update_ui(self):
        self.update_menu_label.setText("Install pending, please close the program")
        self.check_updates_button.setVisible(False)
        self.download_button.setVisible(False)
        self.version_combo.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.close_button.setVisible(True)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Curernt Version Group
        version_group, version_layout = QGroupBox(), QHBoxLayout()
        version_group.setLayout(version_layout)
        version_layout.addWidget(QLabel(f"Current Version: <b>{self.current_version}</b>"))
        version_layout.addWidget(QLabel("Select Branch:"), alignment=Qt.AlignRight)
        self.branch_combo = QComboBox(fixedWidth=70, objectName="EncasedRadiusHalved")
        branches = ["Release", "Beta", "Dev"] if GITHUB_TOKEN or DEV_BRANCH_VISIBLE else ["Release", "Beta"]
        self.branch_combo.addItems(branches)
        self.branch_combo.currentIndexChanged.connect(self.on_branch_changed)
        version_layout.addWidget(self.branch_combo)

        # Check Update Group
        check_update_group, check_update_layout = QGroupBox(), QVBoxLayout()
        check_update_group.setLayout(check_update_layout)
        self.update_menu_label = QLabel("Checking for updates...", alignment=Qt.AlignCenter)
        check_update_layout.addWidget(self.update_menu_label)
        button_layout = QHBoxLayout()
        self.check_updates_button = QPushButton("Check", fixedWidth=75, objectName="EncasedRadiusHalved")
        self.check_updates_button.clicked.connect(self.manual_update_check)
        button_layout.addWidget(self.check_updates_button)
        self.download_button = QPushButton("Download", visible=False, objectName="EncasedRadiusHalved")
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        self.version_combo = QComboBox(visible=False, objectName="EncasedRadiusHalved")
        self.version_combo.currentIndexChanged.connect(self.on_version_selected)
        button_layout.addWidget(self.version_combo)
        self.cancel_button = QPushButton("Cancel", fixedWidth=75, visible=False, objectName="EncasedRadiusHalved")
        self.cancel_button.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_button)
        self.close_button = QPushButton("Close SteamKM", fixedWidth=120, objectName="EncasedRadiusHalved")
        self.close_button.clicked.connect(QApplication.quit)
        self.close_button.setVisible(False)
        button_layout.addWidget(self.close_button)
        check_update_layout.addLayout(button_layout)
        self.progress_bar = QProgressBar(visible=False)
        check_update_layout.addWidget(self.progress_bar)

        # Changelog Group
        changelog_group, changelog_layout = QGroupBox(), QVBoxLayout()
        changelog_group.setLayout(changelog_layout)
        changelog_layout.addWidget(QLabel("Changelog:", alignment=Qt.AlignLeft))
        self.changelog_text = QTextEdit(readOnly=True, objectName="ChangeLog")
        self.changelog_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        changelog_layout.addWidget(self.changelog_text)

        # Layout
        main_layout.addWidget(version_group)
        main_layout.addWidget(check_update_group)
        main_layout.addWidget(changelog_group)
        main_layout.addWidget(QLabel("SteamKM by Stick-bon", alignment=Qt.AlignRight))

    def on_branch_changed(self):
        if not self.initializing:
            self.update_menu_label.setText("Loading new branch...")
            self.update_signal.emit("Checking Branch", True)
            config = load_config()
            config["selected_branch"] = self.branch_combo.currentText().lower()
            save_config(config)
            self.parent().selected_branch = config["selected_branch"]
            self.parent().show_update_message = config.get("show_update_message", False)
            QTimer.singleShot(100, self.fetch_releases)

    def manual_update_check(self):
        self.update_menu_label.setText("Searching for Updates...")
        self.update_signal.emit("Checking Updates", True)
        QTimer.singleShot(100, self.fetch_releases)

    def fetch_releases(self):
        self.config = load_config()
        if self.config.get("show_update_message", False):
            self.set_pending_update_ui()
            return

        branch = self.branch_combo.currentText().lower()
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        
        try:
            response = requests.get(f"{GITHUB_LINK}", headers=headers)
            response.raise_for_status()
            releases = response.json()
            
            # Filter releases based on the selected branch
            if branch == "release":
                # For Stable branch, include only tags without any suffix (e.g., "0.7.0")
                versions = [release["tag_name"] for release in releases if "-" not in release["tag_name"]]
                self.version_combo.setFixedWidth(55)
            else:
                # For Beta/Dev, include tags with the respective suffix (e.g., "0.7.0-beta")
                versions = [release["tag_name"] for release in releases if f"-{branch}" in release["tag_name"].lower()]
                self.version_combo.setFixedWidth(85)

            self.version_combo.clear()
            if versions:
                latest_version_for_branch = versions[0]
                self.version_combo.addItems(versions)
                self.version_combo.setVisible(True)
                self.download_button.setVisible(True)
                self.update_menu_label.setText("Select a version to download")
                if parse(latest_version_for_branch) > parse(self.current_version):
                    self.update_signal.emit("Update Available", True)
                    logging.debug(f"Higher version found for {branch}")
            else:
                self.update_menu_label.setText(f"No downloads available for {branch.capitalize()} branch")
                self.version_combo.setVisible(False)
                self.download_button.setVisible(False)
            self.fetch_changelog()
            
        except Exception as e:
            self.update_menu_label.setText("Failed to check for updates. Please try again later.")
            self.update_signal.emit("Failed Update Check", True)
            logging.error(f"Error checking for updates: {e}")

    def fetch_changelog(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/AbelSniffel/SteamKM/main/CHANGELOG.md")
            changelog_text = response.text if response.status_code == 200 else "Failed to fetch changelog."
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
                    html_lines.append(f"<p><b>{line}</b></p>") # Bold lines that don't start with symbols
            self.changelog_text.setHtml("\n".join(html_lines))
        except Exception as e:
            self.changelog_text.setPlainText(f"Failed to fetch changelog: {e}")

    def on_version_selected(self, index):
        selected_version_text = self.version_combo.itemText(index)
        self.download_button.setText("Update")
        
        if not selected_version_text: # Check if the selected version is empty
            self.download_button.setEnabled(False)
            return
        
        if parse(selected_version_text) < parse(self.current_version):
            self.download_button.setText("Rollback")
        elif parse(selected_version_text) == parse(self.current_version):
            self.download_button.setText("Already Installed")
        
        self.download_button.setEnabled(selected_version_text != self.current_version)

    def start_download(self):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A download is already in progress.")
            return
        if selected_version := self.version_combo.currentText():
            self.latest_version = selected_version
            self.update_menu_label.setText(f"Preparing to download {self.latest_version}...")
            self.check_updates_button.setVisible(False)
            self.version_combo.setVisible(False)
            self.download_button.setVisible(False)
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
            self.download_thread.terminate()
            self.download_thread.wait()
            self.download_thread = None
            self.check_updates_button.setVisible(True)
            self.version_combo.setVisible(True)
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.download_button.setVisible(True)
        else:
            QMessageBox.warning(self, "Download Not Running", "No download is currently running.")

    def download_error(self, error_message):
        self.check_updates_button.setVisible(True)
        self.version_combo.setVisible(True)
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.download_button.setVisible(True)
        self.update_menu_label.setText("Download Error")
        QMessageBox.critical(self, "Download Error", error_message)

    def update_progress(self, downloaded, total, estimated_time):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(downloaded)
        self.update_menu_label.setText(f"Downloaded: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB (Estimated Time: {int(estimated_time)} seconds)" if estimated_time > 0 else f"Download Size: {total / (1024 * 1024):.2f} MB")

    def download_finished(self, success):
        if success:
            config = load_config()
            config["show_update_message"] = True
            save_config(config)
            self.set_pending_update_ui()
            self.parent().show_update_message = config.get("show_update_message", False)
        else:
            QMessageBox.warning(self, "Download Failed", f"Update {self.latest_version} failed to download.")
        self.download_thread.deleteLater()
        self.download_thread = None