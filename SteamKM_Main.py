# SteamKM_Main.py
import json
import sys
import pyperclip
import re
import uuid
import shutil
import os, sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QTableWidget, 
    QTableWidgetItem, QMenu, QMessageBox, QCheckBox, QLineEdit, QFileDialog, QComboBox, QDialog, QFormLayout, 
    QGroupBox, QSpacerItem, QSizePolicy, QDockWidget, QInputDialog
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QPalette, QColor
from PySide6.QtCore import Qt, QPoint, QTimer, QThread, Signal
from SteamKM_Version import CURRENT_BUILD
from SteamKM_Updater import UpdateDialog, UpdateManager
from SteamKM_Themes import ColorConfigDialog, Theme, DEFAULT_BR, DEFAULT_BS, DEFAULT_BSI, DEFAULT_CR, DEFAULT_SR, DEFAULT_SW, BUTTON_HEIGHT
from SteamKM_Icons import UPDATE_ICON, MENU_ICON, CUSTOMIZATION_ICON, CATEGORY_MANAGER_ICON
from SteamKM_Config import load_config, save_config
from SteamKM_Edit_Menu import EditGameDialog
from SteamKM_Category_Menu import CategoryManagerDialog
from SteamKM_Import import merge_imported_games_from_json, merge_imported_games_from_txt

print(os.environ.get("QT_OPENGL")) # Debugging

class PlainTextInput(QTextEdit): # Removes Rich Text Support
    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())

class ModernQLineEdit(QLineEdit): # Improved Search Bar
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText("Search title or key")
        self.setClearButtonEnabled(True)

class SteamKeyManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Key Manager V3 (Beta)")
        self.resize(1005, 600)
        self.data_file = Path("steam_keys.json")
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.icons_dir = os.path.join(self.script_dir, "SteamKM_Icons")

        # Initialize Data
        self.games = {}
        self.visible_keys = set()
        self.show_keys = False
        self.load_initial_data()
        self.load_key_data()
        self.setup_ui()
        self.update_manager = UpdateManager(self, CURRENT_BUILD) # Check For Updates
        self.apply_theme()

    def load_initial_data(self):
        self.config = load_config()
        self.theme = self.config.get("theme", "dark")
        self.selected_branch = self.config.get("selected_branch", "stable")
        self.show_update_message = self.config.get("show_update_message", False)
        self.using_custom_colors = self.config.get("using_custom_colors", False)
        self.custom_colors = self.config.get("custom_colors", {})
        self.border_radius = self.config.get("border_radius", DEFAULT_BR)
        self.border_size = self.config.get("border_size", DEFAULT_BS)
        self.border_size_interactables = self.config.get("border_size_interactables", DEFAULT_BSI)
        self.checkbox_radius = self.config.get("checkbox_radius", DEFAULT_CR)
        self.scrollbar_width = self.config.get("scrollbar_width", DEFAULT_SW)
        self.scroll_radius = self.config.get("scroll_radius", DEFAULT_SR)
        dock_area_int = self.config.get("dock_area", Qt.BottomDockWidgetArea.value) # Load dock area from config as int
        self.dock_area = Qt.DockWidgetArea(dock_area_int) # Convert int to DockWidgetArea
        self.categories = self.config.get("categories", ["Premium", "Good", "Low Effort", "Bad", "VR", "Used", "New"])
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

        def add_button_to_dock(layout, text, height, callback, icon=None, fixed_width=None):
            button = self.create_button(text, height, callback, icon=icon, fixed_width=fixed_width)
            layout.addWidget(button)
            return button

        # Default Theme Toggle
        self.theme_switch = add_checkbox_to_dock(dock_layout, "Dark Mode", self.theme == "dark", self.toggle_default_theme)
        dock_layout.addSpacerItem(fixedspacer)

        # Default/Custom Theme Toggle
        self.toggle_theme_checkbox = add_checkbox_to_dock(dock_layout, "Custom Theme", self.using_custom_colors, self.toggle_custom_theme)
        dock_layout.addSpacerItem(fixedspacerlarger)

        # Dock Buttons
        self.toggle_keys_button = add_button_to_dock(dock_layout, "Toggle All Keys", BUTTON_HEIGHT, self.toggle_all_keys_visibility)
        self.copy_button = add_button_to_dock(dock_layout, "Copy Selected Keys", BUTTON_HEIGHT, self.copy_selected_keys)
        self.remove_button = add_button_to_dock(dock_layout, "Remove Selected Keys", BUTTON_HEIGHT, self.remove_selected_games)
        dock_layout.addSpacerItem(expandingspacer)
        
        # Update Available Label
        self.update_available_label = QLabel("Checking Updates")
        self.update_available_label.setObjectName("update_available_label")
        self.update_available_label.setFixedWidth(95)
        self.update_available_label.setVisible(True)
        dock_layout.addWidget(self.update_available_label)

        # Dock Buttons with Icons
        self.update_menu_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_update_dialog, icon=UPDATE_ICON, fixed_width=BUTTON_HEIGHT + 2)
        self.manage_categories_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_category_manager, icon=CATEGORY_MANAGER_ICON, fixed_width=BUTTON_HEIGHT + 2)
        self.color_customization_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_color_config_dialog, icon=CUSTOMIZATION_ICON, fixed_width=BUTTON_HEIGHT + 2)
        self.hamburger_menu_button = add_button_to_dock(dock_layout, "", BUTTON_HEIGHT, self.open_hamburger_menu, icon=MENU_ICON, fixed_width=BUTTON_HEIGHT + 2)

        # Finalize Dock
        self.dock.setWidget(dock_widget)

        # Add Games Button
        self.add_button = self.create_button("Add Games", 75, self.add_games)
        add_button_layout.addWidget(self.add_button)

        # Add Games Input Box
        self.input_text = PlainTextInput()
        self.input_text.setPlaceholderText("Enter games (one per line, format: Title XXXXX-XXXXX-XXXXX)")
        self.input_text.setLineWrapMode(QTextEdit.NoWrap)
        self.input_text.setFixedHeight(75)
        self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        input_row_layout.addWidget(self.input_text)
        
        # Enhanced search bar
        self.search_bar = ModernQLineEdit()
        self.search_bar.textChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.search_bar, 3)

        # Add category filter drop-down
        self.category_filter = QComboBox()
        self.category_filter.setFixedWidth(105)
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(self.categories)
        self.category_filter.currentTextChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.category_filter)  # Add to the nested layout

        # Found Games Count label
        self.found_count_label = QLabel("Found Games: 0")
        self.found_count_label.setObjectName("FoundCountLabel")
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
                    
    def parse_input_line(self, line):
        match = re.match(r'(.+?)\s+([A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5})', line)
        return match.groups() if match else (None, None)

    def create_button(self, text, height, slot, icon=None, fixed_width=None):
        button = QPushButton(text)
        button.setFixedHeight(height)
        if icon and (theme := Theme(self.theme, self.custom_colors if self.using_custom_colors else None)):
            icon_data = icon.replace("{{COLOR}}", theme.get_icon_color())
            button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon_data.encode()))))
        if fixed_width:
            button.setFixedWidth(fixed_width)
        button.clicked.connect(slot)
        return button
        
    def toggle_default_theme(self):
        self.theme = "dark" if self.theme_switch.isChecked() else "light"
        self.apply_theme()
        self.save_config()

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

    def open_update_dialog(self):
        dialog = UpdateDialog(self, CURRENT_BUILD)
        dialog.exec()
    
    def toggle_all_keys_visibility(self):
        self.show_keys = not self.show_keys
        if not self.show_keys:
            self.visible_keys.clear()
        self.refresh_game_list()
                
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

    def open_hamburger_menu(self):
        menu = QMenu(self)

        import_action = QAction("Import Games", self)
        import_action.triggered.connect(self.import_games)
        menu.addAction(import_action)

        backup_action = QAction("Backup Games", self)
        backup_action.triggered.connect(self.manual_game_data_backup)
        menu.addAction(backup_action)

        pos = self.hamburger_menu_button.mapToGlobal(QPoint(0, self.hamburger_menu_button.height()))
        pos.setX(pos.x() - menu.sizeHint().width() + self.hamburger_menu_button.width() + 1)
        pos.setY(pos.y() + 4) # Move the menu down by 4 pixels
        menu.exec(pos)
        
    def show_right_click_menu(self, position):
        menu = QMenu(self)
        reveal_action = QAction("Toggle Key")
        reveal_action.triggered.connect(self.toggle_selected_keys)
        menu.addAction(reveal_action)

        edit_action = QAction("Edit")
        edit_action.triggered.connect(self.edit_selected_game)
        menu.addAction(edit_action)

        copy_action = QAction("Copy")
        copy_action.triggered.connect(self.copy_selected_keys)
        menu.addAction(copy_action)

        remove_action = QAction("Remove")
        remove_action.triggered.connect(self.remove_selected_games)
        menu.addAction(remove_action)

        set_game_category_menu = QMenu("Set Category", self)
        for category in self.categories:
            action = QAction(category, self)
            action.triggered.connect(lambda checked, c=category: self.set_game_category(c))
            set_game_category_menu.addAction(action)
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

    def add_games(self):
        input_text = self.input_text.toPlainText().strip()
        added_count = 0
        invalid_lines = []
        already_exists = set()
        added_titles = []

        for line in input_text.split('\n'):
            title, key = self.parse_input_line(line)
            if title and key:
                if key not in {game["key"] for game in self.games.values()}:
                    unique_id = str(uuid.uuid4())
                    self.games[unique_id] = {"title": title, "key": key, "category": "New"}
                    added_count += 1
                    added_titles.append(title)
                else:
                    already_exists.add(title)
            else:
                invalid_lines.append(line)
        
        self.input_text.clear()
        
        if added_count > 0:
            QMessageBox.information(self, "Success", f"Added {added_count} game(s) successfully: {', '.join(added_titles)}")
        
        if invalid_lines:
            QMessageBox.warning(self, "Invalid Format", "Some lines had an invalid format")
        
        if already_exists:
            QMessageBox.warning(self, "Duplicate Keys", f"The following games were ignored: {', '.join(already_exists)}")

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
                QMessageBox.information(self, "Success", f"Successfully removed {removed_titles_str}")
            
            self.save_key_data()
            self.refresh_game_list()

    def edit_selected_game(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Edit Error", "Please select at least one item to edit.")
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
        
        selected_keys = []
        for item in selected_items:
            row = item.row()
            unique_id = self.row_to_unique_id[row]
            if unique_id in self.games:
                game = self.games[unique_id]
                selected_keys.append(f"{game['title']}: {game['key']}")
        
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
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("JSON and Text Files (*.json *.txt)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                import_file = Path(file_paths[0])
                try:
                    if import_file.suffix.lower() == '.json':
                        added_count, added_titles = merge_imported_games_from_json(import_file, self.games, self.categories)
                    elif import_file.suffix.lower() == '.txt':
                        added_count, added_titles = merge_imported_games_from_txt(import_file, self.games, self.categories)
                    else:
                        QMessageBox.warning(self, "Error", "Unsupported file type.")
                    
                    if added_count > 0:
                        added_titles_str = ", ".join(added_titles)
                        self.save_key_data()
                        self.refresh_game_list()
                        QMessageBox.information(self, "Success", f"Successfully imported {added_count} game(s): {added_titles_str}")
                    else:
                        QMessageBox.information(self, "Error", f"Didn't find any new games to import")
                
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to import games: {str(e)}")

    def manual_game_data_backup(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self,"Save Backup File", "", "JSON Files (*.json)", options=options)
        if file_name:
            shutil.copy(self.data_file, file_name)
            QMessageBox.information(self, "Success", "Data backed up successfully.")
        
    def load_key_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as file:
                    self.games = json.load(file)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load data: {str(e)}")
                self.games = {}

    def save_dock_position(self, area):
        if not self.dock.isFloating(): # Only save if the dock is actually docked
            print(f"Saving dock position: {area}, value:{area.value}")
            self.dock_area = area
            self.save_config()

    def save_key_data(self):
        backup_file = self.data_file.with_suffix('.json.bak')
        if self.data_file.exists():
            shutil.copy(self.data_file, backup_file)
        self.data_file.write_text(json.dumps(self.games, indent=4))

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
    sys.exit(app.exec())

if __name__ == "__main__":
    main()