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
from SteamKM_Config import load_config, save_config
from packaging.version import parse, InvalidVersion

URL = "https://api.github.com/repos/AbelSniffel/SteamKM/releases"

logging.basicConfig(level=logging.DEBUG)

try:
    from github_token import GITHUB_TOKEN
    logging.debug("GitHub token loaded successfully.")
except ImportError:
    GITHUB_TOKEN = None
    logging.debug("GitHub token not found. Using unauthenticated requests.")

def check_for_updates(config=None): # NEED TO MAKE THIS NOT A CRUCIAL PART SO THAT THE PROGRAM IS FUNCTIONAL EVEN IF THE UPDATE CHECK FAILS
    if config is None:
        config = load_config()
    
    selected_branch = config.get("selected_branch", "Beta")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        response = requests.get(f"{URL}/latest", headers=headers)
        response.raise_for_status()
        latest_version = response.json().get("tag_name", "0.0.0")
        logging.debug(f"Latest version from GitHub: {latest_version}")
        
        if selected_branch in latest_version:
            return latest_version if parse(latest_version) > parse(CURRENT_BUILD) else CURRENT_BUILD
        return CURRENT_BUILD
        
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
        QMessageBox.critical(None, "Update Error", str(e))
        return CURRENT_BUILD

def download_update(latest_version, progress_callback):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        release_url = f"{URL}/tags/{latest_version}"
        response = requests.get(release_url, headers=headers)
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
                with open(update_path, 'wb') as f:
                    with requests.get(download_url, headers=headers, stream=True) as r:
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
        raise Exception("No matching asset found for version {latest_version}")
    except Exception as e:
        logging.error(f"Failed to download update: {e}")
        raise e

class UpdateManager: # This is triggered from the main script for automatic startup update check
    def __init__(self, parent=None, current_version=CURRENT_BUILD):
        self.parent = parent
        self.cleanup_old_files()
        self.current_version = current_version
        self.update_check_thread = UpdateCheckThread()
        self.update_check_thread.update_available.connect(self.on_update_available)
        self.update_check_thread.finished.connect(self.update_check_thread.deleteLater)
        QTimer.singleShot(1000, self.start_update_check)

    def start_update_check(self):
        self.update_check_thread.start()

    def on_update_available(self, available):
        update_available_label = self.parent.findChild(QLabel, "update_available_label")
        update_available_label.setText("Update Available")
        update_available_label.setVisible(available)

    def cleanup_old_files(self):
        backup_file = os.path.realpath(sys.executable) + ".bak"
        restart_script = "restart_script.py"
        
        for file_path in [backup_file, restart_script]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed {file_path}")
                except Exception as e:
                    print(f"Failed to remove {file_path}: {e}")

class UpdateCheckThread(QThread):
    update_available = Signal(bool)

    def run(self):
        available = parse(check_for_updates()) > parse(CURRENT_BUILD)
        self.update_available.emit(available)

class DownloadThread(QThread):
    progress_signal = Signal(int, int, float)
    finished_signal = Signal(bool)
    error_signal = Signal(str)

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
        download_speed = downloaded / elapsed_time if elapsed_time > 0 and downloaded > 0 else 0
        remaining_bytes = total - downloaded
        estimated_time = remaining_bytes / download_speed if download_speed > 0 else 0
        self.progress_signal.emit(downloaded, total, estimated_time)

class UpdateDialog(QDialog):
    def __init__(self, parent=None, current_version=CURRENT_BUILD):
        super().__init__(parent)
        self.setWindowTitle("Update Menu")
        self.resize(480, 600)
        self.current_version = current_version
        self.latest_version = None
        self.download_thread = None
        self.initializing = True
        self.setup_ui()
        self.load_saved_branch()
        self.initializing = False
        QTimer.singleShot(100, self.fetch_releases) # Delay update fetch so that the UI can fire right up

    def load_saved_branch(self):
        try:
            config = load_config()
            saved_branch = config.get("selected_branch", "Beta")
            index = self.branch_combo.findText(saved_branch.capitalize())
            if index >= 0:
                self.branch_combo.setCurrentIndex(index)
        except Exception as e:
            logging.error(f"Failed to load saved branch: {e}")

    def setup_ui(self):
        main_layout = QVBoxLayout()

        version_group = QGroupBox()
        version_layout = QHBoxLayout()

        version_label = QLabel(f"Current Version: <b>{self.current_version}</b>")
        version_layout.addWidget(version_label)

        select_branch_label = QLabel("Select Branch:")
        version_layout.addWidget(select_branch_label, alignment=Qt.AlignRight)

        self.branch_combo = QComboBox(fixedWidth=65)
        self.branch_combo.addItems(["Stable", "Beta", "Alpha"])
        self.branch_combo.currentIndexChanged.connect(self.on_branch_changed)
        version_layout.addWidget(self.branch_combo)

        version_group.setLayout(version_layout)
        main_layout.addWidget(version_group)

        check_update_group = QGroupBox()
        check_update_layout = QVBoxLayout()
        self.update_label = QLabel("Checking for updates...", alignment=Qt.AlignCenter)
        check_update_layout.addWidget(self.update_label)

        button_layout = QHBoxLayout()
        self.check_updates_button = QPushButton("Check", fixedWidth=75)
        self.check_updates_button.clicked.connect(self.manual_update_check)
        button_layout.addWidget(self.check_updates_button)

        self.download_button = QPushButton("Download", visible=False)
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        
        self.version_combo = QComboBox(fixedWidth=130, visible=False)
        self.version_combo.currentIndexChanged.connect(self.on_version_selected)
        button_layout.addWidget(self.version_combo)

        self.cancel_button = QPushButton("Cancel", fixedWidth=75, visible=False)
        self.cancel_button.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_button)

        check_update_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar(visible=False)
        check_update_layout.addWidget(self.progress_bar)

        check_update_group.setLayout(check_update_layout)
        main_layout.addWidget(check_update_group)

        changelog_group = QGroupBox()
        changelog_layout = QVBoxLayout()

        changelog_label = QLabel("Changelog:", alignment=Qt.AlignLeft)
        changelog_layout.addWidget(changelog_label)

        self.changelog_text = QTextEdit(readOnly=True)
        self.changelog_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        changelog_layout.addWidget(self.changelog_text)
        changelog_group.setLayout(changelog_layout)
        main_layout.addWidget(changelog_group)

        created_by_label = QLabel("SteamKM by Stick-bon", alignment=Qt.AlignRight)
        main_layout.addWidget(created_by_label)

        self.setLayout(main_layout)

    def on_branch_changed(self):
        branch = self.branch_combo.currentText().lower()

        if not self.initializing:
            self.update_label.setText("Loading New Branch...")
            
            try:
                config = load_config()
                config["selected_branch"] = branch
                save_config(config)
            except Exception as e:
                logging.error(f"Failed to save config: {e}")

            QTimer.singleShot(100, self.fetch_releases)

    def manual_update_check(self):
        self.update_label.setText("Searching for Updates...")
        QTimer.singleShot(100, self.fetch_releases)

    def fetch_releases(self):
        branch = self.branch_combo.currentText().lower()
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        try:
            response = requests.get(f"https://api.github.com/repos/AbelSniffel/SteamKM/releases", headers=headers)
            response.raise_for_status()
            releases = response.json()
            versions = [release["tag_name"] for release in releases]
            
            # Filter versions based on the selected branch
            if branch == "stable":
                versions = [v for v in versions if "-stable" in v]
            elif branch == "beta":
                versions = [v for v in versions if "-beta" in v]
            elif branch == "alpha":
                versions = [v for v in versions if "-alpha" in v]
            
            latest_version = versions[0] if versions else None

            self.version_combo.clear()
            local_version = parse(self.current_version)
            if versions:
                for version in versions:
                    item_text = version
                    if version == latest_version:
                        item_text = f"{version} (latest)"
                    self.version_combo.addItem(item_text)
                self.download_button.setVisible(True)
            else:
                self.version_combo.addItem("No Available Updates")
                self.version_combo.setFixedWidth(140)
                self.download_button.setVisible(False)
            
            self.version_combo.setVisible(True)
            self.fetch_changelog()

            if latest_version and local_version >= parse(latest_version):
                self.update_label.setText("You're already on the latest build.")
                self.version_combo.setFixedWidth(130)
                return
            self.update_label.setText("Select a version to download.")
        except Exception as e:
            self.update_label.setText("Failed to check for updates. Please try again later.")
            logging.error(f"Error checking for updates: {e}")

    def fetch_changelog(self):
        try:
            response = requests.get(f"https://raw.githubusercontent.com/AbelSniffel/SteamKM/main/CHANGELOG.md")
            if response.status_code == 200:
                changelog_text = response.text
                lines = changelog_text.split('\n')
                # Initialize an empty list to hold the HTML lines
                html_lines = []
                
                for line in lines:
                    if line.startswith("0."):
                        # Version header
                        html_lines.append(f"<h3>{line}</h3>")
                    elif line.startswith("+"):
                        # Added items
                        html_lines.append(f"<p><span style='color: green;'><strong>+</strong></span> {line[2:]}</p>")
                    elif line.startswith("*"):
                        # Tweaked items
                        html_lines.append(f"<p><span style='color: orange;'><strong>*</strong></span> {line[2:]}</p>")
                    elif line.startswith("-"):
                        # Removed items
                        html_lines.append(f"<p><span style='color: red;'><strong>-</strong></span> {line[2:]}</p>")
                    else:
                        # Other lines (e.g., empty lines)
                        html_lines.append(f"<p>{line}</p>")
                
                # Join the HTML lines into a single string
                html_changelog = "\n".join(html_lines)
                self.changelog_text.setHtml(html_changelog)
            else:
                self.changelog_text.setPlainText("Failed to fetch changelog.")
        except Exception as e:
            self.changelog_text.setPlainText(f"Failed to fetch changelog: {e}")

    def on_version_selected(self, index):
        selected_version = self.version_combo.itemText(index).replace("(latest)", "").strip()
        self.download_button.setEnabled(selected_version != self.current_version)

    def start_download(self):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A download is already in progress.")
            return
        selected_version = self.version_combo.currentText().replace("(latest)", "").strip()
        if selected_version:
            self.latest_version = selected_version
            self.update_label.setText("Starting Download...")
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
            self.update_label.setText("Download cancelled.")
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
        self.update_label.setText("Download Error")
        QMessageBox.critical(self, "Download Error", error_message)

    def update_progress(self, downloaded, total, estimated_time):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(downloaded)
        self.update_label.setText(f"Downloaded: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB\nEstimated Time: {int(estimated_time)} seconds" if estimated_time > 0 else f"Download Size: {downloaded / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB")

    def download_finished(self, success):
        if success:
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.download_button.setVisible(True)
            
            try:
                config = load_config()
                config["show_update_message"] = True
                save_config(config)
            except Exception as e:
                logging.error(f"Failed to update config file: {e}")

            # Create a temporary script to handle the restart
            restart_script = """
    import os
    import sys
    import time

    # Paths
    new_executable = '{}'
    old_executable = '{}'
    backup_executable = '{}'

    # Wait for the main application to close
    time.sleep(2)

    # Replace the old executable with the new one
    os.remove(old_executable)
    os.rename(new_executable, old_executable)

    # Remove the backup file if it exists
    if os.path.exists(backup_executable):
        os.remove(backup_executable)

    # Restart the application
    os.execv(old_executable, ['python'] + sys.argv)
    """.format(os.path.realpath(sys.executable) + ".new", os.path.realpath(sys.executable), os.path.realpath(sys.executable) + ".bak")

            # Write the restart script to a temporary file
            with open("restart_script.py", "w") as f:
                f.write(restart_script)

            try:
                # Run the restart script in a new process
                subprocess.Popen([sys.executable, "restart_script.py"])
                QApplication.quit()
            except Exception as e:
                QMessageBox.information(self, "Restart Required", "Please reopen the program to get the latest update.")
        else:
            msg_box = QMessageBox.warning
            msg_box(self, "Download Failed", f"Update {self.latest_version} failed to download.")
            self.download_thread.deleteLater()
            self.download_thread = None