# Themes.py
import logging
from Config import (DEFAULT_RADIUS, DEFAULT_BORDER_SIZE, DEFAULT_CHECKBOX_RADIUS, DEFAULT_BAR_RADIUS, DEFAULT_BAR_THICKNESS, TABLE_CELL_RADIUS, BUTTON_HEIGHT, CHECKBOX_SIZE,
                    PADDING, BUTTON_PADDING, COLOR_PICKER_BUTTON_STYLE, COLOR_RESET_BUTTON_STYLE, DBH, DBP, DV_SCROLLBAR, GROUPBOX_PADDING, CONFIG_DIR)
from Icons import DOWN_ARROW_ICON, UP_ARROW_ICON
import os

# Create a permanent directory for arrow icons
ARROW_ICON_DIR = os.path.join(CONFIG_DIR, "arrow_icons")
os.makedirs(ARROW_ICON_DIR, exist_ok=True)
# Define the fixed path for the arrow icons
FIXED_ARROW_ICON_PATH = os.path.join(ARROW_ICON_DIR, "down_arrow.svg")
FIXED_UP_ARROW_ICON_PATH = os.path.join(ARROW_ICON_DIR, "up_arrow.svg")

class BrightnessAdjuster:
    def __init__(self):
        self._brightness_cache = {}

    def adjust_brightness(self, hex_color, factor, dynamic=False):
        # Return early if inputs are None
        if (hex_color is None or factor is None):
            return "#808080"  # Return grey as a fallback

        # Check if we already calculated this combination
        if (hex_color, factor, dynamic) in self._brightness_cache:
            return self._brightness_cache[(hex_color, factor, dynamic)]

        # Validate that hex_color is a proper hex color string
        if not isinstance(hex_color, str) or not hex_color.startswith('#') or len(hex_color) != 7:
            logging.warning(f"Invalid color format: {hex_color}, using fallback grey")
            return "#808080"  # Return grey as a fallback

        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            if dynamic:
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                factor = factor + (0.5 - luminance) * 0.35  # Dynamic adjustment
            r, g, b = [min(max(0, int(c * factor)), 255) for c in (r, g, b)]
            self._brightness_cache[(hex_color, factor, dynamic)] = f"#{r:02x}{g:02x}{b:02x}"
            return self._brightness_cache[(hex_color, factor, dynamic)]
        except (ValueError, IndexError) as e:
            logging.error(f" adjusting brightness for {hex_color}: {e}")
            return "#808080"  # Return grey as a fallback

    def adjust_brightness_dynamically(self, hex_color, factor):
        return self.adjust_brightness(hex_color, factor, dynamic=True)

class Theme:
    
    def __init__(self, theme="dark", custom_colors=None, border_radius=DEFAULT_RADIUS, border_size=DEFAULT_BORDER_SIZE, 
                 checkbox_radius=DEFAULT_CHECKBOX_RADIUS, bar_radius=DEFAULT_BAR_RADIUS, bar_thickness=DEFAULT_BAR_THICKNESS):
        self.theme = theme
        self.border_radius = border_radius
        self.border_size = border_size
        self.checkbox_radius = checkbox_radius
        self.bar_radius = bar_radius
        self.bar_thickness = bar_thickness
        self.colors = self.get_theme_colors(theme)
        if custom_colors:
            self.colors.update(custom_colors)
        self.brightness_adjuster = BrightnessAdjuster()
        
        # Update the arrow icon files with the current text color and store the fixed paths
        text_color = self.colors["text_color"]
        self._arrow_icon_path = self._update_arrow_icon(text_color)
        self._up_arrow_icon_path = self._update_up_arrow_icon(text_color) 
    
    @staticmethod
    def _update_arrow_icon(color):
        """Update the fixed down arrow icon file with the specified color"""
        # Generate the SVG content with the new color
        svg_content = DOWN_ARROW_ICON.replace("{{COLOR}}", color)
        
        # Overwrite the fixed file
        try:
            with open(FIXED_ARROW_ICON_PATH, "w", encoding="utf-8") as f:
                f.write(svg_content)
        except Exception as e:
            logging.error(f"Failed to write arrow icon file: {e}")
            # Return a default or indicate failure if needed, though unlikely
            return "" 
            
        # Return the fixed path
        return FIXED_ARROW_ICON_PATH

    @staticmethod
    def _update_up_arrow_icon(color):
        """Update the fixed up arrow icon file with the specified color"""
        # Generate the SVG content with the new color using UP_ARROW_ICON
        svg_content = UP_ARROW_ICON.replace("{{COLOR}}", color)
        
        # Overwrite the fixed file
        try:
            with open(FIXED_UP_ARROW_ICON_PATH, "w", encoding="utf-8") as f:
                f.write(svg_content)
        except Exception as e:
            logging.error(f"Failed to write up arrow icon file: {e}")
            return "" 
            
        # Return the fixed path
        return FIXED_UP_ARROW_ICON_PATH

    def get_theme_colors(self, theme):
        theme_to_index = {"dark": 0, "light": 1, "ocean": 2, "forest": 3, "fire": 4}
        colors = {
            "text_color": ("#ffffff", "#3c3c73", "#e6ffff", "#e6ffe6", "#fff5d7"),
            "main_background": ("#252525", "#eef1ff", "#00557f", "#065242", "#1a0500"),
            "info_window_background": ("#4b4b4b", "#becfff", "#13314b", "#316447", "#732800"),
            "search_background": ("#565656", "#becfff", "#4181b9", "#287855", "#732800"),
            "label_background": ("#646464", "#a5b6ff", "#002e43", "#136c54", "#692300"),
            "changelog_background": ("#232323", "#f5f7ff", "#18344b", "#04332a", "#120400"),
            "groupbox_background": ("#323232", "#dce2ff", "#1f415f", "#083f33", "#3c1300"),
            "button_background": ("#30be88", "#b4c3ff", "#40a5aa", "#3e8354", "#c33e00"),
            "reset_button_background": ("#16a173", "#afafff", "#55557f", "#619e51", "#ff7c30"),
            "combobox_background": ("#009d6f", "#aab1ff", "#007e82", "#4f9e00", "#d76400"),
            "checkbox_background_checked": ("#45e09a", "#8286ff", "#00e6ff", "#6beb3c", "#ffaa00"),
            "checkbox_background_unchecked": ("#4f4f4f", "#bbbbf4", "#002f43", "#00281f", "#5f1d00"),
            "bar_handle": ("#3be69f", "#8286ff", "#3bbaff", "#53c865", "#ff7700"),
            "bar_background": ("#3d6452", "#bbbbf4", "#25789b", "#37734a", "#4d2600"),
            "table_background": ("#232323", "#eceefd", "#203650", "#02372d", "#200a00"),
            "table_item_selected": ("#38b677", "#99aaff", "#3c7ab3", "#3e954c", "#cc5200"),
            "table_gridline_color": ("#3d3d3d", "#bec9ff", "#2f4962", "#144d44", "#331a00"),
            "table_border_color": ("#383838", "#b5c1ff", "#2b5a83", "#025a4a", "#4d2600"),
            "border_color": ("#4d4d4d", "#8b9ffe", "#45a1c9", "#0d8e58", "#661a00"),
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

        # Convert backslashes to forward slashes for CSS compatibility
        arrow_path = self._arrow_icon_path.replace(os.sep, "/")
        up_arrow_path = self._up_arrow_icon_path.replace(os.sep, "/") 

        # Calculate dynamic margin percentage based on corner radius (minimum 2%, maximum 15%)
        dynamic_scroll_margin = max(2, min(15, ((self.border_radius - 8) / 8) * 15 if self.border_radius > 8 else 0))

        styles = {
            "QWidget": f"background-color: transparent; color: {colors['text_color']}; border-radius: {self.border_radius}px;",
            "QMainWindow, QDialog, QDockWidget": f"background-color: {colors['main_background']};",
            "QDockWidget::title": f"{PADDING};",
            "QGroupBox": f"background-color: {colors['groupbox_background']}; border: {max(self.border_size, 0)}px solid {colors['border_color']}; border-radius: {self.border_radius * 1.5}px; {GROUPBOX_PADDING};",
            "QLabel": f"background-color: transparent; padding-left: 2px; padding-right: 2px;",
            "#GameCount": f"background-color: {colors['label_background']}; {PADDING};",
            "#Title": f"background-color: {colors['label_background']}; {PADDING};",
            "#Title-UnifiedUI": f"background-color: {colors['label_background']}; {PADDING}; border-top-right-radius: 0px; border-bottom-right-radius: 0px;",
            "QTextEdit": f"background-color: {colors['info_window_background']}; {PADDING};",
            "QLineEdit": f"background-color: {colors['search_background']}; padding-left: 7px; height: {BUTTON_HEIGHT}px; {BUTTON_PADDING};",
            "#CategoryLineEdit": f"background-color: {colors['search_background']}; {COLOR_PICKER_BUTTON_STYLE}; padding-left: 7px; height: {BUTTON_HEIGHT}px;",
            "QComboBox": f"background-color: {colors['combobox_background']}; border-radius: {self.border_radius}px; {BUTTON_PADDING}; height: {BUTTON_HEIGHT}px; padding-right: 12px;",
            "QComboBox:hover": f"background-color: {self.brightness_adjuster.adjust_brightness_dynamically(colors['combobox_background'], DBH)};",
            "QComboBox::drop-down": f"subcontrol-origin: padding; subcontrol-position: center right; margin-right: 14px; border: none;",
            "QComboBox::down-arrow": f"image: url({arrow_path}); width: 12px; height: 8px;", 
            "QComboBox::down-arrow:on": f"image: url({up_arrow_path});", 
            "QComboBox::down-arrow svg": f"fill: {colors['text_color']}; stroke: {colors['text_color']};",
            "QComboBox QAbstractItemView": f"background-color: {colors['combobox_background']}; border-radius: {self.border_radius / 2}px; margin-top: 5px; padding: 2px;",
            "QPushButton": f"background-color: {colors['button_background']}; {BUTTON_PADDING}; height: {BUTTON_HEIGHT}px;",
            "QPushButton:focus": "outline: none;",
            "QPushButton:hover, QMenu::item:selected": f"background-color: {colors['button_background_hover']};",
            "QPushButton:pressed, QMenu::item:pressed": f"background-color: {colors['button_background_pressed']};",
            "QPushButton:disabled": f"background-color: {self.brightness_adjuster.adjust_brightness(colors['button_background'], 0.75)}; color: {self.brightness_adjuster.adjust_brightness(colors['text_color'], 0.90)};",
            "#ResetButton": f"background-color: {colors['reset_button_background']};",
            "#ResetButtonHalf": f"background-color: {colors['reset_button_background']}; {COLOR_RESET_BUTTON_STYLE};",
            "#ResetButton:hover, #ResetButtonHalf:hover": f"background-color: {colors['reset_button_background_hover']};",
            "#ResetButton:pressed, #ResetButtonHalf:pressed": f"background-color: {colors['reset_button_background_pressed']};",
            "QCheckBox::indicator": f"height: {CHECKBOX_SIZE}px; width: {BUTTON_HEIGHT/1.2}px; border-radius:{self.checkbox_radius}px;",
            "QCheckBox::indicator:unchecked": f"background-color: {colors['checkbox_background_unchecked']};",
            "QCheckBox::indicator:checked": f"background-color: {colors['checkbox_background_checked']};",
            "QRadioButton::indicator": f"height: {CHECKBOX_SIZE}px; width: {CHECKBOX_SIZE}px; border-radius: {CHECKBOX_SIZE/2}px;",
            "QRadioButton::indicator:unchecked": f"background-color: {colors['checkbox_background_unchecked']};",
            "QRadioButton::indicator:checked": f"background-color: {colors['checkbox_background_checked']};",
            "QHeaderView": f"background-color: {colors['table_background']}; border: 0;",
            "QHeaderView::section": f"background-color: {colors['table_gridline_color']}; border-radius: {TABLE_CELL_RADIUS}px; margin: 2px; padding-left: 4px;",
            "QTableCornerButton::section": f"background-color: {colors['button_background']}; border-radius: {TABLE_CELL_RADIUS}px; border-top-left-radius: {(self.border_radius / 2)}px; margin: 2px; padding-left: 4px;",
            "QTableWidget": f"background-color: {colors['table_background']}; border: {max(self.border_size, 2)}px solid {colors['table_border_color']}; {PADDING}; gridline-color: {colors['table_gridline_color']};",
            "QTableWidget::item": f"background-color: transparent; border-radius: {TABLE_CELL_RADIUS}px; margin: 2px",
            "QTableWidget::item:selected": f"background-color: {colors['table_item_selected']};",
            "QTextBrowser": f"{PADDING};",
            "QScrollBar": f"background-color: {colors['bar_background']}; border-radius: {self.bar_radius}px; border: 0;",
            "QScrollBar:vertical": f"width: {self.bar_thickness}px; margin-top: 2px; margin-bottom: 2px;",
            "QScrollBar:horizontal": f"height: {self.bar_thickness}px; margin-left: 2px; margin-right: 2px;",
            "QScrollBar::handle": f"background-color: {colors['bar_handle']}; border-radius: {self.bar_radius}px; border: 0;",
            "QScrollBar::handle:vertical": f"min-height: {self.bar_thickness}px;",
            "QScrollBar::handle:horizontal": f"min-width: {self.bar_thickness}px;",
            "QScrollBar::add-page, QScrollBar::sub-page": "background-color: none;",
            "QScrollBar::add-line, QScrollBar::sub-line": "width: 0px; height: 0px;",
            f"#{DV_SCROLLBAR} QScrollBar:vertical": f"margin-top: {dynamic_scroll_margin}px; margin-bottom: {dynamic_scroll_margin+1}px;",
            "QProgressBar": f"background-color: {colors['bar_background']}; border-radius: 9px; border: 0; text-align: center; height: 18px;",
            "QProgressBar::chunk": f"background-color: {colors['bar_handle']}; border-radius: 9px; border: 0; min-width: 18px;",
            "QMenu": f"background-color: {colors['groupbox_background']}; {PADDING}; border: {max(self.border_size, 2)}px solid {colors['border_color']};",
            "QMenu::item": f"{PADDING} 15px; border-radius: {self.border_radius / 2}px;",
            "QMenu::item:disabled": f"background-color: {self.brightness_adjuster.adjust_brightness(colors['groupbox_background'], 0.75)}; color: {self.brightness_adjuster.adjust_brightness(colors['text_color'], 0.90)};",
            "#ChangeLog": f"background-color: {colors['changelog_background']};",
            "#FlatLeftEdge": f"border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: 0;",
            "#FlatRightEdge": f"border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: 0;",
            "#StatusSuccess": f"background-color: rgba(0, 255, 0, 0.1); color: #00cc00; {PADDING}; border: 1px solid rgba(0, 255, 0, 1);",
            "#StatusError": f"background-color: rgba(255, 0, 0, 0.1); color: #ff3333; {PADDING}; border: 1px solid rgba(255, 0, 0, 1);",
            "#StatusNeutral": f"background-color: rgba(0, 0, 0, 0); {PADDING}; border: 1px solid rgba(0, 0, 0, 0);",
            ".icon": f"fill: {colors['text_color']}; stroke: {colors['text_color']};",
            "#DebugHelperColor": f"border-radius: 60px; background-color: red;",
        }

        return "\n".join(f"{selector} {{ {style} }}" for selector, style in styles.items())
