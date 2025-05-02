# Main.py
import json
import sys
import os, sys
import weakref
import logging
from PySide6.QtWidgets import *
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QColor
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from Version import CURRENT_BUILD
from Updater import UpdateDialog, AutomaticUpdateCheck
from Theme_Menu import ColorConfigDialog
from Themes import Theme
from CustomWidgets import ModernQLineEdit, RoundedImage, CenteredIconContainer, CustomCheckBox
from Icons import UPDATE_ICON, CUSTOMIZATION_ICON, CATEGORY_MANAGER_ICON, PLUS_ICON, COG_ICON
from Config import ConfigManager, CONFIG_FILE_PATH, GAME_PICTURES_DIR, ICON_BUTTON_WIDTH, HORIZONTAL_SPACING, UI_MARGIN, TABLE_ICON_WIDTH, TABLE_ICON_HEIGHT, TABLE_CELL_RADIUS, VERTICAL_SPACING, VERTICAL_SPACING_SMALL, check_old_file_structure, migrate_files
from Game_Management import edit_selected_games, add_games, remove_selected_games, copy_selected_keys
from Category_Menu import CategoryManagerDialog
from Settings_Menu import SettingsMenuDialog
from Encryption import EncryptionManager
from Import_Backup import import_games, manual_game_data_backup, parse_input_line_global
from Steam_API import SteamFetchManager, handle_browser_open, get_rating_color, format_rating_text
from UI_Handler import apply_merged_edges

class SteamKeyManager(QMainWindow):
    status_message_label = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Key Manager V3 (Beta)")
        self.setMinimumSize(655, 360)
        self.resize(1210, 650)
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.icons_dir = os.path.join(self.script_dir, "Icons")
        self.cache = {}
        self.icons_folder = str(GAME_PICTURES_DIR)
        os.makedirs(self.icons_folder, exist_ok=True)  # Ensure the game_pictures directory exists
        self.color_config_dialog = None
        self.current_stylesheet = ""
        self._theme_cache = {}  # Add cache for theme instances
        
        # Sorting variables
        self.current_sort_column = 1  # Default sort column (Title)
        self.current_sort_order = Qt.AscendingOrder  # Default sort order
        
        # Initialize config manager
        self.config_manager = ConfigManager()

        # Initialize Data
        self.games = {}
        self.visible_keys = set()
        self.show_keys = False
        self.encryption_manager = EncryptionManager(self)
        self.load_initial_data()
        self.load_key_data()
        self.setup_ui()
        self.apply_theme()
        
        # Initialize Steam fetcher manager
        self.steam_manager = SteamFetchManager(self, self.table_widget, self.games, self.icons_folder)
        self.steam_manager.set_status_label(self.fetch_status_label)
        self.steam_manager.set_fetch_button(self.fetch_steam_button)
        self._patch_fetch_button_state()
        
        # Apply the merged edges styling based on config
        self.apply_merged_edges_style()

        # Initialize Update Checker
        self.update_manager = AutomaticUpdateCheck(self, self.cache)
        self.update_manager_ref = weakref.ref(self.update_manager)
        self.status_message_label.connect(self.handle_status_message_label)
        self.update_manager.update_status_signal.connect(self.handle_status_message_label)
        self.message_timer = None
        self.auto_update_check = self.config_manager.get("auto_update_check")

    def _patch_fetch_button_state(self):
        """Wrap SteamFetchManager.set_fetch_button_state to also enable/disable editing buttons."""
        orig_set_fetch_button_state = self.steam_manager.set_fetch_button_state
        def wrapped(is_fetching):
            orig_set_fetch_button_state(is_fetching)
            self.set_game_editing_enabled(not is_fetching)
        self.steam_manager.set_fetch_button_state = wrapped

    def set_game_editing_enabled(self, enabled):
        """Enable or disable add, remove, and edit buttons based on fetch state."""
        # Add button
        if hasattr(self, "add_button"):
            self.add_button.setEnabled(enabled)
        # Remove button
        if hasattr(self, "remove_button"):
            self.remove_button.setEnabled(enabled)
        self._edit_enabled = enabled

    def load_initial_data(self):
        # Load config values to instance variables
        self.theme = self.config_manager.get("theme")
        self.selected_branch = self.config_manager.get("selected_branch")
        self.show_update_message = self.config_manager.get("show_update_message")
        self.using_custom_colors = self.config_manager.get("using_custom_colors")
        self.custom_colors = self.config_manager.get("custom_colors")
        self.border_radius = self.config_manager.get("border_radius")
        self.border_size = self.config_manager.get("border_size")
        self.checkbox_radius = self.config_manager.get("checkbox_radius")
        self.bar_thickness = self.config_manager.get("bar_thickness")
        self.bar_radius = self.config_manager.get("bar_radius")
        self.categories = self.config_manager.get("categories")
        self.merge_edges = self.config_manager.get("merge_edges")
        self.swap_input_search = self.config_manager.get("swap_input_search")

    def setup_ui(self):
        # GUI Layout Elements
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(*UI_MARGIN) # Custom Margin For Main Layout
        main_layout.setSpacing(VERTICAL_SPACING)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Row 1: Top Controls GroupBox
        top_group = QGroupBox()
        top_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        top_controls = QHBoxLayout()
        top_controls.setSpacing(HORIZONTAL_SPACING)
        top_group.setLayout(top_controls)
        
        # Left side controls with no spacing
        left_controls = QHBoxLayout()

        # Theme controls
        self.theme_controls = QHBoxLayout()
        self.theme_controls.setSpacing(HORIZONTAL_SPACING)

        self.color_customization_button = self.create_button("", self.open_color_config_dialog, objectName=None,
                                                           icon=CUSTOMIZATION_ICON, fixed_width=ICON_BUTTON_WIDTH, 
                                                           tooltip="Customize the application theme colors")
        self.theme_switch = QComboBox()
        self.theme_switch.addItems(["Dark", "Light", "Ocean", "Forest", "Fire"])
        self.theme_switch.setCurrentText(self.theme.capitalize())
        self.theme_switch.currentIndexChanged.connect(self.toggle_default_theme)

        self.theme_controls.addWidget(self.color_customization_button)
        self.theme_controls.addWidget(self.theme_switch)

        # Use CustomCheckBox with only text for simple usage
        self.toggle_theme_checkbox = QCheckBox("Use Custom Theme")
        self.toggle_theme_checkbox.setChecked(self.using_custom_colors)
        self.toggle_theme_checkbox.stateChanged.connect(self.toggle_custom_theme)

        left_controls.addLayout(self.theme_controls)
        left_controls.addWidget(self.toggle_theme_checkbox)
        
        # Add left controls to main top controls
        top_controls.addLayout(left_controls)
        top_controls.addStretch()

        # Right side controls
        right_controls = QHBoxLayout()
        
        # Update Available Label
        self.update_status_label = QLabel("", self, objectName="update_status_label", alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.update_status_label.setCursor(Qt.PointingHandCursor)  # Set cursor to hand when hovering
        self.update_status_label.mousePressEvent = self.update_label_clicked  # Make label clickable
        right_controls.addWidget(self.update_status_label)
        
        # Right-side buttons
        self.update_menu_button = self.create_button("", self.open_update_dialog, objectName=None,
                                                   icon=UPDATE_ICON, fixed_width=ICON_BUTTON_WIDTH,
                                                   tooltip="Check for updates or manage update settings")

        # Add the add_button as a hamburger menu with plus icon
        self.add_button = self.create_button("", self.open_add_menu, objectName=None,
                                            icon=PLUS_ICON, fixed_width=ICON_BUTTON_WIDTH,
                                            tooltip="Add/import/backup games")

        # Settings menu button
        self.settings_button = self.create_button("", self.open_settings_menu, objectName=None,
                                                  icon=QIcon.fromTheme("settings") if QIcon.hasThemeIcon("settings") else COG_ICON,
                                                  fixed_width=ICON_BUTTON_WIDTH,
                                                  tooltip="Open settings menu")
        right_controls.addWidget(self.update_menu_button)
        right_controls.addWidget(self.add_button)
        right_controls.addWidget(self.settings_button)
        
        # Add right controls to main top controls
        top_controls.addLayout(right_controls)

        # Row 2: Games List Group
        combined_group = QGroupBox()
        combined_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        combined_layout = QVBoxLayout()
        combined_layout.setSpacing(VERTICAL_SPACING_SMALL)
        
        # Store layout references as instance variables for dynamic rearrangement
        self.combined_layout = combined_layout
        self.combined_group = combined_group
        
        # Search controls
        search_controls = QHBoxLayout()
        self.search_controls = search_controls
        self.search_controls.setSpacing(HORIZONTAL_SPACING)
        
        self.search_bar = ModernQLineEdit()
        self.search_bar.setPlaceholderText("Search title or key")
        self.search_bar.textChanged.connect(self.refresh_game_list)
        search_controls.addWidget(self.search_bar)

        self.found_count_label = QLabel("Games: 0", self, objectName="GameCount")
        search_controls.addWidget(self.found_count_label)

        # Category controls
        self.category_controls = QHBoxLayout()
        self.category_controls.setSpacing(HORIZONTAL_SPACING)
        
        self.manage_categories_button = self.create_button("", self.open_category_manager, objectName=None,
                                                         icon=CATEGORY_MANAGER_ICON, fixed_width=ICON_BUTTON_WIDTH,
                                                         tooltip="Manage game categories")
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories"] + self.categories)
        self.category_filter.currentTextChanged.connect(self.refresh_game_list)
        
        self.category_controls.addWidget(self.manage_categories_button)
        self.category_controls.addWidget(self.category_filter)
        
        search_controls.addLayout(self.category_controls)
        
        # Table widget setup
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["Icon", "Game Title", "Steam Key", "Category", "AppID", "Steam Ratings", "Developer"])
        self.table_widget.setColumnWidth(0, 74)   # Icon Column
        self.table_widget.setColumnWidth(1, 280)  # Title Column
        self.table_widget.setColumnWidth(2, 200)  # Key Column
        self.table_widget.setColumnWidth(3, 110)  # Category Column
        self.table_widget.setColumnWidth(4, 80)  # AppID Column
        self.table_widget.setColumnWidth(5, 200)  # Ratings Column
        self.table_widget.setColumnWidth(6, 150)  # Developer Column
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_right_click_menu)
        
        # Set up sorting functionality
        self.table_widget.horizontalHeader().setSectionsClickable(True)
        self.table_widget.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        
        # Initial layout arrangement
        self.arrange_input_search_layouts()
            
        combined_group.setLayout(combined_layout)

        # Row 3: Bottom Controls GroupBox
        bottom_group = QGroupBox()
        bottom_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        bottom_controls = QHBoxLayout()
        bottom_controls.setSpacing(HORIZONTAL_SPACING)
        bottom_group.setLayout(bottom_controls)
        
        # Left-side buttons
        self.toggle_keys_button = self.create_button("Show All Keys", self.toggle_all_keys_visibility, objectName=None,
                                                   tooltip="Show/Hide all game keys in the table")
        self.copy_button = self.create_button("Copy Keys", self.copy_selected_keys, objectName=None,
                                            tooltip="Copy the selected game keys to the clipboard")
        self.remove_button = self.create_button("Remove Keys", self.remove_selected_games, objectName=None,
                                              tooltip="Remove the selected games from the list")
        bottom_controls.addWidget(self.toggle_keys_button)
        bottom_controls.addWidget(self.copy_button)
        bottom_controls.addWidget(self.remove_button)
        bottom_controls.addStretch()

        # Right-side control - Fetch status label and buttons
        self.fetch_status_label = QLabel("", objectName="FetchStatusLabel")
        self.fetch_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fetch_status_label.setMinimumWidth(200)  # Ensure label has enough space
        
        # Create the fetch_steam_button before using it
        self.fetch_steam_button = self.create_button("Fetch Steam Data", self.open_steam_fetch_menu, objectName=None,
                                                 tooltip="Fetch or update Steam data for games")

        bottom_controls.addWidget(self.fetch_status_label)
        bottom_controls.addWidget(self.fetch_steam_button)
        
        # Add all rows to main layout
        main_layout.addWidget(top_group)
        main_layout.addWidget(combined_group)
        main_layout.addWidget(bottom_group)

        # Refresh initial game list
        self.refresh_game_list()

    def arrange_input_search_layouts(self):
        """Arrange the input and search layouts based on swap_input_search setting"""
        # First, remove existing layouts if they're already in combined_layout
        for i in reversed(range(self.combined_layout.count())):
            item = self.combined_layout.itemAt(i)
            if item is not None:
                widget_or_layout = item.widget() or item.layout()
                if widget_or_layout is not None:
                    if widget_or_layout == self.table_widget:
                        self.combined_layout.removeWidget(self.table_widget)
                    elif item.layout() == self.search_controls:
                        self.combined_layout.removeItem(item)

        # Add layouts in the correct order based on swap_input_search setting
        if self.swap_input_search:
            self.combined_layout.addWidget(self.table_widget)
            self.combined_layout.addLayout(self.search_controls)
        else:
            self.combined_layout.addLayout(self.search_controls)
            self.combined_layout.addWidget(self.table_widget)
        
        # Force GUI update
        self.combined_group.updateGeometry()
        self.update()

    def toggle_merged_edges(self, state):
        # Save the state to instance variable and config
        self.merge_edges = bool(state)
        self.config_manager.set("merge_edges", self.merge_edges)
        # Apply the styling based on current state
        self.apply_merged_edges_style()

    def apply_merged_edges_style(self):
        """Apply the styling for merged/separate edges based on current merge_edges setting"""
        # Define widget pairs for merged edges styling
        widget_pairs = [
            # Theme controls
            (self.color_customization_button, self.theme_switch, 
             self.theme_controls, "FlatRightEdge", "FlatLeftEdge"),
            
            # Category controls
            (self.manage_categories_button, self.category_filter,
             self.category_controls, "FlatRightEdge", "FlatLeftEdge")
        ]
        
        # Apply the styling using the centralized function
        apply_merged_edges(widget_pairs, self.merge_edges)

    def open_update_dialog(self):
        update_manager = self.update_manager_ref()
        if update_manager is not None:
            dialog = UpdateDialog(self, self.cache)
            dialog.update_signal.connect(lambda text, visible: self.status_message_label.emit(text, visible))
            dialog.exec()
            self.auto_update_check = dialog.auto_update_check
            self.save_config()

    # Add a new method to handle update label clicks
    def update_label_clicked(self, event):
        # Only respond if the label contains "Update Available"
        if "Update Available" in self.update_status_label.text():
            self.open_update_dialog()

    def handle_status_message_label(self, text, visible):
        self.update_status_label.setText(text)
        self.update_status_label.setVisible(visible)
        # Cancel any existing timer
        if self.message_timer and self.message_timer.isActive():
            self.message_timer.stop()

        # Only set a timeout if the message should be temporary
        if visible and not text.startswith("Update Available"):
            self.message_timer = QTimer()
            self.message_timer.setSingleShot(True)
            
            if text.startswith("Successfully updated"):
                # Longer timeout for successful update messages (6 seconds)
                self.message_timer.timeout.connect(lambda: self.status_message_label.emit("", False))
                self.message_timer.start(6000)
            else:
                # Default timeout for other messages (3 seconds)
                self.message_timer.timeout.connect(lambda: self.status_message_label.emit("", False))
                self.message_timer.start(3000)

    def create_button(self, text, slot, icon=None, objectName=None, fixed_height=None, fixed_width=None, tooltip=None):
        button = QPushButton(text)
        if icon:
            theme = Theme(self.theme, self.custom_colors if self.using_custom_colors else None)
            if theme:
                icon_data = icon.replace("{{COLOR}}", theme.get_icon_color())
                button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon_data.encode()))))
        if fixed_width:
            button.setFixedWidth(fixed_width)
        if fixed_height:
            button.setFixedHeight(fixed_height)
        if objectName:
            button.setObjectName(objectName)
        if tooltip:
            button.setToolTip(tooltip)
        button.clicked.connect(slot)
        return button

    def toggle_default_theme(self):
        current_theme = self.theme
        selected_theme = self.theme_switch.currentText().lower()
        if selected_theme in ["dark", "light", "ocean", "forest", "fire"]:
            if selected_theme != current_theme:
                self.theme = selected_theme
                self.config_manager.set("theme", selected_theme)
                self.apply_theme()
        else:
            logging.warning("Invalid theme selected")

    def toggle_custom_theme(self):
        self.using_custom_colors = self.toggle_theme_checkbox.isChecked()
        self.config_manager.set("using_custom_colors", self.using_custom_colors)
        self.apply_theme()

    def apply_theme(self):
        if self.using_custom_colors:
            theme = Theme(self.theme, self.custom_colors, self.border_radius, self.border_size, self.checkbox_radius, self.bar_radius, self.bar_thickness)
        else:
            theme = Theme(self.theme)
        new_stylesheet = theme.generate_stylesheet()
        if new_stylesheet != self.current_stylesheet:
            self.current_stylesheet = new_stylesheet            
            self.setStyleSheet(new_stylesheet)
            self.update_icons(theme)
            # Update custom checkbox theme
            if hasattr(self, "toggle_theme_checkbox") and isinstance(self.toggle_theme_checkbox, CustomCheckBox):
                self.toggle_theme_checkbox.setBorderRadius(theme.border_radius)
                self.toggle_theme_checkbox.setBorderColor(theme.colors.get("checkbox_background_unchecked", "#4f4f4f"))
                self.toggle_theme_checkbox.setBorderColorChecked(theme.colors.get("checkbox_background_checked", "#45e09a"))

    def apply_custom_colors(self, custom_colors, border_radius, border_size, checkbox_radius, bar_radius, bar_thickness):
        # Create cache key from all parameters
        cache_key = (
            self.theme,
            tuple(sorted(custom_colors.items())),
            border_radius,
            border_size,
            checkbox_radius,
            bar_radius,
            bar_thickness
        )

        # Check if we already have this theme configuration cached
        if cache_key not in self._theme_cache:
            self._theme_cache.clear()  # Clear old cache to prevent memory growth
            theme = Theme(
                self.theme,
                custom_colors,
                border_radius,
                border_size,
                checkbox_radius,
                bar_radius,
                bar_thickness
            )
            self._theme_cache[cache_key] = theme
        theme = self._theme_cache[cache_key]
        stylesheet = theme.generate_stylesheet()
        
        if stylesheet != self.current_stylesheet:
            self.current_stylesheet = stylesheet
            self.setStyleSheet(stylesheet)
            self.update_icons(theme)
            # Update custom checkbox theme
            if hasattr(self, "toggle_theme_checkbox") and isinstance(self.toggle_theme_checkbox, CustomCheckBox):
                self.toggle_theme_checkbox.setBorderRadius(theme.border_radius)
                self.toggle_theme_checkbox.setBorderColor(theme.colors.get("checkbox_background_unchecked", "#4f4f4f"))
                self.toggle_theme_checkbox.setBorderColorChecked(theme.colors.get("checkbox_background_checked", "#45e09a"))

    def update_icons(self, theme):
        icons = [
            (self.update_menu_button, UPDATE_ICON),
            (self.color_customization_button, CUSTOMIZATION_ICON),
            (self.settings_button, COG_ICON),
            (self.manage_categories_button, CATEGORY_MANAGER_ICON),
            (self.add_button, PLUS_ICON)
        ]
        color = theme.get_icon_color()
        for button, icon in icons:
            button.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(icon.replace("{{COLOR}}", color).encode()))))

    def censor_key(self, key):
        return '-'.join(['*' * len(part) for part in key.split('-')])

    def update_key_column(self, rows=None):
        if not hasattr(self, "table_widget") or not hasattr(self, "row_to_unique_id"):
            return

        if rows is None:
            rows = range(self.table_widget.rowCount())

        for row in rows:
            unique_id = self.row_to_unique_id.get(row)
            if unique_id is None or unique_id not in self.games:
                continue
            data = self.games[unique_id]
            key_text = data["key"] if self.show_keys or unique_id in self.visible_keys else self.censor_key(data["key"])
            item = self.table_widget.item(row, 2)
            if item is None:
                item = QTableWidgetItem(key_text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 2, item)
            else:
                item.setText(key_text)

    def toggle_all_keys_visibility(self):
        # Always perform the action indicated by the button text
        if self.toggle_keys_button.text() == "Hide All Keys":
            self.show_keys = False
            self.visible_keys.clear()
        else:
            self.show_keys = True
            self.visible_keys.clear()
        self.update_toggle_keys_button_text()
        self.update_key_column()

    def toggle_selected_keys(self):
        affected_rows = set(item.row() for item in self.table_widget.selectedItems())
        # If show_keys is True (all keys visible), switch to per-row visibility mode
        if self.show_keys:
            self.show_keys = False
            # Set visible_keys to all currently visible keys except those being toggled off
            self.visible_keys = set(self.row_to_unique_id[row] for row in range(self.table_widget.rowCount()))
            # Now toggle the selected ones off
            for row in affected_rows:
                unique_id = self.row_to_unique_id[row]
                if unique_id in self.visible_keys:
                    self.visible_keys.remove(unique_id)
                else:
                    self.visible_keys.add(unique_id)
            self.update_key_column()
        else:
            for row in affected_rows:
                unique_id = self.row_to_unique_id[row]
                if unique_id in self.visible_keys:
                    self.visible_keys.remove(unique_id)
                else:
                    self.visible_keys.add(unique_id)
            self.update_key_column(affected_rows)

    def update_toggle_keys_button_text(self):
        self.toggle_keys_button.setText("Hide All Keys" if self.show_keys else "Show All Keys")

    def open_color_config_dialog(self):
        self.toggle_theme_checkbox.setChecked(True)
        
        # Clean up previous dialog if it exists
        if self.color_config_dialog:
            self.color_config_dialog.deleteLater()
        
        self.color_config_dialog = ColorConfigDialog(
            self, self.custom_colors, self.theme, self.border_radius, self.border_size, 
            self.checkbox_radius, self.bar_radius, self.bar_thickness, self.merge_edges, self.swap_input_search
        )
        
        # Connect to the signals
        self.color_config_dialog.theme_changed.connect(self.sync_theme_from_dialog)
        self.color_config_dialog.merge_edges_changed.connect(self.sync_merge_edges_from_dialog)
        self.color_config_dialog.swap_input_search_changed.connect(self.sync_swap_input_search_from_dialog)
        self.color_config_dialog.status_message_label.connect(lambda text, visible: self.status_message_label.emit(text, visible))
        
        # Execute the dialog
        self.color_config_dialog.exec()
        
        # Always apply changes when dialog is closed (regardless of how it was closed)
        self.custom_colors = self.color_config_dialog.current_colors
        self.border_radius = self.color_config_dialog.border_radius
        self.border_size = self.color_config_dialog.border_size
        self.checkbox_radius = self.color_config_dialog.checkbox_radius
        self.bar_thickness = self.color_config_dialog.bar_thickness
        self.bar_radius = self.color_config_dialog.bar_radius
        self.merge_edges = self.color_config_dialog.merge_edges  # Get the merge_edges setting from the dialog
        self.swap_input_search = self.color_config_dialog.swap_input_search  # Get the swap_input_search setting from the dialog
        
        # Update config all at once
        self.config_manager.update({
            "custom_colors": self.custom_colors,
            "border_radius": self.border_radius,
            "border_size": self.border_size,
            "checkbox_radius": self.checkbox_radius,
            "bar_thickness": self.bar_thickness,
            "bar_radius": self.bar_radius,
            "merge_edges": self.merge_edges,
            "swap_input_search": self.swap_input_search
        })
        
        self.apply_theme()
        self.apply_merged_edges_style()  # Apply merge edges style
        
        # Clean up
        self.color_config_dialog.deleteLater()
        self.color_config_dialog = None

    def sync_theme_from_dialog(self, theme):
        """Sync main window theme selector with the dialog's theme selector"""
        # Update the theme instance variable
        self.theme = theme
        # Update the main window's theme selector
        self.theme_switch.setCurrentText(theme.capitalize())
        
        # Update the config
        self.config_manager.set("theme", theme)
                
        # Apply theme changes
        self.apply_theme()

    def sync_merge_edges_from_dialog(self, merge_edges):
        """Sync main window merge edges checkbox with the dialog's merge edges checkbox"""
        self.merge_edges = merge_edges
        self.config_manager.set("merge_edges", merge_edges)
        self.apply_merged_edges_style()

    def sync_swap_input_search_from_dialog(self, swap_input_search):
        """Sync swap input/search setting with the dialog's setting"""
        if self.swap_input_search != swap_input_search:
            self.swap_input_search = swap_input_search
            self.config_manager.set("swap_input_search", swap_input_search)
            
            # Apply the layout change immediately
            self.arrange_input_search_layouts()

    def create_menu_action(self, menu, text, slot):
        action = QAction(text, self)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def open_add_menu(self):
        menu = QMenu(self)
        self.create_menu_action(menu, "Add New Games", self.add_games)
        self.create_menu_action(menu, "Import Games", self.import_games)
        self.create_menu_action(menu, "Backup Games", self.manual_game_data_backup)
        pos = self.add_button.mapToGlobal(QPoint(0, self.add_button.height()))
        pos.setX(pos.x() - menu.sizeHint().width() + self.add_button.width() + 1)
        pos.setY(pos.y() + 4)
        menu.exec(pos)

    def open_steam_fetch_menu(self):
        # Check if already fetching
        if hasattr(self, 'steam_manager') and self.steam_manager.is_fetching:
            self.steam_manager.cancel_steam_fetch()
            return

        menu = QMenu(self)
        self.create_menu_action(menu, "Fetch Missing Data", lambda: self.steam_manager.start_steam_fetch(False))
        self.create_menu_action(menu, "Update Reviews", lambda: self.steam_manager.update_steam_reviews())
        pos = self.fetch_steam_button.mapToGlobal(QPoint(0, self.fetch_steam_button.height()))
        pos.setX(pos.x() - menu.sizeHint().width() + self.fetch_steam_button.width() + 1)
        pos.setY(pos.y() + 4)  # Move the menu down by 4 pixels
        menu.exec(pos)

    def show_right_click_menu(self, position):
        # Get the row index from the position
        row = self.table_widget.rowAt(position.y())
        if (row < 0):
            return
            
        unique_id = self.row_to_unique_id[row]
        self.current_game = self.games[unique_id]
        
        menu = QMenu(self)
        
        # Create common menu items
        actions = [
            ("Toggle Key", self.toggle_selected_keys),
            ("Edit", self.edit_selected_game),
            ("Copy", self.copy_selected_keys),
            ("Remove", self.remove_selected_games),
            ("Open in Browser", self.open_selected_in_browser)
        ]
        
        for text, slot in actions:
            action = self.create_menu_action(menu, text, slot)
            # Disable Edit and Remove if editing is disabled
            if text in ("Edit", "Remove") and hasattr(self, "_edit_enabled") and not self._edit_enabled:
                action.setEnabled(False)
            
        # Insert category submenu after the first item
        set_game_category_menu = QMenu("Set Category", self)
        for category in self.categories:
            action = QAction(category, self)
            action.triggered.connect(lambda checked, cat=category: self.set_game_category(cat))
            set_game_category_menu.addAction(action)
        
        # Insert submenu after first item
        menu.insertMenu(menu.actions()[1], set_game_category_menu)
        
        menu.exec(self.table_widget.viewport().mapToGlobal(position))

    def open_category_manager(self):
        dialog = CategoryManagerDialog(self.categories, self)
        # Connect the signal to the main window's status_message_label
        dialog.status_message_label.connect(lambda text, visible: self.status_message_label.emit(text, visible))
        if dialog.exec():
            # Save categories and update config
            self.categories = dialog.categories
            self.config_manager.set("categories", self.categories)
            
            # Update game categories based on the mapping
            for game in self.games.values():
                if (game["category"] in dialog.category_map):
                    game["category"] = dialog.category_map[game["category"]]
                elif (game["category"] not in self.categories):
                    game["category"] = "New"
                    
            # Update UI and save changes
            self.save_key_data()
            self.category_filter.clear()
            self.category_filter.addItems(["All Categories"] + self.categories)
            self.refresh_game_list()

    def parse_input_line(self, line):
        return parse_input_line_global(line) # Call the global parsing function

    def add_games(self):
        if hasattr(self, "_edit_enabled") and not self._edit_enabled:
            return  # Prevent adding while fetching
        add_games(self, self.games, self.save_key_data, self.refresh_game_list, self.steam_manager, self.parse_input_line)

    def remove_selected_games(self):
        if hasattr(self, "_edit_enabled") and not self._edit_enabled:
            return  # Prevent removing while fetching
        remove_selected_games(self, self.table_widget, self.games, self.row_to_unique_id, self.save_key_data, self.refresh_game_list)

    def copy_selected_keys(self):
        copy_selected_keys(self, self.table_widget, self.games, self.row_to_unique_id)
    
    def edit_selected_game(self):
        if hasattr(self, "_edit_enabled") and not self._edit_enabled:
            return  # Prevent editing while fetching
        edit_selected_games(self, self.table_widget, self.games, self.row_to_unique_id, self.save_key_data, self.refresh_game_list, 
                            self.current_sort_column, self.current_sort_order, self.steam_manager, self.using_custom_colors, self.border_radius)

    def set_game_category(self, category):
        for item in self.table_widget.selectedItems():
            row = item.row()
            unique_id = self.row_to_unique_id[row]
            if unique_id in self.games:
                self.games[unique_id]["category"] = category
        self.save_key_data()
        self.refresh_game_list()

    def handle_header_click(self, column):
        """Handle clicking on table headers to sort the table"""
        # If clicking the same column, toggle sort order, otherwise set new column with ascending order
        self.current_sort_order = Qt.DescendingOrder if (column == self.current_sort_column and 
                                   self.current_sort_order == Qt.AscendingOrder) else Qt.AscendingOrder
        self.current_sort_column = column
        self.refresh_game_list()

    def refresh_game_list(self):
        search_term = self.search_bar.text().lower()
        category_filter = self.category_filter.currentText()

        # Filter games
        filtered_games = [
            (uid, data) for uid, data in self.games.items()
            if (search_term in data["title"].lower() or search_term in data["key"].lower()) and
            (category_filter == "All Categories" or data["category"] == category_filter)
        ]
        
        # Use centralized sort key function from Game_Management.py
        from Game_Management import get_sort_key_function
        sort_key = get_sort_key_function(self.current_sort_column, self.categories)
        
        # Apply sorting with the appropriate key function
        filtered_games.sort(key=sort_key)
        
        # Apply sort order
        if self.current_sort_order == Qt.DescendingOrder:
            filtered_games.reverse()

        # Update the found games count
        self.found_count_label.setText(f"Games: {len(filtered_games)}")
        self.table_widget.setRowCount(len(filtered_games))

        # Map table rows to unique IDs
        self.row_to_unique_id = {i: unique_id for i, (unique_id, _) in enumerate(filtered_games)}

        for i, (unique_id, data) in enumerate(filtered_games):
            # Handle icon display
            has_valid_icon = "icon_path" in data and os.path.exists(data["icon_path"])
            
            if has_valid_icon:
                pixmap = QPixmap(data["icon_path"]).scaled(TABLE_ICON_WIDTH, TABLE_ICON_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                
                icon_column_label = RoundedImage(self, border_radius=TABLE_CELL_RADIUS, fixed_size=(TABLE_ICON_WIDTH, TABLE_ICON_HEIGHT))
                icon_column_label.setPixmap(pixmap)
                
                # Use a container to center the icon label
                container = CenteredIconContainer(self)
                container.setWidget(icon_column_label)
                self.table_widget.setCellWidget(i, 0, container)
            else:
                self.table_widget.removeCellWidget(i, 0)
                self.table_widget.setItem(i, 0, QTableWidgetItem(""))
            
            # Helper function to create table items with common properties
            def create_item(text, center_align=True):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if center_align:
                    item.setTextAlignment(Qt.AlignCenter)
                return item
            
            # Create items with appropriate data
            items = [
                create_item(data["title"], center_align=False),
                create_item(data["key"] if self.show_keys or unique_id in self.visible_keys else self.censor_key(data["key"])),
                create_item(data["category"]),
                create_item(data.get("app_id", "")),
                create_item(format_rating_text(data.get("review_data", None))),
                create_item(data.get("developer", ""))
            ]
            
            # Set rating color if available
            review_data = data.get("review_data", None)
            if review_data and 'rating_text' in review_data:
                items[4].setForeground(QColor(get_rating_color(review_data['rating_text'], review_data.get('percentage'))))
            
            # Add all items to table
            for col, item in enumerate(items, 1):
                self.table_widget.setItem(i, col, item)

    def import_games(self):
        import_games(self)

    def manual_game_data_backup(self):
        manual_game_data_backup(self)

    def load_key_data(self):
        data = self.encryption_manager.load_data()
        if (data):
            self.games = json.loads(data)

    def save_key_data(self):
        data_to_save = json.dumps(self.games, indent=4)
        self.encryption_manager.save_data(data_to_save)

    def save_config(self):
        """
        Save current configuration settings using the config manager.
        Updates all necessary fields at once.
        """
        # Make sure we have all values initialized
        if not hasattr(self, 'theme') or not hasattr(self, 'categories'):
            return  # Safety check - don't save incomplete config

        config_data = {
            "selected_branch": self.selected_branch,
            "show_update_message": self.show_update_message,
            "auto_update_check": self.auto_update_check,
            "categories": self.categories,
            "merge_edges": self.merge_edges,
            "swap_input_search": self.swap_input_search,
            "theme": self.theme,
            "using_custom_colors": self.using_custom_colors,
            "custom_colors": self.custom_colors,
            "border_radius": self.border_radius,
            "border_size": self.border_size,
            "checkbox_radius": self.checkbox_radius,
            "bar_thickness": self.bar_thickness,
            "bar_radius": self.bar_radius,
        }
        
        # Update all config values at once
        self.config_manager.update(config_data)

    def show_update_message_if_needed(self):
        if self.show_update_message:
            self.status_message_label.emit(f"Successfully updated to version: {CURRENT_BUILD}", True)
            self.show_update_message = False
            self.config_manager.set("show_update_message", False)
            
            # If auto update check is enabled, start it after the success message timeout
            if self.auto_update_check:
                QTimer.singleShot(6000, self.update_manager.start)
        elif self.auto_update_check:
            # If no success message to show, start the update check immediately
            self.update_manager.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)

    def open_selected_in_browser(self):
        handle_browser_open(self.games, self.table_widget.selectedItems(), self.row_to_unique_id, self)

    def open_settings_menu(self):
        dialog = SettingsMenuDialog(self, encryption_manager=self.encryption_manager, config_path=str(CONFIG_FILE_PATH))
        dialog.settings_imported.connect(self.reload_config_and_apply)
        dialog.exec()

    def reload_config_and_apply(self):
        """Reload config from disk and apply all relevant settings/UI."""
        self.config_manager.load()
        # Reload all config-dependent attributes
        self.theme = self.config_manager.get("theme")
        self.selected_branch = self.config_manager.get("selected_branch")
        self.show_update_message = self.config_manager.get("show_update_message")
        self.using_custom_colors = self.config_manager.get("using_custom_colors")
        self.custom_colors = self.config_manager.get("custom_colors")
        self.border_radius = self.config_manager.get("border_radius")
        self.border_size = self.config_manager.get("border_size")
        self.checkbox_radius = self.config_manager.get("checkbox_radius")
        self.bar_thickness = self.config_manager.get("bar_thickness")
        self.bar_radius = self.config_manager.get("bar_radius")
        self.categories = self.config_manager.get("categories")
        self.merge_edges = self.config_manager.get("merge_edges")
        self.swap_input_search = self.config_manager.get("swap_input_search")
        # Update UI elements to reflect new config
        self.theme_switch.setCurrentText(self.theme.capitalize())
        self.toggle_theme_checkbox.setChecked(self.using_custom_colors)
        self.category_filter.clear()
        self.category_filter.addItems(["All Categories"] + self.categories)
        self.arrange_input_search_layouts()
        self.apply_theme()
        self.apply_merged_edges_style()
        self.refresh_game_list()

def check_and_migrate_files():
    """Check if files need to be migrated from old structure and prompt user"""
    needs_migration, old_files, new_files = check_old_file_structure()
    
    if needs_migration:
        msg = QMessageBox()
        msg.setWindowTitle("File Migration")
        msg.setText("Old configuration files detected in application directory")
        msg.setInformativeText("Would you like to migrate your settings and game keys to the new location?\n\n"
                              f"From: {os.path.dirname(old_files[0])}\n"
                              f"To: {os.path.dirname(new_files[0])}")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setIcon(QMessageBox.Question)
        
        if msg.exec() == QMessageBox.Yes:
            success = migrate_files(old_files, new_files)
            
            if success:
                QMessageBox.information(
                    None, 
                    "Migration Complete",
                    "Files have been successfully migrated to the new location."
                )
            else:
                QMessageBox.warning(
                    None, 
                    "Migration Failed",
                    "There was a problem migrating the files. Please check the application logs."
                )

def main():
    app = QApplication(sys.argv)
    #app.setStyle('Fusion') # Linux Style
    # Check for files to migrate before initializing the main window
    check_and_migrate_files()
    window = SteamKeyManager()
    window.show()
    window.show_update_message_if_needed()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()