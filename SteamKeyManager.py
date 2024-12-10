from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTableWidget, QTableWidgetItem, QMenu, QMessageBox, QCheckBox, QLineEdit,
    QFileDialog, QComboBox, QColorDialog, QDialog, QFormLayout, QGroupBox, QSlider, QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtCore import Qt, QPoint
from pathlib import Path
import json
import sys
import pyperclip
import re
import uuid
import shutil
import os

from SteamKeyManager_Updater import check_for_updates, download_update
from SteamKeyManager_Themes import Theme

CURRENT_BUILD = "1.00"

BUTTON_HEIGHT = 33
DEFAULT_BR = 5 # Border Radius
DEFAULT_BS = 0 # Border Size
DEFAULT_CR = 4 # Checkbox Radius
DEFAULT_SR = 3 # Scrollbar Radius
DEFAULT_SW = 12 # Scrollbar Width
COLOR_PICKER_BUTTON_STYLE = "border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;"
COLOR_RESET_BUTTON_STYLE = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: 0px;"

class ColorConfigDialog(QDialog):
    def __init__(self, parent=None, current_colors=None, theme="dark", border_radius=DEFAULT_BR, border_size=DEFAULT_BS, checkbox_radius=DEFAULT_CR, scroll_radius=DEFAULT_SR, scrollbar_width=DEFAULT_SW):
        super().__init__(parent)
        self.setWindowTitle("Color Customization")
        self.resize(500, 700)
        self.theme = theme
        self.current_colors = current_colors if current_colors else {}
        self.border_radius = border_radius
        self.border_size = border_size
        self.checkbox_radius = checkbox_radius
        self.scroll_radius = scroll_radius
        self.scrollbar_width = scrollbar_width
        self.color_pickers = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        scroll_area_layout = QVBoxLayout(scroll_area_widget)

        groups = [
            ("General Colors", [
                ("Text", "text_color"),
                ("Background", "main_background"),
                ("Search Background", "search_bar_background"),
                ("Add Games Background", "add_games_background"),
                ("Found Games Background", "found_games_background"),
            ]),
            ("Border Colors", [
                ("Generic Border", "generic_border_color"),
                ("Interactables Border", "interactables_border_color"),
                ("Game List Border", "table_border_color"),
            ]),
            ("Game List", [
                ("Game List Background", "table_background"),
                ("Game List Gridline", "table_gridline_color"),
                ("Game List Selected Item", "table_item_selected"),
            ]),
            ("Scrollbar", [
                ("Scrollbar", "scrollbar_handle"),
                ("Scrollbar Background", "scrollbar_background"),
            ]),
            ("Interactables", [
                ("Button Hover", "button_hover"),
                ("Button Pressed", "button_pressed"),
                ("Button Background", "button_background"),
                ("Checkbox Checked", "checkbox_background_checked"),
                ("Checkbox Unchecked", "checkbox_background_unchecked"),
                ("Category Background", "combobox_background"),
                ("Category Dropdown Background", "combobox_dropdown_background"),
            ]),
        ]

        for title, elements in groups:
            group = QGroupBox(title)
            self.setup_group(group, elements)
            scroll_area_layout.addWidget(group)
            scroll_area_layout.addSpacing(10)

        self.setup_border_group()
        scroll_area_layout.addWidget(self.border_group)

        main_layout.addWidget(scroll_area)

        apply_button = QPushButton("Apply and Save")
        apply_button.clicked.connect(self.apply_colors)
        main_layout.addWidget(apply_button)

    def setup_group(self, group, elements):
        layout = QFormLayout()
        group.setLayout(layout)
        [self.add_color_picker(layout, label, key) for label, key in elements]

    def add_color_picker(self, layout, label, key):
        color_name = self.current_colors.get(key, "")
        button = QPushButton(color_name or "Default")
        button.setFixedSize(150, BUTTON_HEIGHT)
        button.clicked.connect(lambda checked, btn=button, k=key: self.choose_color(btn, k))
        reset_button = QPushButton("X")
        reset_button.setObjectName("resetButton")
        reset_button.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
        reset_button.clicked.connect(lambda checked, btn=button, k=key: self.reset_color(btn, k))
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addWidget(reset_button)
        layout.addRow(label, button_layout)
        self.color_pickers[key] = button
        button.setStyleSheet(f""" QPushButton {{{ COLOR_PICKER_BUTTON_STYLE }}} """)
        reset_button.setStyleSheet(f""" QPushButton {{{ COLOR_RESET_BUTTON_STYLE }}} """)

        if color_name:
            self.set_button_color(button, color_name)
        else:
            self.update_default_button_style(button)

    def setup_border_group(self):
        self.border_group = QGroupBox("Border Size and Radius")
        layout = QVBoxLayout()
        self.border_group.setLayout(layout)

        sliders = [
            ("Border Radius", "border_radius", 0, 13, self.update_border_radius, DEFAULT_BR),
            ("Border Size", "border_size", 0, 3, self.update_border_size, DEFAULT_BS),
            ("Checkbox Radius", "checkbox_radius", 0, 7, self.update_checkbox_radius, DEFAULT_CR),
            ("Scrollbar Width", "scrollbar_width", 8, 14, self.update_scrollbar_width, DEFAULT_SW),
            ("Scroll Radius", "scroll_radius", 0, self.scrollbar_width // 2, self.update_scroll_radius, DEFAULT_SR)
        ]

        [self.add_slider_row(layout, label, key, min_val, max_val, update_func, default_val) for label, key, min_val, max_val, update_func, default_val in sliders]

    def add_slider_row(self, layout, label, key, min_val, max_val, update_func, default_val):
        label_widget = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(getattr(self, key))
        slider.valueChanged.connect(update_func)
        value_label = QLabel(str(getattr(self, key)))
        reset_button = QPushButton("X")
        reset_button.setObjectName("resetButton")
        reset_button.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
        reset_button.clicked.connect(lambda checked, s=slider, d=default_val, v=value_label: self.reset_slider(s, d, v))
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(label_widget)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(value_label)
        slider_layout.addWidget(reset_button)
        layout.addLayout(slider_layout)
        setattr(self, f"{key}_slider", slider)
        setattr(self, f"{key}_value_label", value_label)

    def choose_color(self, button, key):
        color = QColorDialog.getColor(QColor(button.text()), self, f"Choose {key} Color")
        if color.isValid():
            color_name = color.name()
            button.setText(color_name)
            self.set_button_color(button, color_name)
            self.current_colors[key] = color_name
            self.update_preview()
        else:
            button.setText("Default")
            self.update_default_button_style(button)
            self.current_colors.pop(key, None)
            self.update_preview()

    def set_button_color(self, button, color_name):
        button.setStyleSheet(f"background-color: {color_name}; color: {self.contrast_color(color_name)}; {COLOR_PICKER_BUTTON_STYLE};")

    def update_default_button_style(self, button):
        text_color = "black" if self.theme == "light" else "white"
        button.setStyleSheet(f"color: {text_color}; {COLOR_PICKER_BUTTON_STYLE};")

    def contrast_color(self, hex_color):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#FFFFFF"

    def apply_colors(self):
        self.accept()

    def update_preview(self):
        self.parent().apply_custom_colors(self.current_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)

    def update_value(self, key, value, value_label):
        setattr(self, key, value)
        value_label.setText(f"{value}")
        self.update_preview()

    def update_border_radius(self, value):
        self.update_value("border_radius", value, self.border_radius_value_label)

    def update_border_size(self, value):
        self.update_value("border_size", value, self.border_size_value_label)

    def update_checkbox_radius(self, value):
        self.update_value("checkbox_radius", value, self.checkbox_radius_value_label)

    def update_scrollbar_width(self, value):
        max_radius = value // 2
        self.scroll_radius_slider.setMaximum(max_radius)
        if self.scroll_radius > max_radius:
            self.update_value("scroll_radius", max_radius, self.scroll_radius_value_label)
        else:
            self.update_value("scrollbar_width", value, self.scrollbar_width_value_label)

    def update_scroll_radius(self, value):
        self.update_value("scroll_radius", value, self.scroll_radius_value_label)

    def reset_color(self, button, key):
        button.setText("Default")
        self.update_default_button_style(button)
        self.current_colors.pop(key, None)
        self.update_preview()

    def reset_slider(self, slider, default_val, value_label):
        slider.setValue(default_val)
        value_label.setText(str(default_val))
        self.update_preview()

class EditGameDialog(QDialog):
    def __init__(self, parent=None, games=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Games")
        self.resize(400, 350)
        self.games = games if games else []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        scroll_area_layout = QVBoxLayout(scroll_area_widget)

        self.group_boxes = []

        for idx, game in enumerate(self.games):
            group_box = QGroupBox(f"Game {idx + 1}")
            form_layout = QFormLayout()

            title_edit = QLineEdit(game["title"])
            title_edit.setFixedHeight(BUTTON_HEIGHT)
            form_layout.addRow("Title:", title_edit)

            key_edit = QLineEdit(game["key"])
            key_edit.setFixedHeight(BUTTON_HEIGHT)
            form_layout.addRow("Key:", key_edit)

            category_combo = QComboBox()
            category_combo.addItems(["Premium", "Good", "Low Effort", "Bad", "VR", "Used", "New"])
            category_combo.setCurrentText(game["category"])
            category_combo.setFixedHeight(BUTTON_HEIGHT)
            form_layout.addRow("Category:", category_combo)

            group_box.setLayout(form_layout)
            scroll_area_layout.addWidget(group_box)
            scroll_area_layout.addSpacing(10)

            self.group_boxes.append((group_box, title_edit, key_edit, category_combo))

        main_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(apply_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def apply_changes(self):
        for idx, (group_box, title_edit, key_edit, category_combo) in enumerate(self.group_boxes):
            self.games[idx]["title"] = title_edit.text()
            self.games[idx]["key"] = key_edit.text()
            self.games[idx]["category"] = category_combo.currentText()
        self.accept()

class SteamKeyManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Key Manager V3 (Beta)")
        self.resize(850, 600)
        self.data_file = Path("steam_keys.json")
        self.config_file = Path("manager_settings.json")
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.icons_dir = os.path.join(self.script_dir, "SteamKM_Icons")
        
        # Initialize data
        self.categories = ["Premium", "Good", "Low Effort", "Bad", "VR", "Used", "New"]
        self.games = {}
        self.visible_keys = set()
        self.show_keys = False
        self.using_custom_colors = False
        self.custom_colors = {}
        self.theme = "dark"
        self.border_radius = DEFAULT_BR
        self.border_size = DEFAULT_BS
        self.checkbox_radius = DEFAULT_CR
        self.scrollbar_width = DEFAULT_SW
        self.scroll_radius = DEFAULT_SR
        
        # Load data
        self.load_key_data()
        self.load_config()
        
        # Set up UI
        self.setup_ui()
        
        # Apply initial theme
        if self.using_custom_colors:
            self.apply_custom_colors(self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        else:
            self.apply_theme(self.theme)

    def setup_ui(self):
        # GUI Layout Elements
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
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

        # Default Theme Toggle
        self.theme_switch = QCheckBox("Dark Mode")
        self.theme_switch.setChecked(self.theme == "dark")
        self.theme_switch.stateChanged.connect(self.toggle_default_theme)
        theme_layout.addWidget(self.theme_switch)

        # Default/Custom Theme Toggle
        self.toggle_theme_checkbox = QCheckBox("Use Custom Colors")
        self.toggle_theme_checkbox.setChecked(self.using_custom_colors)
        self.toggle_theme_checkbox.stateChanged.connect(self.toggle_custom_theme)
        theme_layout.addWidget(self.toggle_theme_checkbox)

        # Buttons
        self.update_button = self.create_button(text="",  height=BUTTON_HEIGHT, fixed_width=BUTTON_HEIGHT + 2, slot=self.check_updates, 
            icon=os.path.join(self.icons_dir, "update_icon.svg"))
        self.color_config_button = self.create_button(text="",  height=BUTTON_HEIGHT, fixed_width=BUTTON_HEIGHT + 2, slot=self.open_color_config_dialog, 
            icon=os.path.join(self.icons_dir, "color-picker.svg"))
        self.hamburger_menu_button = self.create_button(text="",  height=BUTTON_HEIGHT, fixed_width=BUTTON_HEIGHT + 2, slot=self.show_hamburger_menu, 
            icon=os.path.join(self.icons_dir, "menu.svg"))
        self.add_button = self.create_button("Add Games", 75, self.add_games)
        self.toggle_keys_button = self.create_button("Toggle All Keys", BUTTON_HEIGHT, self.toggle_all_keys_visibility)
        self.copy_button = self.create_button("Copy Selected Keys", BUTTON_HEIGHT, self.copy_selected_keys)
        self.remove_button = self.create_button("Remove Selected", BUTTON_HEIGHT, self.remove_selected_games)

        theme_layout.addSpacerItem(spacer)
        theme_layout.addWidget(self.update_button)
        theme_layout.addWidget(self.color_config_button)
        theme_layout.addWidget(self.hamburger_menu_button)
        add_button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.toggle_keys_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.remove_button)
        
        # Add Games Input Box
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter games (one per line, format: Title XXXXX-XXXXX-XXXXX)")
        self.input_text.setLineWrapMode(QTextEdit.NoWrap)
        self.input_text.setFixedHeight(75)
        self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        input_row_layout.addWidget(self.input_text)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by title or key")
        self.search_bar.setFixedHeight(BUTTON_HEIGHT)
        self.search_bar.textChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.search_bar)

        # Add category filter drop-down
        self.category_filter = QComboBox()
        self.category_filter.setFixedHeight(BUTTON_HEIGHT)
        self.category_filter.setFixedWidth(140)
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(self.categories)
        self.category_filter.currentTextChanged.connect(self.refresh_game_list)
        search_layout.addWidget(self.category_filter, 1)
        
        # Found Games Count label
        self.found_count_label = QLabel("Found Games: 0")
        self.found_count_label.setObjectName("foundCountLabel")
        self.found_count_label.setFixedHeight(BUTTON_HEIGHT)
        search_layout.addWidget(self.found_count_label)

        # Game list section
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Game Title", "Steam Key", "Category"])
        self.table_widget.setColumnWidth(0, 400)  # Set width for the "Title" column
        self.table_widget.setColumnWidth(1, 240)  # Set width for the "Steam Key" column
        self.table_widget.setColumnWidth(2, 140)  # Set width for the "Category" column
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
        main_layout.addLayout(table_layout, 1)  # Use stretch factor of 1 to make the table widget take up the remaining space
        main_layout.addSpacing(5)
        main_layout.addLayout(button_layout)

        # Refresh initial game list
        self.refresh_game_list()

        # Apply initial theme
        if self.using_custom_colors:
            self.apply_custom_colors(self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        else:
            self.apply_theme(self.theme)

    def check_updates(self):
        latest_version = check_for_updates()
        if latest_version is None:
            QMessageBox.warning(self, "Update Check", "Failed to check for updates. Please try again later.")
        elif latest_version == CURRENT_BUILD:
            QMessageBox.information(self, "Update Check", f"You're already on the latest build {CURRENT_BUILD}")
        else:
            reply = QMessageBox.question(self, "New Version Available", f"New {latest_version} is available. Do you want to update?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                download_update(latest_version)
    
    def create_button(self, text, height, slot, icon=None, fixed_width=None):
        button = QPushButton(text)
        button.setFixedHeight(height)
        if icon:
            button.setIcon(QIcon(icon))
        if fixed_width:
            button.setFixedWidth(fixed_width)
        button.clicked.connect(slot)
        return button
            
    def parse_input_line(self, line):
        match = re.match(r'(.+?)\s+([A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5})', line)
        return match.groups() if match else (None, None)

    def show_hamburger_menu(self):
        menu = QMenu(self)

        # Add version label
        version_action = QAction(f"Version: {CURRENT_BUILD}", self)
        version_action.setEnabled(False)
        menu.addAction(version_action)
        menu.addSeparator()

        import_action = QAction("Import Games", self)
        import_action.triggered.connect(self.import_games)
        menu.addAction(import_action)
        backup_action = QAction("Backup Games", self)
        backup_action.triggered.connect(self.manual_game_data_backup)
        menu.addAction(backup_action)

        pos = self.hamburger_menu_button.mapToGlobal(QPoint(0, self.hamburger_menu_button.height()))
        pos.setX(pos.x() - menu.sizeHint().width() + self.hamburger_menu_button.width() + 1)
        pos.setY(pos.y() + 4)  # Move the menu down by 4 pixels
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

    def toggle_default_theme(self):
        self.theme = "dark" if self.theme_switch.isChecked() else "light"
        if self.using_custom_colors:
            self.apply_custom_colors(self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        else:
            self.apply_theme(self.theme)
        self.save_config()

    def toggle_custom_theme(self):
        self.using_custom_colors = self.toggle_theme_checkbox.isChecked()
        if self.using_custom_colors:
            self.apply_custom_colors(self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        else:
            self.apply_theme(self.theme)
        self.save_config()

    def apply_theme(self, theme):
        theme = Theme(theme=theme)
        self.setStyleSheet(theme.generate_stylesheet())

    def apply_custom_colors(self, colors, border_radius, border_size, checkbox_radius, scroll_radius, scrollbar_width):
        theme = Theme(theme=self.theme, custom_colors=colors, border_radius=border_radius, border_size=border_size, checkbox_radius=checkbox_radius, scroll_radius=scroll_radius, scrollbar_width=scrollbar_width)
        self.setStyleSheet(theme.generate_stylesheet())

    def open_color_config_dialog(self):
        self.toggle_theme_checkbox.setChecked(True)
        dialog = ColorConfigDialog(self, self.custom_colors, self.theme, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
        if dialog.exec() == QDialog.Accepted:
            self.custom_colors = dialog.current_colors
            self.using_custom_colors = True
            self.border_radius = dialog.border_radius
            self.border_size = dialog.border_size
            self.checkbox_radius = dialog.checkbox_radius
            self.scrollbar_width = dialog.scrollbar_width
            self.scroll_radius = dialog.scroll_radius
            self.apply_custom_colors(self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)
            self.save_config()
    
    def censor_key(self, key):
        return '-'.join(['*' * len(part) for part in key.split('-')])
    
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
        file_dialog.setNameFilter("JSON Files (*.json)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                import_file = Path(file_paths[0])
                try:
                    self.merge_imported_games(import_file)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to import games: {str(e)}")

    def merge_imported_games(self, import_file):
        try:
            with open(import_file, 'r') as file:
                imported_data = json.load(file)
            
            added_count = [0]
            added_titles = []

            def add_game(title, code, category):
                if title and code and not any(game["key"] == code for game in self.games.values()):
                    unique_id = str(uuid.uuid4())
                    self.games[unique_id] = {"title": title, "key": code, "category": category}
                    added_count[0] += 1  # Increment the count
                    added_titles.append(title)

            if isinstance(imported_data, list):
                for game in imported_data:
                    add_game(game.get("title"), game.get("code"), game.get("category", "New"))
            elif isinstance(imported_data, dict):
                for game in imported_data.values():
                    add_game(game.get("title"), game.get("key"), game.get("category", "New"))
            
            if added_count[0] > 0:
                added_titles_str = ", ".join(added_titles)
                self.save_key_data()
                self.refresh_game_list()
                QMessageBox.information(self, "Success", f"Successfully imported {added_count[0]} game(s): {added_titles_str}")
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

    def save_key_data(self):
        backup_file = self.data_file.with_suffix('.json.bak')
        if self.data_file.exists():
            shutil.copy(self.data_file, backup_file)
        self.data_file.write_text(json.dumps(self.games, indent=4))

    def load_config(self):
        if self.config_file.exists():
            try:
                config = json.loads(self.config_file.read_text())
                self.theme = config.get("theme", "dark")
                self.using_custom_colors = config.get("using_custom_colors", False)
                self.custom_colors = config.get("custom_colors", {})
                self.border_radius = config.get("border_radius", DEFAULT_BR)
                self.border_size = config.get("border_size", DEFAULT_BS)
                self.checkbox_radius = config.get("checkbox_radius", DEFAULT_CR)
                self.scrollbar_width = config.get("scrollbar_width", DEFAULT_SW)
                self.scroll_radius = config.get("scroll_radius", DEFAULT_SR)
            except json.JSONDecodeError:
                self.theme = "dark"
                self.using_custom_colors = False
                self.custom_colors = {}
                self.border_radius = DEFAULT_BR
                self.border_size = DEFAULT_BS
                self.checkbox_radius = DEFAULT_CR
                self.scrollbar_width = DEFAULT_SW
                self.scroll_radius = DEFAULT_SR

    def save_config(self):
        config = {
            "theme": self.theme,
            "using_custom_colors": self.using_custom_colors,
            "custom_colors": self.custom_colors,
            "border_radius": self.border_radius,
            "border_size": self.border_size,
            "checkbox_radius": self.checkbox_radius,
            "scrollbar_width": self.scrollbar_width,
            "scroll_radius": self.scroll_radius,
        }
        self.config_file.write_text(json.dumps(config, indent=4))

def main():
    app = QApplication(sys.argv)
    window = SteamKeyManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
