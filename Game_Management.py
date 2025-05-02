# Game_Management.py
import os
import uuid
import html
import pyperclip
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from Config import ConfigManager, GAME_PICTURES_DIR, HORIZONTAL_SPACING, VERTICAL_SPACING, VERTICAL_SPACING_SMALL, TITLE_HEIGHT, UI_MARGIN
from CustomWidgets import ScrollRejectionComboBox, RoundedImage, PlainTextInput, create_scrollable_message_dialog
from Theme_Menu import DEFAULT_RADIUS

ICON_MULTIPLIER = 0.25  # Multiplier for icon size # 0.60
ICON_HEIGHT = 215  # Actual picture height
ICON_WIDTH = 460  # Actual picture width

# Centralized sorting functions
def get_review_sort_key(game_data):
    review_data = game_data.get("review_data", None)
    if not review_data or "rating_text" not in review_data:
        return (999, 0)  # No review data should be sorted last
    
    rating_text = review_data.get("rating_text", "").lower()
    review_count = review_data.get("review_count", 0) or 0
    
    # Define the order of ratings (from highest to lowest)
    rating_ranks = {
        "overwhelmingly positive": 1,
        "very positive": 2,
        "positive": 3,
        "mostly positive": 4,
        "mixed": 5,
        "mostly negative": 6,
        "negative": 7,
        "very negative": 8,
        "overwhelmingly negative": 9,
        "age restricted": 10
    }
    
    # Try to match the rating text to one of our defined rankings
    for rating, rank in rating_ranks.items():
        if rating in rating_text:
            return (rank, -review_count)  # Negative review count for descending sort
    
    # If we couldn't match the rating text, use a default rank
    return (100, -review_count)  # Unknown ratings sorted after known ones

def get_category_sort_key(game_data, categories):
    category = game_data.get("category", "").strip()
    if not category:
        return len(categories) + 1  # Empty categories at the end
        
    try:
        # Return the index of the category in the categories list
        return categories.index(category)
    except ValueError:
        # If category isn't in the list, place it at the end
        return len(categories)

def get_app_id_sort_key(game_data):
    app_id = game_data.get("app_id", "").strip()
    if not app_id:
        return float('inf')  # Empty app_ids at the end
    
    try:
        # Convert to integer for proper numerical sorting
        return int(app_id)
    except ValueError:
        # If app_id isn't a valid number, sort it to the end
        return float('inf')

def get_sort_key_function(column_index, categories=None):  
    sort_keys = {
        0: lambda g: g["title"].lower() if isinstance(g, dict) else g[1]["title"].lower(),  # Icon sorts by title
        1: lambda g: g["title"].lower() if isinstance(g, dict) else g[1]["title"].lower(),  # Game Title
        2: lambda g: g["key"].lower() if isinstance(g, dict) else g[1]["key"].lower(),      # Steam Key
        3: lambda g: get_category_sort_key(g, categories) if isinstance(g, dict) else get_category_sort_key(g[1], categories),  # Category
        4: lambda g: get_app_id_sort_key(g) if isinstance(g, dict) else get_app_id_sort_key(g[1]),  # AppID - numeric sorting
        5: lambda g: get_review_sort_key(g) if isinstance(g, dict) else get_review_sort_key(g[1]),  # Steam Ratings
        6: lambda g: g.get("developer", "").lower() if isinstance(g, dict) else g[1].get("developer", "").lower(),  # Developer
    }
    
    return sort_keys.get(column_index, sort_keys[1])

class EditGameDialog(QDialog):
    def __init__(self, parent=None, games=None, sort_column=1, sort_order=Qt.AscendingOrder, border_radius=DEFAULT_RADIUS, parent_categories=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Games Menu")
        self.setMinimumSize(700, 200)
        self.resize(900, 400)
        self.games = games or []
        self.original_data = [{k: v for k, v in game.items()} for game in self.games]  # Deep copy
        self.modified_games = []
        self.force_fetch = []
        self.config_manager = ConfigManager()
        self.categories = parent_categories or self.config_manager.get("categories", ["Premium", "Good", "Low Effort", "Bad", "VR", "Used", "New"])
        self.border_radius = border_radius
        
        self.sort_games(sort_column, sort_order)
        self.setup_ui()
    
    def sort_games(self, sort_column, sort_order):
        if not self.games:
            return
            
        # Use the centralized sort key function
        sort_key = get_sort_key_function(sort_column, self.categories)
        self.games.sort(key=sort_key, reverse=(sort_order == Qt.DescendingOrder))
        self.original_data = [{k: v for k, v in game.items()} for game in self.games]

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*UI_MARGIN)

        # GroupBox for column headers
        header_groupbox = QGroupBox()
        header_layout = QHBoxLayout(header_groupbox)
        margins = header_layout.contentsMargins()
        header_layout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())  # Only modify the right margin
        header_layout.setSpacing(HORIZONTAL_SPACING)
        headers = ["Icon", "Title", "Key", "AppID", "Category"]
        header_stretches = [0, 4, 3, 0, 1]  # Match grid column stretches

        # Fixed sizes for Icon, AppID, and Category headers
        ICON_HEADER_WIDTH = ICON_WIDTH * ICON_MULTIPLIER
        APPID_HEADER_WIDTH = 80
        CATEGORY_HEADER_WIDTH = 140

        for i, text in enumerate(headers):
            label = QLabel(text)
            label.setObjectName("Title")
            label.setAlignment(Qt.AlignCenter)
            # Set fixed sizes for specific headers
            if i == 0:  # Icon
                label.setFixedWidth(ICON_HEADER_WIDTH)
            elif i == 3:  # AppID
                label.setFixedWidth(APPID_HEADER_WIDTH)
            elif i == 4:  # Category
                label.setMinimumWidth(CATEGORY_HEADER_WIDTH)
            header_layout.addWidget(label, header_stretches[i])
        main_layout.addWidget(header_groupbox)

        # GroupBox for the scrollable grid
        groupbox = QGroupBox()
        groupbox_layout = QVBoxLayout(groupbox)

        # Scroll area for game rows
        scroll_area = QScrollArea(objectName="DynamicVScrollBar")
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        grid_layout = QGridLayout(scroll_area_widget)
        grid_layout.setContentsMargins(0, 0, 8, 0)
        grid_layout.setAlignment(Qt.AlignTop)
        grid_layout.setHorizontalSpacing(HORIZONTAL_SPACING)
        grid_layout.setVerticalSpacing(VERTICAL_SPACING_SMALL)

        self.row_widgets = []
        Icon_height, Icon_width = ICON_HEIGHT * ICON_MULTIPLIER, ICON_WIDTH * ICON_MULTIPLIER

        for row, game in enumerate(self.games):
            icon_label = RoundedImage(parent=self, border_radius=self.border_radius)
            icon_label.setFixedSize(Icon_width, Icon_height)
            icon_label.setAlignment(Qt.AlignCenter)
            if "icon_path" in game and os.path.exists(game["icon_path"]):
                pixmap = QPixmap(game["icon_path"]).scaled(Icon_width, Icon_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setText("._.")
                icon_label.setStyleSheet("font-size: 24px; qproperty-alignment: AlignCenter;")  # Vertically and horizontally center

            # Editable fields
            title_edit = QLineEdit(game["title"])
            title_edit.setAlignment(Qt.AlignCenter)
            key_edit = QLineEdit(game["key"])
            key_edit.setAlignment(Qt.AlignCenter)
            app_id_edit = QLineEdit(game.get("app_id", ""))
            app_id_edit.setAlignment(Qt.AlignCenter)
            app_id_edit.setFixedWidth(80)

            category_combo = ScrollRejectionComboBox()
            category_combo.addItems(self.categories)
            category_combo.setCurrentText(game["category"] if game["category"] in self.categories else "New")
            category_combo.setMinimumWidth(140)

            # Add widgets to grid - use column stretches consistent with headers
            grid_layout.addWidget(icon_label, row, 0)
            grid_layout.addWidget(title_edit, row, 1)
            grid_layout.addWidget(key_edit, row, 2)
            grid_layout.addWidget(app_id_edit, row, 3)
            grid_layout.addWidget(category_combo, row, 4)

            self.row_widgets.append((icon_label, title_edit, key_edit, app_id_edit, category_combo))

        # Set column stretch factors
        grid_layout.setColumnStretch(0, 0)  # Icon (fixed width)
        grid_layout.setColumnStretch(1, 4)  # Title
        grid_layout.setColumnStretch(2, 3)  # Key
        grid_layout.setColumnStretch(3, 0)  # AppID (fixed width)
        grid_layout.setColumnStretch(4, 1)  # Category

        groupbox_layout.addWidget(scroll_area)
        main_layout.addWidget(groupbox)

        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_changes)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def apply_changes(self):
        for idx, (_, title_edit, key_edit, app_id_edit, category_combo) in enumerate(self.row_widgets):
            original = self.original_data[idx]
            game = self.games[idx]
            
            # Check all fields at once
            new_values = {
                "title": title_edit.text(),
                "key": key_edit.text(),
                "app_id": app_id_edit.text(),
                "category": category_combo.currentText()
            }
            
            modified = False
            for key, new_value in new_values.items():
                old_value = original.get(key, "")
                if str(new_value) != str(old_value):
                    modified = True
                    game[key] = new_value
                    
                    # Handle AppID changes specially
                    if key == "app_id":
                        game.pop("icon_path", None)
                        if game not in self.force_fetch:
                            self.force_fetch.append(game)
            
            if modified and game not in self.modified_games:
                self.modified_games.append(game)

        self.accept()

class AddGamesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Games")
        self.resize(550, 250)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel("Add games (one per line, format: Title XXXXX-XXXXX-XXXXX)")
        layout.addWidget(info_label)
        
        # Text input
        self.input_text = PlainTextInput(
            lineWrapMode=QTextEdit.NoWrap,
            verticalScrollBarPolicy=Qt.ScrollBarAsNeeded
        )
        layout.addWidget(self.input_text, 1)  # 1 = stretch factor to take available space
        
        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Games")
        add_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def get_input_text(self):
        return self.input_text.toPlainText().strip()

def create_game_list_dialog(parent, title, message, game_list, 
                           min_width=400, min_height=150, 
                           buttons=QDialogButtonBox.Ok, 
                           extra_widgets=None,
                           footer_text=None):
    """Creates a dialog with a scrollable list of games"""
    dialog, get_content_browser = create_scrollable_message_dialog(
        parent=parent,
        title=title,
        message=message,
        content=game_list,
        min_width=min_width,
        min_height=min_height,
        buttons=buttons,
        extra_widgets=extra_widgets,
        footer_text=footer_text
    )
    # Set minimum height to the dialog's natural minimum
    dialog.setMinimumHeight(dialog.sizeHint().height())
    return dialog, get_content_browser

def edit_selected_games(parent, table_widget, games, row_to_unique_id, save_key_data, refresh_game_list, 
                        current_sort_column, current_sort_order, steam_manager, 
                        using_custom_colors=False, border_radius=DEFAULT_RADIUS):
    selected_items = table_widget.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Edit Error", "Please select at least one item to edit")
        return

    # Get unique games to edit
    unique_ids = {row_to_unique_id[item.row()] for item in selected_items}

    # --- Patch: Update icon_path for games if icon file now exists ---
    for uid in unique_ids:
        game = games[uid]
        app_id = game.get("app_id", "")
        icon_path = game.get("icon_path", "")
        if app_id and (not icon_path or not os.path.exists(icon_path)):
            possible_icon = os.path.join(GAME_PICTURES_DIR, f"{app_id}.jpg")
            if os.path.exists(possible_icon):
                game["icon_path"] = possible_icon
    # --- End patch ---

    # Save original AppIDs to detect changes
    original_app_ids = {uid: games[uid].get("app_id", "") for uid in unique_ids}
    games_to_edit = [games[uid] for uid in unique_ids]
    
    # Use correct border radius
    actual_border_radius = border_radius if using_custom_colors else DEFAULT_RADIUS
    
    # Open edit dialog - pass parent's categories list for consistent sorting
    parent_categories = getattr(parent, 'categories', None)  # Safely get parent's categories if available
    dialog = EditGameDialog(parent, games_to_edit, current_sort_column, current_sort_order, actual_border_radius, parent_categories)
    if dialog.exec() == QDialog.Accepted:
        save_key_data()
        
        # Check which games need data refresh
        modified_games_dict = {}
        for unique_id in unique_ids:
            game = games[unique_id]
            if game.get("app_id", "") != original_app_ids[unique_id]:
                if game not in dialog.force_fetch:
                    dialog.force_fetch.append(game)
            
            if game in dialog.force_fetch:
                modified_games_dict[unique_id] = game
        
        refresh_game_list()

        # Fetch Steam data if needed
        if modified_games_dict:
            steam_manager.fetch_for_edited_games(modified_games_dict)

def process_game_selection(table_widget, row_to_unique_id, games=None):
    """Extract unique selected games from table selection"""
    selected_items = table_widget.selectedItems()
    if not selected_items:
        return None, []
    
    unique_ids = set()
    processed_rows = set()
    selected_games = []
    
    for item in selected_items:
        row = item.row()
        if row not in processed_rows:
            processed_rows.add(row)
            unique_id = row_to_unique_id[row]
            unique_ids.add(unique_id)
            if games and unique_id in games:
                selected_games.append(games[unique_id])
    
    return unique_ids, selected_games

def add_games(parent, games, save_key_data, refresh_game_list, steam_manager, parse_input_line):
    # Open dialog to get input
    dialog = AddGamesDialog(parent)
    if dialog.exec() != QDialog.Accepted:
        return
        
    input_text_value = dialog.get_input_text()
    if not input_text_value:
        return
        
    added_count = 0
    invalid_lines = []
    already_exists = set()
    added_game_ids = []

    # Process input lines
    existing_keys = {game["key"] for game in games.values()}
    for line in input_text_value.split('\n'):
        title, key, error_message = parse_input_line(line)
        if title and key:
            if key not in existing_keys:
                unique_id = str(uuid.uuid4())
                games[unique_id] = {"title": title, "key": key, "category": "New"}
                added_count += 1
                added_game_ids.append(unique_id)
                existing_keys.add(key)  # Update to prevent duplicates within current batch
            else:
                already_exists.add("\n• " + title)
        else:
            invalid_lines.append((line, error_message))

    # Show error messages if any
    if invalid_lines or already_exists:
        error_text = ""
        if already_exists:
            error_text += f"Ignored these titles due to duplicate keys: {"".join(already_exists)}\n\n"
        if invalid_lines:
            error_text += "The following lines had problems:"
            for line, error in invalid_lines:
                error_text += f"\n• {line} / Error: {error}"

        error_dialog, _ = create_game_list_dialog(
            parent=parent,
            title="Import Issues",
            message="The following issues occurred:",
            game_list=error_text.rstrip('\n'),
        )
        error_dialog.exec_()

    # If games were added, save data and show success
    if added_count > 0:
        save_key_data()
        refresh_game_list()
        
        # Get new games info for Steam fetching
        new_games = {id: games[id] for id in added_game_ids}
        
        added_titles = [games[id]['title'] for id in added_game_ids]
        
        success_dialog, _ = create_game_list_dialog(
            parent=parent,
            title="Success",
            message=f"Successfully added {added_count} games:" if added_count > 1 else "Successfully added:",
            game_list=added_titles,
            footer_text="Fetching Steam data..."
        )
        success_dialog.exec_()

        # Fetch Steam data for new games
        steam_manager.fetch_for_new_games(new_games)

def remove_selected_games(parent, table_widget, games, row_to_unique_id, save_key_data, refresh_game_list):
    unique_ids, selected_games = process_game_selection(table_widget, row_to_unique_id, games)
    if not selected_games:
        QMessageBox.information(parent, "Remove Error", "Please select at least one item to remove")
        return

    removed_titles = [game["title"] for game in selected_games]
    
    # Add count to the message
    count = len(selected_games)
    message = f"Remove the following {count} game{'s' if count != 1 else ''}?"

    # Confirm removal
    confirm_dialog, _ = create_game_list_dialog(
        parent=parent,
        title="Deleting Game Entries",
        message=message,
        game_list=removed_titles,
        buttons=QDialogButtonBox.Yes | QDialogButtonBox.No
    )
    
    if confirm_dialog.exec_() == QDialog.Accepted:
        # Delete the games
        for unique_id in unique_ids:
            if unique_id in games:
                del games[unique_id]
        
        # Show success confirmation
        success_dialog, _ = create_game_list_dialog(
            parent=parent,
            title="Games Removed",
            message="Successfully removed these games:",
            game_list=removed_titles
        )
        
        save_key_data()
        refresh_game_list()
        success_dialog.exec_()

def copy_selected_keys(parent, table_widget, games, row_to_unique_id):
    unique_ids, selected_games = process_game_selection(table_widget, row_to_unique_id, games)
    if not selected_games:
        QMessageBox.information(parent, "Copy Error", "Please select at least one item to copy")
        return

    game_titles = [game['title'] for game in selected_games]
    copy_options = [
        ("Title And Key", lambda title, key: f"{title}: {key}"),
        ("Discord Spoiler", lambda title, key: f"{title}: ||{key}||"),
        ("Title Only", lambda title, key: title),
        ("Key Only", lambda title, key: key),
    ]

    # Dialog setup (create dialog and get content_browser)
    dialog, get_content_browser = create_game_list_dialog(
        parent=parent,
        title="Copying Game Keys",
        message="",  # Remove message from dialog header
        game_list=game_titles,
        buttons=QDialogButtonBox.Cancel,
        extra_widgets=[],
    )
    content_browser = get_content_browser()

    # GroupBox for buttons, label, and the scrollable list
    button_groupbox = QGroupBox()
    button_groupbox.setFlat(True)
    groupbox_vbox = QVBoxLayout(button_groupbox)

    # Copy Options label
    Title = QLabel("Copy Options", objectName="Title", fixedHeight=TITLE_HEIGHT)
    Title.setAlignment(Qt.AlignCenter)
    groupbox_vbox.addWidget(Title)

    # Horizontal layout for the copy buttons
    button_layout = QHBoxLayout()
    button_layout.setSpacing(HORIZONTAL_SPACING)
    copy_buttons = []
    for label, _ in copy_options:
        btn = QPushButton(label)
        button_layout.addWidget(btn)
        copy_buttons.append(btn)
    groupbox_vbox.addLayout(button_layout)

    # Add spacing between button_layout and content_browser
    groupbox_vbox.addSpacing(VERTICAL_SPACING)

    # Add the scrollable game list (content_browser)
    groupbox_vbox.addWidget(content_browser)

    # Insert the groupbox above the dialog's button box
    vbox = QVBoxLayout()
    vbox.addWidget(button_groupbox)
    dialog.layout().insertLayout(dialog.layout().count() - 1, vbox)

    # Move the "Copying X game entries:" text to the same line as the Cancel button
    bottom_hbox = QHBoxLayout()
    count = len(selected_games)
    entries_label = QLabel(f"Copying {count} {'game entries' if count != 1 else 'game entry'}")
    bottom_hbox.addWidget(entries_label)
    bottom_hbox.addStretch()

    # Remove the Cancel button from the dialog's button box and add it here
    cancel_btn = dialog.button_box.button(QDialogButtonBox.Cancel)
    if cancel_btn:
        dialog.button_box.removeButton(cancel_btn)
        cancel_btn.clicked.connect(dialog.reject)
        bottom_hbox.addWidget(cancel_btn)
    dialog.layout().addLayout(bottom_hbox)

    def handle_copy(style_idx):
        style_func = copy_options[style_idx][1]
        selected_keys = [style_func(game['title'], game['key']) for game in selected_games]
        pyperclip.copy("\n".join(selected_keys))
        preview_text = "".join([f"{html.escape(line)}<br>" for line in selected_keys])
        confirm, _ = create_game_list_dialog(
            parent=parent,
            title="Copy Keys",
            message="Copied to clipboard:",
            game_list=preview_text
        )
        dialog.accept()
        confirm.exec_()

    for idx, btn in enumerate(copy_buttons):
        btn.clicked.connect(lambda _, i=idx: handle_copy(i))

    dialog.exec_()