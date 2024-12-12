# SteamKM_Updater.py
import requests
import os
import sys
from PySide6.QtWidgets import QMessageBox
from SteamKM_Version import CURRENT_BUILD  # Import the version number

def check_for_updates(silent=False):
    try:
        response = requests.get("https://api.github.com/repos/AbelSniffel/SteamKeyManager/releases/latest")
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        latest_version = response.json().get("tag_name", "0.0.0")
        if latest_version > CURRENT_BUILD:
            return latest_version
    except requests.exceptions.RequestException as e:
        if not silent:
            QMessageBox.critical(None, "Update Error", f"Failed to check for updates: {e}")
    return None

def download_update(latest_version):
    try:
        release_url = f"https://api.github.com/repos/AbelSniffel/SteamKeyManager/releases/tags/{latest_version}"
        response = requests.get(release_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        assets = response.json().get("assets", [])
        
        # Debugging: Print available assets
        print(f"Available assets for version {latest_version}:")
        for asset in assets:
            print(asset.get("name"))
        
        for asset in assets:
            if asset.get("name") == "SteamKeyManager.py":  # Use the correct filename
                download_url = asset.get("browser_download_url")
                script_path = os.path.realpath(__file__)
                update_path = script_path + ".new"
                with open(update_path, 'wb') as f:
                    f.write(requests.get(download_url).content)
                
                # Rename the current script to a backup
                backup_path = script_path + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(script_path, backup_path)
                
                # Rename the new script to the current script name
                os.rename(update_path, script_path)
                
                QMessageBox.information(None, "Update Success", f"Update to version {latest_version} successful. Please restart the application.")
                return
        
        QMessageBox.critical(None, "Update Error", f"No matching asset found for version {latest_version}")
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(None, "Update Error", f"Failed to download update: {e}")
    except Exception as e:
        QMessageBox.critical(None, "Update Error", f"An error occurred: {e}")