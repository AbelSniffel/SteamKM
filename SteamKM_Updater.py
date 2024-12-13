# SteamKM_Updater.py
import requests
import os
import sys
from PySide6.QtWidgets import QMessageBox
from SteamKM_Version import CURRENT_BUILD
from packaging.version import parse, InvalidVersion 
import logging

# Debug logging
logging.basicConfig(level=logging.DEBUG)

try:
    from github_token import GITHUB_TOKEN
    logging.debug("GitHub token loaded successfully.")
except ImportError:
    GITHUB_TOKEN = None
    logging.debug("GitHub token not found. Using unauthenticated requests.")

def check_for_updates(silent=False):
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get("https://api.github.com/repos/AbelSniffel/SteamKM/releases/latest", headers=headers)
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

def download_update(latest_version):
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
                
                with open(update_path, 'wb') as f:
                    f.write(requests.get(download_url, headers=headers).content)
                
                backup_path = script_path + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(script_path, backup_path)
                
                os.rename(update_path, script_path)
                
                QMessageBox.information(None, "Update Success", f"Update to version {latest_version} successful. Please restart the application.")
                return
        
        QMessageBox.critical(None, "Update Error", f"No matching asset found for version {latest_version}")
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(None, "Update Error", f"Failed to download update: {e}")
    except Exception as e:
        QMessageBox.critical(None, "Update Error", f"An error occurred: {e}")