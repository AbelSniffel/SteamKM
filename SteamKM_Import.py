# SteamKM_Import.py
import json
import re
from pathlib import Path
import uuid

def merge_imported_games_from_json(import_file, games, categories):
    try:
        with open(import_file, 'r') as file:
            imported_data = json.load(file)
        
        added_count = 0
        added_titles = []
        new_categories = []

        def add_game(title, code, category):
            nonlocal added_count, added_titles, new_categories
            if category and category not in categories:
                new_categories.append(category)
            if title and code and not any(game["key"] == code for game in games.values()):
                unique_id = str(uuid.uuid4())
                games[unique_id] = {"title": title, "key": code, "category": category if category in categories else "New"}
                added_count += 1
                added_titles.append(title)

        if isinstance(imported_data, list):
            for game in imported_data:
                add_game(game.get("title"), game.get("code"), game.get("category", "New"))
        elif isinstance(imported_data, dict):
            for game in imported_data.values():
                add_game(game.get("title"), game.get("key"), game.get("category", "New"))
        
        # Add new categories found in import
        categories.extend(new_categories)
        
        return added_count, added_titles
    except Exception as e:
        raise RuntimeError(f"Failed to import games from JSON: {str(e)}")

def merge_imported_games_from_txt(import_file, games, categories):
    try:
        with open(import_file, 'r') as file:
            lines = file.readlines()
        
        added_count = 0
        added_titles = []
        new_categories = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 2:
                continue  # Skip invalid lines

            # Find the split point between title and key
            for i in range(len(parts)):
                part = parts[i]
                if re.match(r'\d{5}-[A-Z0-9]{5}-[A-Z0-9]{5}', part):
                    title_parts = parts[:i]
                    key = parts[i]
                    category = "New"  # Default category
                    break
                elif ':' in part:
                    colon_index = part.index(':')
                    if colon_index != -1:
                        title_parts = [part[:colon_index]]
                        key = part[colon_index+1:].strip()
                        if not re.match(r'\d{5}-[A-Z0-9]{5}-[A-Z0-9]{5}', key):
                            continue  # Invalid key format
                        break
            else:
                continue  # No valid key found in the line

            title = ' '.join(title_parts).replace(':', '')
            if title and key and not any(game["key"] == key for game in games.values()):
                unique_id = str(uuid.uuid4())
                games[unique_id] = {"title": title, "key": key, "category": category}
                added_count += 1
                added_titles.append(title)

        categories.extend(new_categories)
        return added_count, added_titles
    except Exception as e:
        raise RuntimeError(f"Failed to import games from TXT: {str(e)}")