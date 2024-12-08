from PySide6.QtCore import Qt

DEFAULT_BR = 6  # Border Radius
DEFAULT_BS = 0  # Border Size
DEFAULT_CR = 4  # Checkbox Radius
DEFAULT_SR = 3  # Scrollbar Radius
DEFAULT_SW = 12  # Scrollbar Width
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
        self.colors = self.get_theme_colors(theme)  # Get colors based on the theme
        if custom_colors:
            self.colors.update(custom_colors)  # Update with custom colors

    def get_theme_colors(self, theme):
        # Index 0: dark theme, Index 1: light theme
        colors = {
            "main_background": ("#2e2e2e", "#FFFFFF"),
            "text_color": ("white", "black"),
            "add_games_background": ("#404040", "#e6eefa"),
            "search_bar_background": ("#404040", "#e6eefa"),
            "found_games_background": ("#404040", "#e6eefa"),
            "scrollbar_background": ("#404040", "#e1e9f2"),
            "scrollbar_handle": ("#62a88e", "#a6c7ff"),
            "button_background": ("#525252", "#d6e8ff"),
            "button_hover": ("#748a81", "#bdd5fc"),
            "button_pressed": ("#71a892", "#a6c7ff"),
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
            "combobox_background": ("#525252", "#e1ebfa"),
            "combobox_dropdown_background": ("#444444", "#d9f8ff"),
            "interactables_border_color": ("#404040", "#d9e3f2"),
            "generic_border_color": ("#4d4d4d", "#d9e3f2"),
        }
        theme_index = 0 if theme == "dark" else 1
        return {key: value[theme_index] for key, value in colors.items()}

    def generate_stylesheet(self):
        colors = self.colors
        CHECKBOX_RADIUS = str(self.checkbox_radius)
        BORDER_RADIUS = str(self.border_radius)
        BORDER_SIZE = str(self.border_size)
        LIMITED_BORDER_SIZE = str(max(self.border_size, 2))
        SCROLL_RADIUS = str(self.scroll_radius)
        SCROLLBAR_WIDTH = str(self.scrollbar_width)
        PADDING = "5"

        theme_stylesheet = f"""
            QWidget {{ background-color: {colors['main_background']}; color: {colors['text_color']}; border-radius: {BORDER_RADIUS}px }}
            #foundCountLabel {{ background-color: {colors['found_games_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; padding: {PADDING}px; }}
            QTextEdit {{ background-color: {colors['add_games_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; padding: {PADDING}px; }}
            QLineEdit {{ background-color: {colors['search_bar_background']}; border: {BORDER_SIZE}px solid {colors['generic_border_color']}; padding: {PADDING}px; }}
            QComboBox {{  background-color: {colors['combobox_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; padding: {PADDING}px; }}
            QComboBox::drop-down {{ height: 0px; }}
            QComboBox QAbstractItemView {{ background-color: {colors['combobox_background']};  border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; margin-top: 5px; padding: {PADDING}px; selection-background-color: {colors['table_item_selected']}; selection-color: {colors['table_item_selected']}; }}
            QComboBox QAbstractItemView::item {{ padding: 5px 10px; }}
            QGroupBox {{ border: {LIMITED_BORDER_SIZE}px solid {colors['generic_border_color']}; border-radius: {BORDER_RADIUS}px; padding-top: 20px; }}
            QGroupBox::title {{ background-color: {colors['generic_border_color']}; padding: 4px; subcontrol-origin: margin; subcontrol-position: top left; }}
            QPushButton {{ background-color: {colors['button_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']};  padding: {PADDING}px 10px; }}
            QPushButton:hover {{ background-color: {colors['button_hover']}; }}
            QPushButton:pressed {{ background-color: {colors['button_pressed']}; }}
            QPushButton#resetButton {{ background-color: {colors['reset_button_background']}; border: {BORDER_SIZE}px solid {colors['interactables_border_color']}; padding: {PADDING}px 10px; }}
            QPushButton#resetButton:hover {{ background-color: {colors['reset_button_hover']}; }}
            QPushButton#resetButton:pressed {{ background-color: {colors['reset_button_pressed']}; }}
            QCheckBox::indicator:unchecked {{ background-color: {colors['checkbox_background_unchecked']}; border: 0px solid; border-radius: {CHECKBOX_RADIUS}px; }}
            QCheckBox::indicator:checked {{ background-color: {colors['checkbox_background_checked']}; border: 0px solid; border-radius: {CHECKBOX_RADIUS}px; }}
            QCheckBox::indicator:disabled {{ background-color: #ff4d4d; border: 0px solid; border-radius: {CHECKBOX_RADIUS}px; }}
            QTableWidget {{ background-color: transparent; border: {LIMITED_BORDER_SIZE}px solid {colors['table_border_color']}; padding: {PADDING}px; gridline-color: {colors['table_gridline_color']}; }}
            QTableWidget::title {{ background-color: {colors['table_background']}; padding: {PADDING}px; gridline-color: {colors['table_gridline_color']}; }}
            QTableWidget::item {{ background-color: {colors['table_background']}; }}
            QTableWidget::item:selected {{ background-color: {colors['table_item_selected']}; }}
            QScrollBar {{ background-color: {colors['scrollbar_background']}; border-radius: {SCROLL_RADIUS}px; margin: 0px; }}
            QScrollBar:vertical {{ width: {SCROLLBAR_WIDTH}px; }}
            QScrollBar:horizontal {{ height: {SCROLLBAR_WIDTH}px; }}
            QScrollBar::handle {{ background-color: {colors['scrollbar_handle']}; border-radius: {SCROLL_RADIUS}px }}
            QScrollBar::add-page, QScrollBar::sub-page {{ background-color: none; }}
            QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
            QMenu {{ background-color: {colors['main_background']}; padding: {PADDING}px; border: {LIMITED_BORDER_SIZE}px solid {colors['interactables_border_color']}; }}
            QMenu::item {{ padding: {PADDING}px 15px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {colors['button_hover']}; }}
            QMenu::item:pressed {{ background-color: {colors['button_pressed']}; }}
        """
        
        return theme_stylesheet