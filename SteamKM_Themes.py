# SteamKM_Themes.py
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QColorDialog, QDialog, QFormLayout, QGroupBox, QSlider, QScrollArea)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Constants
BUTTON_HEIGHT = 31
CHECKBOX_SIZE = 18  # Width and Height
DEFAULT_BR = 6  # Border Radius
DEFAULT_BS = 0  # Border Size
DEFAULT_BSI = 0  # Border Size Interactables
DEFAULT_CR = 4  # Checkbox Radius
DEFAULT_SR = 3  # Scrollbar Radius
DEFAULT_SW = 14  # Scrollbar Width
DBH = 1.2  # Dynamic brightness hover value
DBP = 0.95  # Dynamic brightness press value
PADDING = "padding: 6px"
DEEP_TITLE_PADDING = "padding: 8px"
BUTTON_PADDING = "padding: 1px 12px;"
COLOR_PICKER_BUTTON_STYLE = "border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;"
COLOR_RESET_BUTTON_STYLE = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: 0px;"

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
        colors = {
            "main_background": ("#2e2e2e", "#FFFFFF"),
            "text_color": ("white", "black"),
            "add_games_background": ("#404040", "#e6eefa"),
            "search_bar_background": ("#404040", "#e6eefa"),
            "label_background": ("#494949", "#c8deff"),
            "scrollbar_background": ("#424f47", "#c7e0f8"),
            "scrollbar_handle": ("#62a88e", "#9bc3ff"),
            "button_background": ("#525252", "#d6e8ff"),
            "reset_button_background": ("#ff6666", "#ff9999"),
            "checkbox_background_unchecked": ("#444444", "#dadfe6"),
            "checkbox_background_checked": ("#62a88e", "#91baff"),
            "table_background": ("#2e2e2e", "#FFFFFF"),
            "table_border_color": ("#4d4d4d", "#d9e3f2"),
            "table_item_selected": ("#62a88e", "#a6c7ff"),
            "table_gridline_color": ("#3d3d3d", "#e8e8e8"),
            "header_background": ("#444444", "#d9d9d9"),
            "combobox_background": ("#525252", "#d6e8ff"),
            "combobox_hover": ("#748a81", "#bdd5fc"),
            "combobox_dropdown_background": ("#444444", "#d9f8ff"),
            "interactables_border_color": ("#404040", "#c1d6f5"),
            "generic_border_color": ("#4d4d4d", "#d9e3f2"),
        }
        theme_index = 0 if theme == "dark" else 1
        return {key: value[theme_index] for key, value in colors.items()}
    
    def get_icon_color(self):
        return self.colors["text_color"]

    def generate_stylesheet(self):
        colors = self.colors
        for key in ["button_background", "reset_button_background"]:
            colors[f"{key}_hover"] = self.brightness_adjuster.adjust_brightness_dynamically(colors[key], DBH)
            colors[f"{key}_pressed"] = self.brightness_adjuster.adjust_brightness(colors[key], DBP)

        styles = {
            "QWidget": f"background-color: {colors['main_background']}; color: {colors['text_color']}; border-radius: {self.border_radius}px;",
            "QGroupBox": f"border: {max(self.border_size, 2)}px solid {colors['generic_border_color']}; border-radius: {self.border_radius}px; margin-right: 5px;",
            "QLabel": f"background-color: transparent; color: {colors['text_color']}; border-radius: 0;",
            "#FoundCountLabel": f"background-color: {colors['label_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; border-radius: {self.border_radius}px; {PADDING};",
            "#DeepLabel": f"background-color: {colors['label_background']}; padding: 6px; height: {BUTTON_HEIGHT}; {DEEP_TITLE_PADDING}; margin-bottom: 4px; border: {self.border_size}px solid {colors['generic_border_color']}; border-radius: {self.border_radius / 2}px;",
            "QTextEdit": f"background-color: {colors['add_games_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; padding-left: 5px; padding-top: 4px; height: {BUTTON_HEIGHT};",
            "QLineEdit": f"background-color: {colors['search_bar_background']}; border: {self.border_size}px solid {colors['generic_border_color']}; padding-left: 7px; height: {BUTTON_HEIGHT}; {BUTTON_PADDING};",
            "#CategoryLineEdit": f"background-color: {colors['search_bar_background']}; {COLOR_PICKER_BUTTON_STYLE}; padding-left: 7px; height: {BUTTON_HEIGHT}; border-top: {self.border_size_interactables}px solid {colors['interactables_border_color']}; border-bottom: {self.border_size_interactables}px solid {colors['interactables_border_color']}; border-left: {self.border_size_interactables}px solid {colors['interactables_border_color']};",
            "QDockWidget::title": f"{PADDING};",
            "QComboBox": f"background-color: {colors['combobox_background']}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; {BUTTON_PADDING}; height: {BUTTON_HEIGHT};",
            "QComboBox:hover": f"background-color: {colors['combobox_hover']};",
            "QComboBox:item:selected": f"background-color: {colors['table_item_selected']}; {BUTTON_PADDING};",
            "QComboBox:drop-down": "height: 0; width: 0;",
            "QComboBox QAbstractItemView": f"border: {max(self.border_size, 2)}px solid {colors['interactables_border_color']};",
            "QPushButton": f"background-color: {colors['button_background']}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; {BUTTON_PADDING}; height: {BUTTON_HEIGHT};",
            "QPushButton:hover, QMenu::item:selected": f"background-color: {colors['button_background_hover']};",
            "QPushButton:pressed, QMenu::item:pressed": f"background-color: {colors['button_background_pressed']};",
            "#ResetButton": f"background-color: {colors['reset_button_background']}; border: {self.border_size_interactables}px solid {colors['interactables_border_color']}; height: {BUTTON_HEIGHT};",
            "#ResetButton:hover": f"background-color: {colors['reset_button_background_hover']};",
            "#ResetButton:pressed": f"background-color: {colors['reset_button_background_pressed']};",
            ".icon": f"fill: {colors['text_color']}; stroke: {colors['text_color']};",
            "QCheckBox::indicator:unchecked": f"background-color: {colors['checkbox_background_unchecked']}; height: {CHECKBOX_SIZE}px; width: {CHECKBOX_SIZE}px; border: 0px; border-radius: {self.checkbox_radius}px;",
            "QCheckBox::indicator:checked": f"background-color: {colors['checkbox_background_checked']}; height: {CHECKBOX_SIZE}px; width: {CHECKBOX_SIZE}px; border: 0px; border-radius: {self.checkbox_radius}px;",
            "QHeaderView": f"background-color: {colors['table_background']}; border: none; gridline-color: {colors['table_gridline_color']};",
            "QHeaderView::section": f"background-color: {colors['table_background']};",
            "QTableCornerButton::section": f"background-color: {colors['table_background']};",
            "QTableWidget": f"background-color: {colors['table_background']}; border: {max(self.border_size, 2)}px solid {colors['table_border_color']}; {PADDING}; gridline-color: {colors['table_gridline_color']};",
            "QTableWidget::item": "background-color: transparent;",
            "QTableWidget::item:selected": f"background-color: {colors['table_item_selected']};",
            "QScrollBar": f"background-color: {colors['scrollbar_background']}; border-radius: {self.scroll_radius}px; border: 0;",
            "QScrollBar:vertical": f"width: {self.scrollbar_width}px;",
            "QScrollBar:horizontal": f"height: {self.scrollbar_width}px;",
            "QScrollBar::handle, QProgressBar::chunk": f"background-color: {colors['scrollbar_handle']}; border-radius: {self.scroll_radius}px; border: 0;",
            "QScrollBar::add-page, QScrollBar::sub-page": "background-color: none;",
            "QScrollBar::add-line, QScrollBar::sub-line": "width: 0px; height: 0px;",
            "QProgressBar": f"background-color: {colors['scrollbar_background']}; border-radius: {self.scroll_radius}px; border: 0; text-align: center; height: 6px;",
            "QMenu": f"background-color: {colors['main_background']}; {PADDING}; border: {max(self.border_size, 2)}px solid {colors['interactables_border_color']};",
            "QMenu::item": f"{PADDING} 15px; border-radius: {self.border_radius / 2}px;",
        }

        return "\n".join(f"{selector} {{ {style} }}" for selector, style in styles.items())

class BrightnessAdjuster:
    def __init__(self):
        self._brightness_cache = {}

    def adjust_brightness(self, hex_color, factor):
        if (hex_color, factor) not in self._brightness_cache:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            r, g, b = [min(max(0, int(c * factor)), 255) for c in (r, g, b)]
            self._brightness_cache[(hex_color, factor)] = f"#{r:02x}{g:02x}{b:02x}"
        return self._brightness_cache[(hex_color, factor)]

    def adjust_brightness_dynamically(self, hex_color, factor):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
 
        # The idea is to reduce the factor for lighter colors and increase it for darker ones.
        dynamic_factor = factor + (0.5 - luminance) * 0.35 # Last value controls the range of the dynamic adjustment

        return self.adjust_brightness(hex_color, dynamic_factor)

class ColorConfigDialog(QDialog):
    def __init__(self, parent=None, current_colors=None, theme="dark", border_radius=DEFAULT_BR, border_size=DEFAULT_BS,
                 border_size_interactables=DEFAULT_BSI, checkbox_radius=DEFAULT_CR, scroll_radius=DEFAULT_SR,
                 scrollbar_width=DEFAULT_SW):
        super().__init__(parent)
        self.setWindowTitle("Color Customization")
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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        scroll_area_layout = QVBoxLayout(scroll_area_widget)

        groups = [
            ("General Colors", [
                ("Text", "text_color"),
                ("Main Background", "main_background"),
                ("Label Background", "label_background"),
            ]),
            ("Borders", [
                ("Generic", "generic_border_color"),
                ("Interactables", "interactables_border_color"),
                ("Game List", "table_border_color"),
            ]),
            ("Interactables", [
                ("Button Color", "button_background"),
                ("Reset Button Color", "reset_button_background"),
                ("Checkbox Checked", "checkbox_background_checked"),
                ("Checkbox Unchecked", "checkbox_background_unchecked"),
                ("Category Background", "combobox_background"),
                ("Category Hover", "combobox_hover"),
                ("Category Dropdown Background", "combobox_dropdown_background"),
            ]),
            ("Add & Search", [
                ("Search Background", "search_bar_background"),
                ("Add Games Background", "add_games_background"),
            ]),
            ("Game List", [
                ("Gridline", "table_gridline_color"),
                ("Background", "table_background"),
                ("Selected Item", "table_item_selected"),
            ]),
            ("Scroll & Progress bar", [
                ("Handle", "scrollbar_handle"),
                ("Background", "scrollbar_background"),
            ]),
        ]

        for title, elements in groups:
            group = QGroupBox()
            self.setup_group(group, title, elements)
            scroll_area_layout.addWidget(group)
            scroll_area_layout.addSpacing(20)

        self.setup_border_group()
        scroll_area_layout.addWidget(self.border_group)
        main_layout.addWidget(scroll_area)

        apply_button = QPushButton("Apply and Save")
        apply_button.clicked.connect(self.apply_colors)
        main_layout.addWidget(apply_button)

    def setup_group(self, group, title, elements):
        layout = QVBoxLayout(group)
        title_label = QLabel(title)
        title_label.setObjectName("DeepLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        form_layout = QFormLayout()
        for label, key in elements:
            self.add_color_picker(form_layout, label, key)
        layout.addLayout(form_layout)

    def add_color_picker(self, layout, label, key):
        color_name = self.current_colors.get(key, "")
        button = QPushButton(color_name or "Default")
        button.setFixedSize(150, BUTTON_HEIGHT)
        button.clicked.connect(lambda _, btn=button, k=key: self.choose_color(btn, k))
        reset_button = QPushButton("X")
        reset_button.setObjectName("ResetButton")
        reset_button.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
        reset_button.clicked.connect(lambda _, btn=button, k=key: self.reset_color(btn, k))
        self.set_reset_button_style(reset_button, flat_left=True)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addWidget(reset_button)
        layout.addRow(label, button_layout)
        self.color_pickers[key] = button
        reset_button.setStyleSheet(COLOR_RESET_BUTTON_STYLE)
        if color_name:
            self.set_button_color(button, color_name)
        else:
            self.update_default_button_style(button)

    def setup_border_group(self):
        self.border_group = QGroupBox()
        layout = QVBoxLayout(self.border_group)
        border_group_label = QLabel("Border Settings")
        border_group_label.setObjectName("DeepLabel")
        border_group_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(border_group_label)

        sliders = [
            ("Border Radius", "border_radius", 0, BUTTON_HEIGHT // 2, self.update_border_radius, DEFAULT_BR),
            ("Border Size", "border_size", 0, 3, self.update_border_size, DEFAULT_BS),
            ("Border Size Interactables", "border_size_interactables", 0, 3, self.update_border_size_interactables, DEFAULT_BSI),
            ("Checkbox Radius", "checkbox_radius", 0, CHECKBOX_SIZE // 2, self.update_checkbox_radius, DEFAULT_CR),
            ("Scrollbar Width", "scrollbar_width", 8, 14, self.update_scrollbar_width, DEFAULT_SW),
            ("Scroll Radius", "scroll_radius", 0, self.scrollbar_width // 2, self.update_scroll_radius, DEFAULT_SR)
        ]
        for label, key, min_val, max_val, update_func, default_val in sliders:
            self.add_slider_row(layout, label, key, min_val, max_val, update_func, default_val)

    def add_slider_row(self, layout, label, key, min_val, max_val, update_func, default_val):
        label_widget = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(getattr(self, key))
        slider.valueChanged.connect(update_func)
        value_label = QLabel(str(getattr(self, key)))
        reset_button = QPushButton("X")
        reset_button.setObjectName("ResetButton")
        reset_button.setFixedSize(BUTTON_HEIGHT + 5, BUTTON_HEIGHT)
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
        reset_button.setStyleSheet("")

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
            QPushButton {{ background-color: {color_name}; color: {text_color}; {COLOR_PICKER_BUTTON_STYLE} }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ background-color: {pressed_color}; }}
        """)

    def set_reset_button_style(self, reset_button, flat_left=False):
        base_color = self.current_colors.get("reset_button_background") or Theme(self.theme).colors["reset_button_background"]
        hover_color = self.brightness_adjuster.adjust_brightness_dynamically(base_color, DBH)
        pressed_color = self.brightness_adjuster.adjust_brightness(base_color, DBP)
        border_style = COLOR_RESET_BUTTON_STYLE if flat_left else ""

        reset_button.setStyleSheet(f"""
            #ResetButton {{ background-color: {base_color}; {border_style}; }}
            #ResetButton:hover {{ background-color: {hover_color}; }}
            #ResetButton:pressed {{ background-color: {pressed_color}; }}
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