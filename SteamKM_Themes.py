# SteamKM_Themes.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QColorDialog, QDialog, QFormLayout, QGroupBox, QSlider, QScrollArea
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from SteamKM_Icons import DOWN_ARROW_ICON

BUTTON_HEIGHT = 33
DEFAULT_BR = 6  # Border Radius
DEFAULT_BS = 0  # Border Size
DEFAULT_CR = 4  # Checkbox Radius
DEFAULT_SR = 3  # Scrollbar Radius
DEFAULT_SW = 14 # Scrollbar Width
PADDING = "5"
DEFAULT_PADDING = "padding: 0px 12px;"
COLOR_PICKER_BUTTON_STYLE = "border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;"
COLOR_RESET_BUTTON_STYLE = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: 0px;"

class Theme:
    def __init__(self, theme="dark", custom_colors=None, border_radius=DEFAULT_BR, border_size=DEFAULT_BS, checkbox_radius=DEFAULT_CR, scroll_radius=DEFAULT_SR, scrollbar_width=DEFAULT_SW):
        self.theme = theme
        self.border_radius = border_radius
        self.border_size = border_size
        self.checkbox_radius = checkbox_radius
        self.scroll_radius = scroll_radius
        self.scrollbar_width = scrollbar_width
        self.colors = self.get_theme_colors(theme)
        if custom_colors:
            self.colors.update(custom_colors)

    def get_theme_colors(self, theme):
        # Index 0: dark theme, Index 1: light theme
        colors = {
            "main_background": ("#2e2e2e", "#FFFFFF"),
            "text_color": ("white", "black"),
            "add_games_background": ("#404040", "#e6eefa"),
            "search_bar_background": ("#404040", "#e6eefa"),
            "label_background": ("#404040", "#e6eefa"),
            "scrollbar_background": ("#424f47", "#c7e0f8"),
            "scrollbar_handle": ("#62a88e", "#9bc3ff"),
            "button_background": ("#525252", "#d6e8ff"),
            "button_hover": ("#689484", "#adcbfb"),
            "button_pressed": ("#62a88e", "#9bc3ff"),
            "reset_button_background": ("#ff6666", "#ff9999"),
            "reset_button_hover": ("#ff9999", "#ff6666"),
            "reset_button_pressed": ("#ff4d4d", "#eb4646"),
            "checkbox_background_unchecked": ("#444444", "#dadfe6"),
            "checkbox_background_checked": ("#62a88e", "#91baff"),
            "table_background": ("#2e2e2e", "#FFFFFF"),
            "table_border_color": ("#4d4d4d", "#d9e3f2"),
            "table_item_selected": ("#62a88e", "#a6c7ff"),
            "table_gridline_color": ("#3d3d3d", "#e8e8e8"),
            "header_background": ("#444444", "#d9d9d9"),
            "combobox_background": ("#525252", "#d6e8ff"),
            "combobox_dropdown_background": ("#444444", "#d9f8ff"),
            "interactables_border_color": ("#404040", "#c1d6f5"),
            "generic_border_color": ("#4d4d4d", "#d9e3f2"),
        }
        theme_index = 0 if theme == "dark" else 1
        return {key: value[theme_index] for key, value in colors.items()}

    def generate_stylesheet(self):
        colors = self.colors
        CHECKBOX_RADIUS = str(self.checkbox_radius)
        BORDER_RADIUS = str(self.border_radius)
        BORDER_SIZE = str(self.border_size)
        MINIMUM_BORDER_SIZE = str(max(self.border_size, 2))
        SCROLL_RADIUS = str(self.scroll_radius)
        SCROLLBAR_WIDTH = str(self.scrollbar_width)

        theme_stylesheet = f"""
            QWidget {{ background-color: {colors['main_background']}; color: {colors['text_color']}; border-radius: {BORDER_RADIUS}px; }}
            QLabel {{ background-color: transparent; color: {colors['text_color']}; border-radius: 0; }}
            #FoundCountLabel {{ background-color: {colors['label_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; border-radius: {BORDER_RADIUS}px; padding: {PADDING}px; }}
            #DeepTitle {{ background-color: {colors['label_background']}; padding: 6px; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; border-radius: {BORDER_RADIUS}px; height: {BUTTON_HEIGHT}; padding: {PADDING}px 12px; }}
            QTextEdit {{ background-color: {colors['add_games_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; {DEFAULT_PADDING}; padding-top: 4px; height: {BUTTON_HEIGHT}; }}
            QLineEdit {{ background-color: {colors['search_bar_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; {DEFAULT_PADDING}; height: {BUTTON_HEIGHT}; }}
            QGroupBox {{ border: {MINIMUM_BORDER_SIZE}px solid {colors['generic_border_color']}; border-radius: {BORDER_RADIUS}px; margin-right: 5px; }}
            QComboBox {{ background-color: {colors['combobox_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; {DEFAULT_PADDING}; height: {BUTTON_HEIGHT}; }}
            QComboBox:item:selected {{ background-color: {colors['table_item_selected']}; {DEFAULT_PADDING}; }}
            QComboBox:drop-down {{ height: 0; width: 0; }}
            QComboBox QAbstractItemView {{ border: {MINIMUM_BORDER_SIZE}px solid {colors['interactables_border_color']}; }}
            QPushButton {{ background-color: {colors['button_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; {DEFAULT_PADDING}; height: {BUTTON_HEIGHT}; }}
            QPushButton:hover, QComboBox:hover {{ background-color: {colors['button_hover']}; }}
            QPushButton:pressed {{ background-color: {colors['button_pressed']}; }}
            QPushButton#resetButton {{ background-color: {colors['reset_button_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; }}
            QPushButton#resetButton:hover {{ background-color: {colors['reset_button_hover']}; }}
            QPushButton#resetButton:pressed {{ background-color: {colors['reset_button_pressed']}; }}
            QCheckBox::indicator:unchecked {{ background-color: {colors['checkbox_background_unchecked']}; height: 18; width: 18; border: 0px; border-radius: {CHECKBOX_RADIUS}px; }}
            QCheckBox::indicator:checked {{ background-color: {colors['checkbox_background_checked']}; height: 18; width: 18; border: 0px; border-radius: {CHECKBOX_RADIUS}px; }}
            QHeaderView {{ background-color: {colors['table_background']}; border: none; gridline-color: {colors['table_gridline_color']}; }}
            QHeaderView::section {{ background-color: {colors['table_background']}; }}
            QTableCornerButton::section {{ background-color: {colors['table_background']}; }}
            QTableWidget {{ background-color: {colors['table_background']}; border: {MINIMUM_BORDER_SIZE}px solid {colors['table_border_color']}; padding: {PADDING}px; gridline-color: {colors['table_gridline_color']}; }}
            QTableWidget::item {{ background-color: transparent; }}
            QTableWidget::item:selected {{ background-color: {colors['table_item_selected']}; }}
            QScrollBar {{ background-color: {colors['scrollbar_background']}; border-radius: {SCROLL_RADIUS}px; }}
            QScrollBar:vertical {{ width: {SCROLLBAR_WIDTH}px; }}
            QScrollBar:horizontal {{ height: {SCROLLBAR_WIDTH}px; }}
            QScrollBar::handle {{ background-color: {colors['scrollbar_handle']}; border-radius: {SCROLL_RADIUS}px }}
            QScrollBar::add-page, QScrollBar::sub-page {{ background-color: none; }}
            QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
            QProgressBar {{ background-color: {colors['scrollbar_background']}; border-radius: {SCROLL_RADIUS}px; text-align: center; height: 6px }}
            QProgressBar::chunk {{ background-color: {colors['scrollbar_handle']}; border-radius: {SCROLL_RADIUS}px }}
            QMenu {{ background-color: {colors['main_background']}; padding: {PADDING}px; border: {MINIMUM_BORDER_SIZE}px solid {colors['interactables_border_color']}; }}
            QMenu::item {{ padding: {PADDING}px 15px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {colors['button_hover']}; }}
            QMenu::item:pressed {{ background-color: {colors['button_pressed']}; }}
        """
        
        return theme_stylesheet

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
                ("Label Background", "label_background"),
                ("Search Background", "search_bar_background"),
                ("Add Games Background", "add_games_background"),
            ]),
            ("Border Colors", [
                ("Generic Border", "generic_border_color"),
                ("Interactables Border", "interactables_border_color"),
                ("Game List Border", "table_border_color"),
            ]),
            ("Game List", [
                ("Gridline", "table_gridline_color"),
                ("Background", "table_background"),
                ("Selected Item", "table_item_selected"),
            ]),
            ("Scrollbar and Progress bar", [
                ("Handle", "scrollbar_handle"),
                ("Background", "scrollbar_background"),
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
        # Create a vertical layout for the group
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Add the title as a label inside the box
        title_label = QLabel(title)
        title_label.setObjectName("DeepTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(5)

        # Add the elements below the title
        form_layout = QFormLayout()
        for label, key in elements:
            self.add_color_picker(form_layout, label, key)
        layout.addLayout(form_layout)

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
        self.border_group = QGroupBox()
        layout = QVBoxLayout()

        # Add the title as a label inside the box
        border_group = QLabel("Border Size and Radius")
        border_group.setObjectName("DeepTitle")
        border_group.setAlignment(Qt.AlignCenter)
        layout.addWidget(border_group)
        layout.addSpacing(4)
        self.border_group.setLayout(layout)

        sliders = [
            ("Border Radius", "border_radius", 0, 13, self.update_border_radius, DEFAULT_BR),
            ("Border Size", "border_size", 0, 3, self.update_border_size, DEFAULT_BS),
            ("Checkbox Radius", "checkbox_radius", 0, 9, self.update_checkbox_radius, DEFAULT_CR),
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