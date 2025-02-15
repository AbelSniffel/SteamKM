# SteamKM_Import_Export.py
import re
import uuid
import json
import shutil
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QLineEdit

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
            added_count, added_titles = merge_imported_games_from_json(import_file, main_window.games, main_window.categories)
        elif import_file.suffix.lower() == '.txt':
            added_count, added_titles = merge_imported_games_from_txt(import_file, main_window.games, main_window.categories, main_window)
        elif import_file.suffix.lower() == '.enc' or (import_file.suffix.lower() == '.bak' and import_file.stem.endswith('.enc')):
            added_count, added_titles = merge_imported_games_from_enc(
                import_file, main_window.games, main_window.categories, main_window.encryption_manager
            )
        else:
            raise ValueError("Unsupported file type")

        if added_count > 0:
            QMessageBox.information(
                main_window,
                "Success",
                f"Successfully imported {added_count} game(s): {', '.join(added_titles)}",
            )
            main_window.save_key_data()
            main_window.refresh_game_list()
        else:
            QMessageBox.information(main_window, "Error", "Didn't find any new games to import")

    except Exception as e:
        QMessageBox.warning(main_window, "Error", f"{str(e)}")

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

def _add_game(title, code, category, games, categories, added_titles):
    if category and category not in categories:
        categories.append(category)
    if title and code and not any(game["key"] == code for game in games.values()):
        unique_id = str(uuid.uuid4())
        games[unique_id] = {"title": title, "key": code, "category": category if category in categories else "New"}
        added_titles.append(title)
        return 1
    return 0

def merge_imported_games_from_txt(import_file, games, categories, main_window):
    try:
        with open(import_file, 'r') as f:
            lines = f.readlines()

        added_count = 0
        added_titles = []
        invalid_lines = []

        for line in lines:
            title, key, error_message = parse_input_line_global(line) # Use global parse function
            if title and key:
                added_count += _add_game(title, key, "New", games, categories, added_titles)
                if error_message:
                    print(f"Line auto-corrected during import: '{line.strip()}'. Added as '{title} {key}'. Message: {error_message}") # Optional logging for import auto-correction
            else:
                invalid_lines.append((line, error_message if error_message else "Invalid format")) # Capture lines with errors

        if invalid_lines:
            error_text = "The following lines had problems:\n"
            for line, error in invalid_lines:
                error_text += f"Line: {line.rstrip()}\nError: {error}\n\n"
            QMessageBox.warning(main_window, "Imported TXT File Problem", error_text.rstrip('\n')) # Use main_window for message box during import

        return added_count, added_titles
    except Exception as e:
        raise RuntimeError(f"TXT: {str(e)}")

def merge_imported_games_from_json(import_file, games, categories):
    try:
        with open(import_file, 'r') as f:
            imported_data = json.load(f)

        added_count = 0
        added_titles = []
        
        games_list = imported_data if isinstance(imported_data, list) else imported_data.values()
        for game in games_list:
           added_count += _add_game(game.get("title"), game.get("key" if isinstance(imported_data, dict) else "code"), game.get("category", "New"), games, categories, added_titles)
           
        return added_count, added_titles
    except Exception as e:
        raise RuntimeError(f"JSON: {str(e)}")

def merge_imported_games_from_enc(import_file, games, categories, encryption_manager):
    try:
        max_attempts = 3
        attempt_count = 0
        
        while attempt_count < max_attempts:
            password, ok = QInputDialog.getText(None, "Importing Encrypted File", 
                f"Enter Imported File Password (Attempt {attempt_count + 1} of {max_attempts}):", QLineEdit.Password)
            
            if not ok:
                return 0, []  # User canceled

            try:
                decrypted_data = encryption_manager.decrypt_data(import_file.read_text(), password)
                if decrypted_data is None:
                    raise RuntimeError("Incorrect password or corrupted data")
                
                break  # Password was correct - exit the loop
            except Exception as e:
                attempt_count += 1
                if attempt_count >= max_attempts:
                    raise RuntimeError(f"Failed after {max_attempts} attempts") from e

            if not password:
                QMessageBox.warning(None, "Error", f"Empty Password???? ({attempt_count}/{max_attempts} attempts used)")
            else:
                QMessageBox.warning(None, "Error", f"Invalid password or corrupted data. ({attempt_count}/{max_attempts} attempts used)")
        
        imported_data = json.loads(decrypted_data)
        added_count = 0
        added_titles = []
        
        games_list = imported_data if isinstance(imported_data, list) else imported_data.values()
        for game in games_list:
           added_count += _add_game(game.get("title"), 
                                   game.get("key" if isinstance(imported_data, dict) else "code"), 
                                   game.get("category", "New"), 
                                   games, categories, added_titles)

        return added_count, added_titles
        
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
        QMessageBox.information(main_window, "Success", "Data backed up successfully")
    except Exception as e:
        QMessageBox.critical(main_window, "Error", f"Failed to backup data: {str(e)}")