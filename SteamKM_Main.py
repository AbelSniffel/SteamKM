# SteamKM_Main.py
import json
import sys
import pyperclip
import re
import uuid
import shutil
import os, sys
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QPalette, QColor
from PySide6.QtCore import Qt, QPoint, QTimer, QThread, Signal
from SteamKM_Version import CURRENT_BUILD
from SteamKM_Updater import UpdateDialog, AutomaticUpdateCheck
from SteamKM_Themes import ColorConfigDialog, Theme, ModernQLineEdit, DEFAULT_BR, DEFAULT_BS, DEFAULT_BSI, DEFAULT_CR, DEFAULT_SR, DEFAULT_SW, BUTTON_HEIGHT
from SteamKM_Icons import UPDATE_ICON, MENU_ICON, CUSTOMIZATION_ICON, CATEGORY_MANAGER_ICON
from SteamKM_Config import load_config, save_config, DEFAULT_BRANCH
from SteamKM_Edit_Menu import EditGameDialog
from SteamKM_Category_Menu import CategoryManagerDialog
from SteamKM_Encryption import EncryptionManager
from SteamKM_Import_Backup import import_games, manual_game_data_backup, parse_input_line_global
import weakref
#from pyqttooltip import Tooltip

class PlainTextInput(QTextEdit): # Removes Rich Text Support
    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())

class SteamKeyManager(QMainWindow):
    update_label_signal = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Key Manager V3 (Beta)")
        self.resize(1005, 600)
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.icons_dir = os.path.join(self.script_dir, "SteamKM_Icons")

        # Initialize Data
        self.games = {}
        self.visible_keys = set()
        self.show_keys = False
        self.encryption_manager = EncryptionManager(self)
        self.load_initial_data()
        self.load_key_data()
        self.setup_ui()
        self.apply_theme()

        # Initialize Update Checker
        self.update_manager = AutomaticUpdateCheck(self)
        self.update_manager_ref = weakref.ref(self.update_manager)
        self.update_label_signal.connect(self.handle_update_status_label)
        self.update_manager.update_status_signal.connect(self.handle_update_status_label) # Connect to the new signal
        self.message_timer = None
        self.update_manager.start()

    def load_initial_data(self):
        self.config = load_config()
        self.theme = self.config.get("theme", "dark")
        self.selected_branch = self.config.get("selected_branch", DEFAULT_BRANCH)
        self.show_update_message = self.config.get("show_update_message", False)
        self.using_custom_colors = self.config.get("using_custom_colors", False)
        self.custom_colors = self.config.get("custom_colors", {})
        self.border_radius = self.config.get("border_radius", DEFAULT_BR)
        self.border_size = self.config.get("border_size", DEFAULT_BS)
        self.border_size_interactables = self.config.get("border_size_interactables", DEFAULT_BSI)
        self.checkbox_radius = self.config.get("checkbox_radius", DEFAULT_CR)
        self.scrollbar_width = self.config.get("scrollbar_width", DEFAULT_SW)
        self.scroll_radius = self.config.get("scroll_radius", DEFAULT_SR)
        dock_area_int = self.config.get("dock_area", Qt.TopDockWidgetArea.value) # Load dock area from config as int
        self.dock_area = Qt.DockWidgetArea(dock_area_int) # Convert int to DockWidgetArea
        self.categories = self.config.get("categories", ["New", "Premium", "Good", "Low Effort", "Bad", "VR", "DLC", "Used"])
        save_config(self.config) # Save categories

    def setup_ui(self):
        # GUI Layout Elements
        fixedspacer = QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        fixedspacerlarger = QSpacerItem(30, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        expandingspacer = QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        theme_layout = QHBoxLayout()
        input_row_layout = QHBoxLayout()
        search_layout = QHBoxLayout()
        table_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        add_button_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create a QDockWidget
        self.dock = QDockWidget("Function Dock", self)
        self.dock.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.dock.setFeatures(QDockWidget.NoDockWidgetFeatures) # Disable detach and close
        self.dock.setFeatures(QDockWidget.DockWidgetMovable)
        dock_widget = QWidget()
        dock_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        dock_layout = QHBoxLayout(dock_widget)
        dock_layout.setAlignment(Qt.AlignTop)
        self.addDockWidget(self.dock_area, self.dock)
        self.dock.dockLocationChanged.connect(self.save_dock_position)

        def add_checkbox_to_dock(layout, text, checked, callback):
            checkbox = QCheckBox(text)
            checkbox.setChecked(checked)
            checkbox.stateChanged.connect(callback)
            layout.addWidget(checkbox)
            return checkbox

        def add_button_to_dock(layout, text, height, callback, icon=None, fixed_width=None, tooltip=None): # Added tooltip parameter
            button = self.create_button(text, height, callback, icon=icon, fixed_width=fixed_width, tooltip=tooltip) # Pass tooltip to create_button
            layout.addWidget(button)
            return button

        # Theme Selection
        self.theme_switch = QComboBox()
        self.theme_switch.addItems(["Dark", "Light", "Ocean", "Forest"])
        self.theme_switch.setCurrentText(self.theme.capitalize())
        self.theme_switch.currentIndexChanged.connect(self.toggle_default_theme)
        dock_layout.addWidget(self.theme_switch)
        dock_layout.addSpacerItem(fixedspacer)

        # Default/Custom Theme Toggle
        self.toggle_theme_checkbox = add_checkbox_to_dock(dock_layout, "Custom Theme", self.using_custom_colors, self.toggle_custom_theme)
        #self.debugCheckbox = add_checkbox_to_dock(dock_layout, "Demo", self.using_custom_colors, self.toggle_custom_theme)
        dock_layout.addSpacerItem(fixedspacerlarger)

        # Dock Buttons
        self.toggle_keys_button = add_button_to_dock(dock_layout, "Show All Keys", BUTTON_HEIGHT, self.toggle_all_keys_visibility, tooltip="Show/Hide all game keys in the table.")
        self.copy_button = add_button_to_dock(dock_layout, "Copy Keys", BUTTON_HEIGHT, self.copy_selected_keys, tooltip="Copy the selected game keys to the clipboard.")
        self.remove_button = add_button_to_dock(dock_layout, "Remove Keys", BUTTON_HEIGHT, self.remove_selected_games, tooltip="Remove the selected games from the list.")
        dock_layout.addSpacerItem(expandingspacer)

        # Update Available Label
        self.update_status_label = QLabel("", self, objectName="update_status_label", alignment=Qt.AlignRight | Qt.AlignVCenter)
        dock_layout.addWidget(self.update_status_label)

        # Dock Buttons with Icons
        self.update_menu_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_update_dialog, icon=UPDATE_ICON, fixed_width=BUTTON_HEIGHT + 2, tooltip="Check for updates or manage update settings.")
        self.manage_categories_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_category_manager, icon=CATEGORY_MANAGER_ICON, fixed_width=BUTTON_HEIGHT + 2, tooltip="Manage game categories.")
        self.color_customization_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_color_config_dialog, icon=CUSTOMIZATION_ICON, fixed_width=BUTTON_HEIGHT + 2, tooltip="Customize the application theme colors.")
        self.hamburger_menu_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_hamburger_menu, icon=MENU_ICON, fixed_width=BUTTON_HEIGHT + 2, tooltip="Open the application menu for import, backup, and password settings.")

        # Finalize Dock
        self.dock.setWidget(dock_widget)

        # Add Games Button
        self.add_button = self.create_button("Add Games", 75, self.add_games, tooltip="Add new games and their keys to the list.")
        add_button_layout.addWidget(self.add_button)

        # Add Games Input Box
        self.input_text = PlainTextInput(
            placeholderText="Add games (one per line, format: Title XXXXX-XXXXX-XXXXX)",
            lineWrapMode=QTextEdit.NoWrap, fixedHeight=75, verticalScrollBarPolicy=Qt.ScrollBarAlwaysOff)
        input_row_layout.addWidget(self.input_text)

        # Enhanced search bar
        self.search_bar = ModernQLineEdit()
        self.search_bar.setPlaceholderText("Search title or key")
        self.search_bar.textChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.search_bar, 3)

        # Add category filter drop-down
        self.category_filter = QComboBox(fixedWidth=105)
        self.category_filter.addItems(["All Categories"] + self.categories)
        self.category_filter.currentTextChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.category_filter)

        # Found Games Count label
        self.found_count_label = QLabel("Found Games: 0", self, objectName="FoundCountLabel")
        search_layout.addWidget(self.found_count_label)

        # Game list section
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Game Title", "Steam Key", "Category"])
        self.table_widget.setColumnWidth(0, 400) # Set width for the "Title" column
        self.table_widget.setColumnWidth(1, 240) # Set width for the "Steam Key" column
        self.table_widget.setColumnWidth(2, 140) # Set width for the "Category" column
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_right_click_menu)
        table_layout.addWidget(self.table_widget)

        # Final GUI Layout
        main_layout.addLayout(theme_layout)
        input_row_layout.addLayout(add_button_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(input_row_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(search_layout)
        main_layout.addSpacing(3)
        main_layout.addLayout(table_layout, 1) # Use stretch factor of 1 to make the table widget take up the remaining space
        main_layout.addSpacing(5)
        main_layout.addLayout(button_layout)

        # Refresh initial game list
        self.refresh_game_list()

    def open_update_dialog(self):
        update_manager = self.update_manager_ref()
        if update_manager is not None:
            dialog = UpdateDialog(self)
            dialog.update_signal.connect(lambda text, visible: self.update_label_signal.emit(text, visible))
            dialog.exec()

    def handle_update_status_label(self, text, visible):
        self.update_status_label.setText(text)
        self.update_status_label.setVisible(visible)

        # Cancel any existing timer
        if self.message_timer and self.message_timer.isActive():
            self.message_timer.stop()

        # Only set a timeout if the message should be temporary
        if visible and text not in ["Update Available"]:
            self.message_timer = QTimer()
            self.message_timer.setSingleShot(True)
            self.message_timer.timeout.connect(lambda: self.update_label_signal.emit("", False))
            self.message_timer.start(2000)

    def create_button(self, text, height, slot, icon=None, fixed_width=None, tooltip=None): # Added tooltip parameter
        button = QPushButton(text)
        button.setFixedHeight(height)
        if icon:
            theme = Theme(self.theme, self.custom_colors if self.using_custom_colors else None)
            if theme:
                icon_data = icon.replace("{{COLOR}}", theme.get_icon_color())
                button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon_data.encode()))))
        if fixed_width:
            button.setFixedWidth(fixed_width)
        #if tooltip:
            #Tooltip(button, tooltip)  # Use pyqttooltip for tooltips
        button.clicked.connect(slot)
        return button

    def toggle_default_theme(self):
        current_theme = self.theme
        selected_theme = self.theme_switch.currentText().lower()
        if selected_theme in ["dark", "light", "ocean", "forest"]:
            if selected_theme != current_theme:
                self.theme = selected_theme
                self.apply_theme()
                self.save_config()
        else:
            print("Invalid theme selected")

    def toggle_custom_theme(self):
        self.using_custom_colors = self.toggle_theme_checkbox.isChecked()
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        if self.using_custom_colors:
            theme = Theme(self.theme, self.custom_colors, self.border_radius, self.border_size, self.border_size_interactables, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        else:
            theme = Theme(self.theme)
        self.setStyleSheet(theme.generate_stylesheet())
        self.update_icons(theme)

    def apply_custom_colors(self, custom_colors, border_radius, border_size, border_size_interactables, checkbox_radius, scroll_radius, scrollbar_width):
        self.using_custom_colors = True
        self.custom_colors = custom_colors
        theme = Theme(self.theme, custom_colors, border_radius, border_size, border_size_interactables, checkbox_radius, scroll_radius, scrollbar_width)
        self.setStyleSheet(theme.generate_stylesheet())
        self.update_icons(theme)

    def update_icons(self, theme):
        icons = [
            (self.update_menu_button, UPDATE_ICON),
            (self.color_customization_button, CUSTOMIZATION_ICON),
            (self.hamburger_menu_button, MENU_ICON),
            (self.manage_categories_button, CATEGORY_MANAGER_ICON)
        ]
        color = theme.get_icon_color()
        for button, icon in icons:
            button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon.replace("{{COLOR}}", color).encode()))))

    def censor_key(self, key):
        return '-'.join(['*' * len(part) for part in key.split('-')])

    def toggle_all_keys_visibility(self):
        self.show_keys = not self.show_keys
        self.update_toggle_keys_button_text()
        if not self.show_keys:
            self.visible_keys.clear()
        self.refresh_game_list()

    def update_toggle_keys_button_text(self):
        self.toggle_keys_button.setText("Hide All Keys" if self.show_keys else "Show All Keys")


    def toggle_selected_keys(self):
        for row in set(item.row() for item in self.table_widget.selectedItems()):
            unique_id = self.row_to_unique_id[row]
            if unique_id in self.visible_keys:
                self.visible_keys.remove(unique_id)
            else:
                self.visible_keys.add(unique_id)
        self.refresh_game_list()

    def open_color_config_dialog(self):
        self.toggle_theme_checkbox.setChecked(True)
        dialog = ColorConfigDialog(self, self.custom_colors, self.theme, self.border_radius, self.border_size, self.border_size_interactables, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        if dialog.exec() == QDialog.Accepted:
            self.custom_colors = dialog.current_colors
            self.border_radius = dialog.border_radius
            self.border_size = dialog.border_size
            self.border_size_interactables = dialog.border_size_interactables
            self.checkbox_radius = dialog.checkbox_radius
            self.scrollbar_width = dialog.scrollbar_width
            self.scroll_radius = dialog.scroll_radius
            self.apply_theme()
            self.save_config()

    def create_menu_action(self, menu, text, slot):
        action = QAction(text, self)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def open_hamburger_menu(self):
        menu = QMenu(self)
        self.create_menu_action(menu, "Import Games", self.import_games)
        self.create_menu_action(menu, "Backup Games", self.manual_game_data_backup)
        self.create_menu_action(menu, "Change Password", self.encryption_manager.change_password)
        pos = self.hamburger_menu_button.mapToGlobal(QPoint(0, self.hamburger_menu_button.height()))
        pos.setX(pos.x() - menu.sizeHint().width() + self.hamburger_menu_button.width() + 1)
        pos.setY(pos.y() + 4)  # Move the menu down by 4 pixels
        menu.exec(pos)

    def show_right_click_menu(self, position):
        menu = QMenu(self)
        self.create_menu_action(menu, "Toggle Key", self.toggle_selected_keys)
        self.create_menu_action(menu, "Edit", self.edit_selected_game)
        self.create_menu_action(menu, "Copy", self.copy_selected_keys)
        self.create_menu_action(menu, "Remove", self.remove_selected_games)
        set_game_category_menu = QMenu("Set Category", self)
        for category in self.categories:
            action = self.create_menu_action(set_game_category_menu, category, lambda checked, c=category: self.set_game_category(c))
        menu.addMenu(set_game_category_menu)

        # Get the row index from the position
        row = self.table_widget.rowAt(position.y())
        if row >= 0:
            unique_id = self.row_to_unique_id[row]
            self.current_game = self.games[unique_id]
            menu.exec(self.table_widget.viewport().mapToGlobal(position))

    def open_category_manager(self):
        dialog = CategoryManagerDialog(self.categories, self)
        if dialog.exec() == QDialog.Accepted:
            old_categories = self.categories.copy()
            self.categories = dialog.categories
            self.config["categories"] = self.categories
            save_config(self.config)

            # Update all games with renamed categories
            category_map = dialog.category_map
            for game in self.games.values():
                if game["category"] in category_map:
                    game["category"] = category_map[game["category"]]
                elif game["category"] not in self.categories:
                    game["category"] = "New"

            self.save_key_data()
            self.category_filter.clear()
            self.category_filter.addItem("All Categories")
            self.category_filter.addItems(self.categories)
            self.refresh_game_list()

    def parse_input_line(self, line):
        return parse_input_line_global(line) # Call the global parsing function

    def add_games(self):
        input_text = self.input_text.toPlainText().strip()
        added_count = 0
        invalid_lines = [] # Store tuples of (line, error_message)
        already_exists = set()
        added_titles_str = ""  # Initialize the string to build upon

        for line in input_text.split('\n'):
            title, key, error_message = self.parse_input_line(line)
            if title and key:
                if key not in {game["key"] for game in self.games.values()}:
                    unique_id = str(uuid.uuid4())
                    self.games[unique_id] = {"title": title, "key": key, "category": "New"}
                    added_count += 1
                    added_titles_str += title + ", " # Add title to the string
                    if error_message: # Inform about auto-corrections
                        print(f"Line auto-corrected: '{line}'. Added as '{title} {key}'. Message: {error_message}")
                else:
                    already_exists.add(title)
            else:
                invalid_lines.append((line, error_message)) # Store line and error

        self.input_text.clear()

        if added_count == 1:
            added_titles_str = added_titles_str.rstrip(", ") # Remove trailing comma and space
            QMessageBox.information(self, "Success", f"Successfully added {added_titles_str} game")

        if added_count >= 2:
            added_titles_str = added_titles_str.rstrip(", ") # Remove trailing comma and space
            QMessageBox.information(self, "Success", f"Successfully added {added_count} games: {added_titles_str}")

        if invalid_lines:
            error_text = "The following lines had problems:\n"
            for line, error in invalid_lines:
                error_text += f"Line: {line} \nError: {error}\n\n"
            QMessageBox.warning(self, "Invalid Format", error_text.rstrip('\n')) # Show detailed errors

        if already_exists:
            QMessageBox.warning(self, "Duplicate Keys", f"Ignored these titles due to duplicate keys: {', '.join(already_exists)}")

        self.save_key_data()
        self.refresh_game_list()

    def remove_selected_games(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Remove Error", "Please select at least one item to remove")
            return

        reply = QMessageBox.question(self, "Confirm", "Remove selected items?")
        if reply == QMessageBox.Yes:
            removed_titles = []
            for item in selected_items:
                row = item.row()
                unique_id = self.row_to_unique_id[row]
                if unique_id in self.games:
                    removed_titles.append(self.games[unique_id]["title"])
                    del self.games[unique_id]

            if removed_titles:
                removed_titles_str = ", ".join(removed_titles)
                QMessageBox.information(self, "Success", f"Successfully remove: {removed_titles_str}")

            self.save_key_data()
            self.refresh_game_list()

    def edit_selected_game(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Edit Error", "Please select at least one item to edit")
            return

        unique_ids = set()
        for item in selected_items:
            row = item.row()
            unique_id = self.row_to_unique_id[row]
            unique_ids.add(unique_id)

        games_to_edit = [self.games[unique_id] for unique_id in unique_ids]

        dialog = EditGameDialog(self, games_to_edit)
        if dialog.exec() == QDialog.Accepted:
            self.save_key_data()
            self.refresh_game_list()

    def copy_selected_keys(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Copy Error", "Please select at least one item to copy")
            return

        items = ["Regular Copy", "Discord Spoiler Style"]
        item, ok = QInputDialog.getItem(self, "Copy Options", "Choose copy style:", items, 0, False)
        if ok and item:
            self.perform_copy(selected_items, discord=(item == "Discord Spoiler Style"))

    def perform_copy(self, selected_items, discord):
        selected_keys = []
        for item in selected_items:
            row = item.row()
            unique_id = self.row_to_unique_id[row]
            if unique_id in self.games:
                game = self.games[unique_id]
                key = game['key']
                if discord:
                    key = f"||{key}||"  # Add spoiler tags
                selected_keys.append(f"{game['title']}: {key}")

        pyperclip.copy("\n".join(selected_keys))
        QMessageBox.information(self, "Copy Keys", "Keys copied to clipboard")

    def set_game_category(self, category):
        for item in self.table_widget.selectedItems():
            row = item.row()
            unique_id = self.row_to_unique_id[row]
            if unique_id in self.games:
                self.games[unique_id]["category"] = category
        self.save_key_data()
        self.refresh_game_list()

    def refresh_game_list(self):
        search_term = self.search_bar.text().lower()
        category_filter = self.category_filter.currentText()

        # Filter and sort games
        filtered_games = [
            (unique_id, data) for unique_id, data in self.games.items()
            if (search_term in data["title"].lower() or search_term in data["key"].lower()) and
            (category_filter == "All Categories" or data["category"] == category_filter)
        ]
        filtered_games.sort(key=lambda x: x[1]["title"])

        # Update the found games count
        self.found_count_label.setText(f"Found Games: {len(filtered_games)}")
        self.table_widget.setRowCount(len(filtered_games))

        # Map table rows to unique IDs
        self.row_to_unique_id = {i: unique_id for i, (unique_id, _) in enumerate(filtered_games)}

        for i, (unique_id, data) in enumerate(filtered_games):
            # Create table items
            title_item = QTableWidgetItem(data["title"])
            key_item = QTableWidgetItem(data["key"] if self.show_keys or unique_id in self.visible_keys else self.censor_key(data["key"]))
            category_item = QTableWidgetItem(data["category"])

            # Set item flags and alignment
            for item in (title_item, key_item, category_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            key_item.setTextAlignment(Qt.AlignCenter)
            category_item.setTextAlignment(Qt.AlignCenter)

            # Add items to table
            self.table_widget.setItem(i, 0, title_item)
            self.table_widget.setItem(i, 1, key_item)
            self.table_widget.setItem(i, 2, category_item)

    def import_games(self):
        import_games(self)

    def manual_game_data_backup(self):
        manual_game_data_backup(self)

    def load_key_data(self):
        data = self.encryption_manager.load_data()
        if data:
            self.games = json.loads(data)

    def save_key_data(self):
        data_to_save = json.dumps(self.games, indent=4)
        self.encryption_manager.save_data(data_to_save)

    def save_dock_position(self, area):
        if not self.dock.isFloating(): # Only save if the dock is actually docked
            print(f"Saving dock position: {area}, value:{area.value}")
            self.dock_area = area
            self.save_config()

    def save_config(self):
        config = load_config() # Load existing config
        config.update({ # Merge with new values
            "theme": self.theme,
            "selected_branch": self.selected_branch,
            "dock_area": self.dock_area.value,
            "show_update_message": self.show_update_message,
            "using_custom_colors": self.using_custom_colors,
            "custom_colors": self.custom_colors,
            "border_radius": self.border_radius,
            "border_size": self.border_size,
            "border_size_interactables": self.border_size_interactables,
            "checkbox_radius": self.checkbox_radius,
            "scrollbar_width": self.scrollbar_width,
            "scroll_radius": self.scroll_radius
        })
        save_config(config)

    def show_update_message_if_needed(self):
        if self.show_update_message:
            QMessageBox.information(None, "Arooga, new version", f"Successfully updated to version: {CURRENT_BUILD}")
            self.show_update_message = False
            self.save_config()

def main():
    app = QApplication(sys.argv)
    window = SteamKeyManager()
    window.show()
    window.show_update_message_if_needed()
    #app.setStyle('Fusion') # Linux Style
    sys.exit(app.exec())

if __name__ == "__main__":
    main()