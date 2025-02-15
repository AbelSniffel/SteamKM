# SteamKM_Themes.py
from PySide6.QtWidgets import *
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Constants
BUTTON_HEIGHT = 32
CHECKBOX_SIZE = 18  # Width and Height
DEFAULT_BR = 9  # Border Radius
DEFAULT_BS = 0  # Border Size
DEFAULT_BSI = 0  # Border Size Interactables
DEFAULT_CR = 6  # Checkbox Radius
DEFAULT_SR = 5  # Scrollbar Radius
DEFAULT_SW = 14  # Scrollbar Width
DBH = 1.19  # Dynamic brightness hover value
DBP = 0.92  # Dynamic brightness press value
PADDING = "padding: 6px"
DEEP_TITLE_PADDING = "padding: 8px"
BUTTON_PADDING = "padding: 0px 12px;"
COLOR_PICKER_BUTTON_STYLE = "border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;"
COLOR_RESET_BUTTON_STYLE = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: 0px;"

class ModernQLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setClearButtonEnabled(True)

class Theme:
    def __init__(self, theme="dark", custom_colors=None, border_radius=DEFAULT_BR, border_size=DEFAULT_BS,
                 border_size_interactables=DEFAULT_BSI, checkbox_radius=DEFAULT_CR, scroll_radius=DEFAULT_SR,
                 scrollbar_width=DEFAULT_SW):
        self.theme = theme
        self.border_radius = border_radius
        self.border_size = border_size
        self.border_size_interactables = border_size_interactables
        self.checkbox_radius = checkbox_radius
        self.scroll_radius = scroll_radius
        self.scrollbar_width = scrollbar_width
        self.colors = self.get_theme_colors(theme)
        if custom_colors:
            self.colors.update(custom_colors)
        self.brightness_adjuster = BrightnessAdjuster()

    def get_theme_colors(self, theme):
        theme_to_index = {"dark": 0, "light": 1, "ocean": 2, "forest": 3}
        colors = {
            "main_background": ("#2e2e2e", "#ffffff", "#00557f", "#065242"),
            "text_color": ("white", "black", "white", "white"),
            "add_games_background": ("#404040", "#dce8fa", "#1b475e", "#256b51"),
            "search_bar_background": ("#404040", "#dce8fa", "#2c3a55", "#137053"),
            "label_background": ("#3d3d3d", "#d2e4ff", "#002e43", "#136c54"),
            "groupbox_background": ("#292929", "#fafafa", "#24496c", "#083f33"),
            "button_background": ("#525252", "#c3d5ff", "#40a5aa", "#3e8354"),
            "reset_button_background": ("#ff6666", "#ff9999", "#55557f", "#235127"),
            "combobox_background": ("#525252", "#d2d5ff", "#aa557f", "#4f9e00"),
            "checkbox_background_checked": ("#45e09a", "#91baff", "#55ffff", "#6beb3c"),
            "checkbox_background_unchecked": ("#4f4f4f", "#dadfe6", "#1b3752", "#00402e"),
            "scrollbar_handle": ("#45e09a", "#93acff", "#3bbaff", "#0bc57e"),
            "scrollbar_background": ("#385b4a", "#d0dfff", "#25789b", "#2c7050"),
            "table_background": ("#292929", "#f7faff", "#1e3d5a", "#023f36"),
            "table_item_selected": ("#38b677", "#a6c7ff", "#3c7ab3", "#3e954c"),
            "table_gridline_color": ("#3d3d3d", "#c9ddfa", "#2e4b66", "#144d44"),
            "changelog_background": ("#222222", "#d9e6fa", "#1b3953", "#04332a"),
            "generic_border_color": ("#4d4d4d", "#ccdbf2", "#45a1c9", "#0d8e58"),
            "interactables_border_color": ("#404040", "#c3c7ff", "#55aaff", "#56af5e"),
            "table_border_color": ("#383838", "#d9e3f2", "#2b5a83", "#025a4a"), #aaaaff (ocean), #024c41 (forest)
        }
        theme_index = theme_to_index.get(theme, 0)
        return {key: value[theme_index] for key, value in colors.items()}
    
    def get_icon_color(self):
        return self.colors["text_color"]

    def generate_stylesheet(self):
        colors = self.colors
        for key in ["button_background", "reset_button_background"]:
            colors[f"{key}_hover"] = self.brightness_adjuster.adjust_brightness_dynamically(colors[key], DBH)
            colors[f"{key}_pressed"] = self.brightness_adjuster.adjust_brightness(colors[key], DBP)

        styles = {
            "QWidget": f"background-color: transparent; color: {colors['text_color']}; border-radius: {self.border_radius}px;",
            "QMainWindow, QDialog, QDockWidget": f"background-color: {colors['main_background']};",
            "QDockWidget::title": f"{PADDING};",
            "QGroupBox": f"background-color: {colors['groupbox_background']}; border: {max(self.border_size, 2)}px solid {colors['generic_border_color']}; margin-right: 5px;",
            "QLabel": f"background-color: transparent;",
            "QTextEdit": f"background-color: {colors['add_games_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; padding-left: 5px; padding-top: 4px; height: {BUTTON_HEIGHT};",
            "#ChangeLog": f"background-color: {colors['changelog_background']}; border-radius: {self.border_radius / 2}px;",
            "QLineEdit": f"background-color: {colors['search_bar_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; padding-left: 7px; height: {BUTTON_HEIGHT}; {BUTTON_PADDING};",
            "QComboBox": f"background-color: {colors['combobox_background']}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; {BUTTON_PADDING}; height: {BUTTON_HEIGHT};",
            "QComboBox:hover": f"background-color: {self.brightness_adjuster.adjust_brightness_dynamically(colors['combobox_background'], DBH)};",
            "QComboBox:drop-down": "height: 0; width: 0;",
            "QComboBox QAbstractItemView": f"background-color: {colors['combobox_background']}; border: 0; border-radius: {self.border_radius / 2}px; margin-top: 5px; padding: 2px;",
            "QPushButton": f"background-color: {colors['button_background']}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; {BUTTON_PADDING}; height: {BUTTON_HEIGHT};",
            "QPushButton:hover, QMenu::item:selected": f"background-color: {colors['button_background_hover']};",
            "QPushButton:pressed, QMenu::item:pressed": f"background-color: {colors['button_background_pressed']};",
            "#ResetButton": f"background-color: {colors['reset_button_background']};",
            "#ResetButtonEncased": f"background-color: {colors['reset_button_background']}; border-radius:{self.border_radius / 2}px;",
            "#ResetButtonHalf": f"background-color: {colors['reset_button_background']}; {COLOR_RESET_BUTTON_STYLE};",
            "#ResetButtonEncasedHalf": f"background-color: {colors['reset_button_background']}; border-radius:{self.border_radius / 2}px; {COLOR_RESET_BUTTON_STYLE};",
            "#ResetButton:hover, #ResetButtonHalf:hover, #ResetButtonEncased:hover, #ResetButtonEncasedHalf:hover": f"background-color: {colors['reset_button_background_hover']};",
            "#ResetButton:pressed, #ResetButtonHalf:pressed, #ResetButtonEncased:pressed, #ResetButtonEncasedHalf:pressed": f"background-color: {colors['reset_button_background_pressed']};",
            "QCheckBox::indicator:unchecked": f"background-color: {colors['checkbox_background_unchecked']}; height: {CHECKBOX_SIZE}px; width: {CHECKBOX_SIZE}px; border: 0px; border-radius: {self.checkbox_radius}px;",
            "QCheckBox::indicator:checked": f"background-color: {colors['checkbox_background_checked']}; height: {CHECKBOX_SIZE}px; width: {CHECKBOX_SIZE}px; border: 0px; border-radius: {self.checkbox_radius}px;",
            "QHeaderView": f"background-color: {colors['table_background']}; border: none;",
            "QHeaderView::section": f"background-color: {colors['table_gridline_color']}; border-radius: 4px; margin: 2px; padding-left: 4px;",
            "QTableCornerButton::section": f"background-color: {colors['button_background']}; border-radius: 4px; border-top-left-radius: {(self.border_radius / 2)}px; margin: 2px; padding-left: 4px;",
            "QTableWidget": f"background-color: {colors['table_background']}; border: {max(self.border_size, 2)}px solid {colors['table_border_color']}; {PADDING}; gridline-color: {colors['table_gridline_color']};",
            "QTableWidget::item": "background-color: transparent; border-radius: 4px; margin: 2px",
            "QTableWidget::item:selected": f"background-color: {colors['table_item_selected']};",
            "QScrollBar": f"background-color: {colors['scrollbar_background']}; border-radius: {self.scroll_radius}px; border: 0;",
            "QScrollBar:vertical": f"width: {self.scrollbar_width}px;",
            "QScrollBar:horizontal": f"height: {self.scrollbar_width}px;",
            "QScrollBar::handle": f"background-color: {colors['scrollbar_handle']}; border-radius: {self.scroll_radius}px; border: 0;",
            "QScrollBar::add-page, QScrollBar::sub-page": "background-color: none;",
            "QScrollBar::add-line, QScrollBar::sub-line": "width: 0px; height: 0px;",
            "QProgressBar": f"background-color: {colors['scrollbar_background']}; border-radius: {self.border_radius / 2}px; border: 0; text-align: center; height: 6px;",
            "QProgressBar::chunk": f"background-color: {colors['scrollbar_handle']}; border-radius: {self.border_radius / 2}px; border: 0;",
            "QMenu": f"background-color: {colors['main_background']}; {PADDING}; border: {max(self.border_size, 2)}px solid {colors['interactables_border_color']};",
            "QMenu::item": f"{PADDING} 15px; border-radius: {self.border_radius / 2}px;",
            "#EncasedRadiusHalved": f"border-radius: {self.border_radius / 2}px;",
            "#CategoryLineEdit": f"background-color: {colors['search_bar_background']}; {COLOR_PICKER_BUTTON_STYLE}; padding-left: 7px; height: {BUTTON_HEIGHT}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; border-right: 0px;",
            "#FoundCountLabel": f"background-color: {colors['label_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; {PADDING};",
            "#DeepLabel": f"background-color: {colors['label_background']}; padding: 6px; {DEEP_TITLE_PADDING}; margin-bottom: 4px; border: {self.border_size}px solid {colors['generic_border_color']}; border-radius: {self.border_radius / 2}px;",
            ".icon": f"fill: {colors['text_color']}; stroke: {colors['text_color']};",
        }

        return "\n".join(f"{selector} {{ {style} }}" for selector, style in styles.items())

class BrightnessAdjuster:
    def __init__(self):
        self._brightness_cache = {}

    def adjust_brightness(self, hex_color, factor, dynamic=False):
        if (hex_color, factor, dynamic) not in self._brightness_cache:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            if dynamic:
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                factor = factor + (0.5 - luminance) * 0.35  # Dynamic adjustment
            r, g, b = [min(max(0, int(c * factor)), 255) for c in (r, g, b)]
            self._brightness_cache[(hex_color, factor, dynamic)] = f"#{r:02x}{g:02x}{b:02x}"
        return self._brightness_cache[(hex_color, factor, dynamic)]

    def adjust_brightness_dynamically(self, hex_color, factor):
        return self.adjust_brightness(hex_color, factor, dynamic=True)

class ColorConfigDialog(QDialog):
    def __init__(self, parent=None, current_colors=None, theme="dark", border_radius=DEFAULT_BR, border_size=DEFAULT_BS,
                 border_size_interactables=DEFAULT_BSI, checkbox_radius=DEFAULT_CR, scroll_radius=DEFAULT_SR,
                 scrollbar_width=DEFAULT_SW):
        super().__init__(parent)
        self.setWindowTitle("Theme Customization Menu")
        self.resize(500, 700)
        self.theme = theme
        self.current_colors = current_colors if current_colors else {}
        self.border_radius = border_radius
        self.border_size = border_size
        self.border_size_interactables = border_size_interactables
        self.checkbox_radius = checkbox_radius
        self.scroll_radius = scroll_radius
        self.scrollbar_width = scrollbar_width
        self.color_pickers = {}
        self.brightness_adjuster = BrightnessAdjuster()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Search bar
        self.search_bar = ModernQLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_items)
        main_layout.addWidget(self.search_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        scroll_area_layout = QVBoxLayout(scroll_area_widget)

        self.config_group = QGroupBox()
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setAlignment(Qt.AlignTop)
        
        # Groups
        self.groups = [
            ("Main Colors", [
                ("Text Color", "text_color"),
                ("Main Background", "main_background"),
                ("Title/Label & Found Games Background", "label_background"),
                ("Grouped Items Background", "groupbox_background"),
                ("Changelog Background", "changelog_background"),
                ("Main Border", "generic_border_color"),
            ]),
            ("Add & Search bars", [
                ("Add Games Background", "add_games_background"),
                ("Search Bar Background", "search_bar_background"),
            ]),
            ("Interactables Elements", [
                ("Button Color", "button_background"),
                ("Reset Color", "reset_button_background"),
                ("Category/Combobox Background", "combobox_background"),
                ("Checkbox Checked", "checkbox_background_checked"),
                ("Checkbox Unchecked", "checkbox_background_unchecked"),
                ("Interactables Border", "interactables_border_color"),
            ]),
            ("Game Table", [
                ("Game Table Background", "table_background"),
                ("Game Table Selected Game Color", "table_item_selected"),
                ("Game Table Gridline & Header Color", "table_gridline_color"),
                ("Game Table Border", "table_border_color"),
            ]),
            ("Scroll & Progress bar", [
                ("Scroll & Progress bar Handle", "scrollbar_handle"),
                ("Scroll & Progress bar Background", "scrollbar_background"),
            ]),
        ]

        self.form_layouts = {}
        for title, elements in self.groups:
            group_label = QLabel(title, objectName="DeepLabel", alignment=Qt.AlignCenter, fixedHeight=BUTTON_HEIGHT+7)
            config_layout.addWidget(group_label)
            form_layout = QFormLayout()
            form_layout.setVerticalSpacing(6)

            for label, key in elements:
                self.add_color_picker(form_layout, label, key)

            config_layout.addLayout(form_layout)
            self.form_layouts[title] = form_layout
        
        # Sliders
        sliders_label = QLabel("Border Size & Radius", objectName="DeepLabel", alignment=Qt.AlignCenter, fixedHeight=BUTTON_HEIGHT+7)
        config_layout.addWidget(sliders_label)

        sliders = [
            ("Corner Radius", "border_radius", 0, BUTTON_HEIGHT // 2, self.update_border_radius, DEFAULT_BR),
            ("Checkbox Radius", "checkbox_radius", 0, CHECKBOX_SIZE // 2, self.update_checkbox_radius, DEFAULT_CR),
            ("Border Size", "border_size", 0, 3, self.update_border_size, DEFAULT_BS),
            ("Border Size Interactables", "border_size_interactables", 0, 3, self.update_border_size_interactables, DEFAULT_BSI),
            ("Scrollbar Width", "scrollbar_width", 4, 20, self.update_scrollbar_width, DEFAULT_SW),
            ("Scrollbar Radius", "scroll_radius", 0, self.scrollbar_width // 2, self.update_scroll_radius, DEFAULT_SR)
        ]
        for label, key, min_val, max_val, update_func, default_val in sliders:
            self.add_slider_row(config_layout, label, key, min_val, max_val, update_func, default_val)
            config_layout.addSpacing(1)

        scroll_area_layout.addWidget(self.config_group)
        main_layout.addWidget(scroll_area)

        apply_button = QPushButton("Apply and Save")
        apply_button.clicked.connect(self.apply_colors)
        main_layout.addWidget(apply_button)

    def filter_items(self):
        search_text = self.search_bar.text().lower()

        for group_title, elements in self.groups:
            form_layout = self.form_layouts[group_title]
            group_label_item = form_layout.parentWidget().layout().itemAt(
                form_layout.parentWidget().layout().indexOf(form_layout) - 1
            )
            group_label = group_label_item.widget()

            group_visible = False
            visible_rows = 0  # Count visible rows in this group
            for row in range(form_layout.rowCount()):
                label_item = form_layout.itemAt(row, QFormLayout.LabelRole)
                field_item = form_layout.itemAt(row, QFormLayout.FieldRole)

                if label_item and field_item:
                    label_text = label_item.widget().text().lower()
                    row_visible = search_text in label_text

                    label_item.widget().setVisible(row_visible)

                    if isinstance(field_item, QLayout):
                        for j in range(field_item.count()):
                            widget = field_item.itemAt(j).widget()
                            if widget:
                                widget.setVisible(row_visible)
                    elif field_item.widget():
                        field_item.widget().setVisible(row_visible)

                    if row_visible:
                        visible_rows += 1
                    group_visible |= row_visible

            group_label.setVisible(group_visible)

            # Adjust form layout spacing based on visible rows
            if group_visible:
                if visible_rows == 0:
                    form_layout.setVerticalSpacing(0)  # No spacing if no rows are visible
                else:
                    default_spacing = 6
                    form_layout.setVerticalSpacing(default_spacing)
            else:
                form_layout.setVerticalSpacing(0)  # No spacing if the group is hidden

    def add_color_picker(self, layout, label, key):
        color_name = self.current_colors.get(key, "")
        button = QPushButton(color_name or "Default", objectName="EncasedRadiusHalved", fixedWidth=150, fixedHeight=BUTTON_HEIGHT)
        button.clicked.connect(lambda _, btn=button, k=key: self.choose_color(btn, k))
        reset_button = QPushButton("X", objectName="ResetButtonEncasedHalf", fixedWidth=BUTTON_HEIGHT + 2, fixedHeight=BUTTON_HEIGHT)
        reset_button.clicked.connect(lambda _, btn=button, k=key: self.reset_color(btn, k))
        self.set_reset_button_style(reset_button, flat_left=True)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addWidget(reset_button)
        layout.addRow(label, button_layout)
        self.color_pickers[key] = button
        reset_button.setStyleSheet(COLOR_RESET_BUTTON_STYLE) # This line is important
        if color_name:
            self.set_button_color(button, color_name)
        else:
            self.update_default_button_style(button)

    def add_slider_row(self, layout, label, key, min_val, max_val, update_func, default_val):
        label_widget = QLabel(label)
        slider = ScrollRejectionSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(getattr(self, key))
        slider.valueChanged.connect(update_func)
        value_label = QLabel(str(getattr(self, key)))
        reset_button = QPushButton("X", objectName="ResetButtonEncased", fixedWidth=BUTTON_HEIGHT + 5, fixedHeight=BUTTON_HEIGHT)
        reset_button.clicked.connect(lambda _, s=slider, d=default_val, v=value_label: self.reset_slider(s, d, v))
        self.set_reset_button_style(reset_button, flat_left=False)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(label_widget)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(value_label)
        slider_layout.addWidget(reset_button)
        layout.addLayout(slider_layout)
        setattr(self, f"{key}_slider", slider)
        setattr(self, f"{key}_value_label", value_label)
        reset_button.setStyleSheet("") # This line is important

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
        hover_color = self.brightness_adjuster.adjust_brightness_dynamically(color_name, DBH)
        pressed_color = self.brightness_adjuster.adjust_brightness(color_name, DBP)
        text_color = self.contrast_color(color_name)

        button.setStyleSheet(f"""
            QPushButton, QPushButton#EnchasedRadiusHalved {{ background-color: {color_name}; color: {text_color}; {COLOR_PICKER_BUTTON_STYLE} }}
            QPushButton:hover, QPushButton#EnchasedRadiusHalved:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed, QPushButton#EnchasedRadiusHalved:pressed {{ background-color: {pressed_color}; }}
        """)

    def set_reset_button_style(self, reset_button, flat_left=False):
        base_color = self.current_colors.get("reset_button_background") or Theme(self.theme).colors["reset_button_background"]
        hover_color = self.brightness_adjuster.adjust_brightness_dynamically(base_color, DBH)
        pressed_color = self.brightness_adjuster.adjust_brightness(base_color, DBP)
        border_style = COLOR_RESET_BUTTON_STYLE if flat_left else ""

        reset_button.setStyleSheet(f"""
            #ResetButton, #ResetButtonHalf, #ResetButtonEncased, #ResetButtonEncasedHalf {{ background-color: {base_color}; {border_style}; }}
            #ResetButton:hover, #ResetButtonHalf:hover, #ResetButtonEncased:hover, #ResetButtonEncasedHalf:hover {{ background-color: {hover_color}; }}
            #ResetButton:pressed, #ResetButtonHalf:pressed, #ResetButtonEncased:pressed, #ResetButtonEncasedHalf:pressed {{ background-color: {pressed_color}; }}
        """)

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
        self.parent().apply_custom_colors(self.current_colors, self.border_radius, self.border_size, self.border_size_interactables, self.checkbox_radius, self.scroll_radius, self.scrollbar_width)

    def update_value(self, key, value, value_label):
        setattr(self, key, value)
        value_label.setText(f"{value}")
        self.update_preview()

    def update_border_radius(self, value):
        self.update_value("border_radius", value, self.border_radius_value_label)

    def update_border_size(self, value):
        self.update_value("border_size", value, self.border_size_value_label)

    def update_border_size_interactables(self, value):
        self.update_value("border_size_interactables", value, self.border_size_interactables_value_label)

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

class ScrollRejectionSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()