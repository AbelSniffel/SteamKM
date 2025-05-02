# SteamKM_Import_Export.py
import re
import uuid
import json
import logging
import shutil
import os
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QLineEdit, QDialogButtonBox, QDialog
from CustomWidgets import create_scrollable_message_dialog
from Encryption import PasswordDialog
from Config import GAME_PICTURES_DIR

def import_games(main_window):
    file_paths, _ = QFileDialog.getOpenFileNames(
        main_window,
        "Select file to import",
        "",
        "Supported Files (*.txt *.json *.json.bak *.enc *.enc.bak)"
    )
    if not file_paths:
        return

    import_file = Path(file_paths[0])
    try:
        if import_file.suffix.lower() == '.json' or (import_file.suffix.lower() == '.bak' and import_file.stem.endswith('.json')):
            added_count, added_titles, added_ids = merge_imported_games_from_json(import_file, main_window.games, main_window.categories)
        elif import_file.suffix.lower() == '.txt':
            added_count, added_titles, added_ids = merge_imported_games_from_txt(import_file, main_window.games, main_window.categories, main_window)
        elif import_file.suffix.lower() == '.enc' or (import_file.suffix.lower() == '.bak' and import_file.stem.endswith('.enc')):
            added_count, added_titles, added_ids = merge_imported_games_from_enc(
                import_file, main_window.games, main_window.categories, main_window.encryption_manager
            )
            # Check for import cancellation
            if added_count == -1:  # Special code for cancellation
                return  # Just return without showing any error message
        else:
            raise ValueError("Unsupported file type")

        if added_count > 0:
            main_window.save_key_data()
            main_window.refresh_game_list()
            
            # Create message box using scrollable dialog instead of QMessageBox
            success_dialog, _ = create_scrollable_message_dialog(
                parent=main_window,
                title="Import Success",
                message=f"Successfully imported {added_count} game(s):",
                content=added_titles,
                buttons=QDialogButtonBox.Yes | QDialogButtonBox.No,
                footer_text="Would you like to fetch Steam data for these games now?"
            )

            result = success_dialog.exec()
            if result == QDialog.Accepted:
                # Create filtered dictionary of just the new games
                new_games = {id: main_window.games[id] for id in added_ids}
                
                # Use the steam manager for fetching (now uses the same filtering as "Fetch Missing Data")
                main_window.steam_manager.fetch_for_new_games(new_games)
        else:
            # Use scrollable dialog for the error message
            error_dialog, _ = create_scrollable_message_dialog(
                parent=main_window,
                title="Import Error",
                message="No new games found to import",
                content=["Didn't find any new games to import"]
            )
            error_dialog.exec()

    except Exception as e:
        # Use scrollable dialog for the error message
        error_dialog, _ = create_scrollable_message_dialog(
            parent=main_window,
            title="Import Error",
            message="An error occurred during import:",
            content=[str(e)]
        )
        error_dialog.exec()

def parse_input_line_global(line): # Robust parsing with auto-correction
    line = line.strip()
    if not line:
        return None, None, "Line is empty"

    # 1. Try standard format: Title SPACE KEY (with dashes) - No correction needed
    standard_match = re.match(r'(.+?)\s+([A-Za-z0-9]{5}-[A-Za-z0-9]{5}-[A-Za-z0-9]{5})$', line)
    if standard_match:
        title, key = standard_match.groups()
        title = title.strip()
        if title.endswith(':'):
            title = title[:-1]
        return title, key.upper(), None # No error, standard format

    # 2. Try "no space" format BUT with dashed key: TitleKEY-DASHED - Auto-correct space
    no_space_dashed_key_match = re.match(r'(.+?)([A-Za-z0-9]{5}-[A-Za-z0-9]{5}-[A-Za-z0-9]{5})$', line)
    if no_space_dashed_key_match:
        title_part, key = no_space_dashed_key_match.groups()
        return title_part.strip(), key.upper(), "Auto-corrected format by adding a space between title and key"

    # 3. Try "no space" format: TitleKEY (with key as 15 chars no dash) - Auto-correct space and dashes
    no_space_match = re.match(r'(.+?)([A-Za-z0-9]{15})$', line)
    if no_space_match:
        title_part, key_part = no_space_match.groups()
        formatted_key = f"{key_part[:5]}-{key_part[5:10]}-{key_part[10:]}".upper()
        return title_part.strip(), formatted_key, "Auto-corrected format by adding space and dashes, and key to uppercase"

    # 4. Lenient key match (for "long key" or "extra dash") - Auto-correct by cleaning key
    lenient_key_match = re.match(r'(.+?)\s+([A-Za-z0-9]{5}-[A-Za-z0-9]{5}-[A-Za-z0-9]{5}.*)$', line)
    if lenient_key_match:
        title_part, key_part = lenient_key_match.groups()
        key_candidate = "".join(filter(str.isalnum, key_part))[:15]
        if len(key_candidate) == 15:
            formatted_key = f"{key_candidate[:5]}-{key_candidate[5:10]}-{key_candidate[10:]}".upper()
            return title_part.strip(), formatted_key, "Auto-corrected key with extra characters by cleaning and formatting"

    # 5. Check for key only line (dashed or no-dash) - Title missing error
    key_only_dashed = re.fullmatch(r"[A-Za-z0-9]{5}-[A-Za-z0-9]{5}-[A-Za-z0-9]{5}$", line)
    key_only_nodash = re.fullmatch(r"[A-Za-z0-9]{15}$", line)
    if key_only_dashed or key_only_nodash:
        return None, None, "Game title is missing"

    # 6. Check for key pattern present but unclear title - Unclear format error (more specific than just "invalid")
    key_pattern_present = re.search(r"([A-Za-z0-9]{5}-[A-Za-z0-9]{5}-[A-Za-z0-9]{5}|[A-Za-z0-9]{15})", line)
    if key_pattern_present:
        return None, None, "Couldn't clearly identify title. Ensure format is 'Title KEY'"

    # 7. Generic error - No key found at all
    return None, None, "Didn't find a valid key"

def _add_game(title, code, category, games, categories, added_titles, added_ids, app_id=None, icon_path=None, review_data=None, developer=None):
    if category and category not in categories:
        categories.append(category)
    if title and code and not any(game["key"] == code for game in games.values()):
        unique_id = str(uuid.uuid4())
        game_data = {
            "title": title,
            "key": code,
            "category": category if category in categories else "New"
        }
        
        # Add Steam data if provided
        if app_id:
            game_data["app_id"] = app_id
        if icon_path and os.path.exists(icon_path):
            game_data["icon_path"] = icon_path
        if review_data:
            game_data["review_data"] = review_data
        if developer:
            game_data["developer"] = developer

        games[unique_id] = game_data
        added_titles.append(title)
        added_ids.append(unique_id)
        return 1
    return 0

def merge_imported_games_from_txt(import_file, games, categories, main_window):
    try:
        with open(import_file, 'r') as f:
            lines = f.readlines()

        added_count = 0
        added_titles = []
        added_ids = []
        invalid_lines = []

        for line in lines:
            title, key, error_message = parse_input_line_global(line) # Use global parse function
            if title and key:
                added_count += _add_game(title, key, "New", games, categories, added_titles, added_ids)
                if error_message:
                    logging.info(f"Line auto-corrected during import: '{line.strip()}'. Added as '{title} {key}'. Message: {error_message}") # Optional logging for import auto-correction
            else:
                invalid_lines.append((line, error_message if error_message else "Invalid format")) # Capture lines with errors

        if invalid_lines:
            error_text = []
            for line, error in invalid_lines:
                error_text.append(f"Line: {line.rstrip()}")
                error_text.append(f"Error: {error}")
                error_text.append("") # Add empty line for spacing
            
            # Use scrollable dialog for showing import problems
            error_dialog, _ = create_scrollable_message_dialog(
                parent=main_window,
                title="Imported TXT File Problem",
                message="The following lines had problems:",
                content=error_text,
                min_width=500,
                min_height=250
            )
            error_dialog.exec()

        return added_count, added_titles, added_ids
    except Exception as e:
        raise RuntimeError(f"TXT: {str(e)}")

def merge_imported_games_from_json(import_file, games, categories):
    try:
        with open(import_file, 'r') as f:
            imported_data = json.load(f)

        added_count = 0
        added_titles = []
        added_ids = []
        
        games_list = imported_data if isinstance(imported_data, list) else imported_data.values()
        for game in games_list:
            # Extract potential Steam data
            app_id = game.get("app_id")
            icon_path = game.get("icon_path")
            review_data = game.get("review_data")
            developer = game.get("developer")
            
            # If icon_path exists but is from a different location, adjust it
            if icon_path and os.path.exists(icon_path):
                # Keep using the existing icon
                pass
            elif app_id:
                # Check if we have this app_id's icon locally
                local_icon = os.path.join(GAME_PICTURES_DIR, f"{app_id}.jpg")
                if os.path.exists(local_icon):
                    icon_path = local_icon

            added_count += _add_game(
                game.get("title"),
                game.get("key" if isinstance(imported_data, dict) else "code"),
                game.get("category", "New"),
                games,
                categories,
                added_titles,
                added_ids,
                app_id,
                icon_path,
                review_data,
                developer
            )
           
        return added_count, added_titles, added_ids
    except Exception as e:
        raise RuntimeError(f"JSON: {str(e)}")

def merge_imported_games_from_enc(import_file, games, categories, encryption_manager):
    try:
        max_attempts = 3
        attempt_count = 0
        
        # Get the theme from main_window (parent of encryption_manager)
        while attempt_count < max_attempts:
            password_dialog = PasswordDialog(
                encryption_manager.main_window,
                "Importing Encrypted File",
                f"Enter Imported File Password (Attempt {attempt_count + 1} of {max_attempts}):"
            )
            
            result = password_dialog.exec()
            if result != QDialog.Accepted:
                return -1, [], []  # Return -1 to indicate cancellation
                
            password = password_dialog.get_password()
            
            if not password:
                QMessageBox.warning(encryption_manager.main_window, "Error", 
                                   f"Empty Password ({attempt_count + 1}/{max_attempts} attempts used)")
                attempt_count += 1
                continue

            try:
                encrypted_text = import_file.read_text()
                decrypted_data = encryption_manager.decrypt_data(encrypted_text, password)
                
                if decrypted_data is None:
                    QMessageBox.warning(encryption_manager.main_window, "Error", 
                                       f"Invalid password or corrupted data. ({attempt_count + 1}/{max_attempts} attempts used)")
                    attempt_count += 1
                    continue
                
                # Try to parse the JSON to validate it
                imported_data = json.loads(decrypted_data)
                break  # Password was correct and JSON is valid - exit the loop
                
            except json.JSONDecodeError:
                QMessageBox.warning(encryption_manager.main_window, "Error", 
                                   f"Invalid password - could not decode file. ({attempt_count + 1}/{max_attempts} attempts used)")
                attempt_count += 1
            except Exception as e:
                QMessageBox.warning(encryption_manager.main_window, "Error", 
                                   f"Error decrypting file: {str(e)} ({attempt_count + 1}/{max_attempts} attempts used)")
                attempt_count += 1
        
        else:  # This runs if the while loop completes without a break
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        added_count = 0
        added_titles = []
        added_ids = []
        
        games_list = imported_data if isinstance(imported_data, list) else imported_data.values()
        for game in games_list:
            # Extract potential Steam data
            app_id = game.get("app_id")
            icon_path = game.get("icon_path")
            review_data = game.get("review_data")
            
            # If icon_path exists but is from a different location, adjust it
            if icon_path and os.path.exists(icon_path):
                # Keep using the existing icon
                pass
            elif app_id:
                # Check if we have this app_id's icon locally
                local_icon = os.path.join(GAME_PICTURES_DIR, f"{app_id}.jpg")
                if os.path.exists(local_icon):
                    icon_path = local_icon

            added_count += _add_game(
                game.get("title"),
                game.get("key" if isinstance(imported_data, dict) else "code"),
                game.get("category", "New"),
                games,
                categories,
                added_titles,
                added_ids,
                app_id,
                icon_path,
                review_data,
                game.get("developer")
            )

        return added_count, added_titles, added_ids
        
    except Exception as e:
        raise RuntimeError(f"ENC: {str(e)}")

def manual_game_data_backup(main_window):
    backup_types = ["Regular Json (Decrypted)", "Encrypted", "Regular Text"]
    backup_type, ok = QInputDialog.getItem(main_window, "Backup Type", "Select backup type:", backup_types, 0, False)
    if not ok:
        return

    ext = {"Regular Json (Decrypted)": "json", "Encrypted": "enc", "Regular Text": "txt"}[backup_type]
    file_name, _ = QFileDialog.getSaveFileName(main_window, "Save Backup File", "", f"{ext.upper()} Files (*.{ext})")
    if not file_name:
        return

    if not file_name.endswith(f".{ext}"):
        file_name += f".{ext}"

    try:
        if backup_type == "Regular Json (Decrypted)":
            decrypted_data = main_window.encryption_manager.load_data()
            if decrypted_data:
                with open(file_name, "w") as f:
                    json.dump(json.loads(decrypted_data), f, indent=4)
            else:
                raise ValueError("Could not decrypt data for backup")
        elif backup_type == "Encrypted":
            shutil.copy(main_window.encryption_manager.encrypted_data_file, file_name)
        elif backup_type == "Regular Text":
            decrypted_data = main_window.encryption_manager.load_data()
            if decrypted_data:
                with open(file_name, "w") as f:
                    for unique_id, game_data in json.loads(decrypted_data).items():
                        f.write(f"{game_data['title']}: {game_data['key']}\n")
            else:
                raise ValueError("Could not decrypt data for backup")
                
        # Use scrollable dialog for success message
        success_dialog, _ = create_scrollable_message_dialog(
            parent=main_window,
            title="Backup Success",
            message="Data backup completed successfully",
            content=[f"Backup saved to: {file_name}"]
        )
        success_dialog.exec()
        
    except Exception as e:
        # Use scrollable dialog for error message
        error_dialog, _ = create_scrollable_message_dialog(
            parent=main_window,
            title="Backup Error",
            message="Failed to backup data:",
            content=[str(e)]
        )
        error_dialog.exec()