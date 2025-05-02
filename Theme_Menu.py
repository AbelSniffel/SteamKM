# Theme_Menu.py
from PySide6.QtWidgets import *
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from CustomWidgets import FilledSlider, ModernQLineEdit, SliderValueEdit
from CustomColorPicker import CustomColorPickerDialog
from Themes import Theme, BrightnessAdjuster
from Config import (UI_MARGIN, BUTTON_HEIGHT, ICON_BUTTON_WIDTH, CHECKBOX_SIZE, DEFAULT_RADIUS, DEFAULT_BORDER_SIZE, DEFAULT_CHECKBOX_RADIUS, DEFAULT_BAR_RADIUS, DEFAULT_BAR_THICKNESS, HORIZONTAL_SPACING,
                    COLOR_PICKER_BUTTON_STYLE, COLOR_RESET_BUTTON_STYLE, DBH, DBP, VERTICAL_SPACING, VERTICAL_SPACING_SMALL, TITLE_HEIGHT)

class ColorConfigDialog(QDialog):
    theme_changed = Signal(str)
    merge_edges_changed = Signal(bool)
    swap_input_search_changed = Signal(bool)
    status_message_label = Signal(str, bool)

    SLIDER_KEYS = ["border_radius", "checkbox_radius", "border_size", "bar_thickness", "bar_radius"]

    def __init__(self, parent=None, current_colors=None, theme="dark", border_radius=DEFAULT_RADIUS, border_size=DEFAULT_BORDER_SIZE, 
                 checkbox_radius=DEFAULT_CHECKBOX_RADIUS, bar_radius=DEFAULT_BAR_RADIUS, bar_thickness=DEFAULT_BAR_THICKNESS, merge_edges=False, swap_input_search=False):
        super().__init__(parent)
        self.setWindowTitle("Theme Menu")
        self.setMinimumSize(505, 200)
        self.resize(530, 700)
        self.theme = theme
        self.current_colors = current_colors if current_colors else {}
        self.border_radius = border_radius
        self.border_size = border_size
        self.checkbox_radius = checkbox_radius
        self.bar_radius = bar_radius
        self.bar_thickness = bar_thickness
        self.merge_edges = merge_edges
        self.swap_input_search = swap_input_search
        self.color_pickers = {}
        self.brightness_adjuster = BrightnessAdjuster()
        self.reset_buttons = []
        self._last_update = {}
        self.group_spacers = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*UI_MARGIN)

        # Top controls
        top_controls_group = QGroupBox()
        top_controls_layout = QHBoxLayout(top_controls_group)
        self.search_bar = ModernQLineEdit()
        self.search_bar.setPlaceholderText("Search theme options...")
        self.search_bar.textChanged.connect(self.filter_items)
        top_controls_layout.addWidget(self.search_bar, 1)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light", "Ocean", "Forest", "Fire"])
        self.theme_selector.setCurrentText(self.theme.capitalize())
        self.theme_selector.currentIndexChanged.connect(self.on_theme_changed)
        top_controls_layout.addWidget(self.theme_selector)
        top_controls_layout.setSpacing(HORIZONTAL_SPACING)
        main_layout.addWidget(top_controls_group)
        main_layout.setSpacing(VERTICAL_SPACING)

        # Color and sliders group
        color_and_sliders_group = QGroupBox()
        color_and_sliders_layout = QVBoxLayout(color_and_sliders_group)
        self.scroll_area = QScrollArea(objectName="DynamicVScrollBar")
        self.scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setSpacing(VERTICAL_SPACING_SMALL)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(scroll_widget)
        color_and_sliders_layout.addWidget(self.scroll_area)
        bar = self.scroll_area.verticalScrollBar()
        bar.rangeChanged.connect(self.adjust_margins_for_bar)
        bar.valueChanged.connect(self.adjust_margins_for_bar)
        QTimer.singleShot(10, self.adjust_margins_for_bar)
        main_layout.addWidget(color_and_sliders_group)

        # Groups
        self.groups = [
            ("Main Colors", [
                ("Text Color", "text_color"),
                ("Main Background", "main_background"),
                ("Info Window Background", "info_window_background"),
                ("Title/Label/Games Count Background", "label_background"),
                ("Group Background", "groupbox_background"),
                ("Changelog Background", "changelog_background"),
                ("Border Color", "border_color"),
            ]),
            ("Interactables Colors", [
                ("Search Background", "search_background"),
                ("Button Color", "button_background"),
                ("Reset Color", "reset_button_background"),
                ("Checkbox Checked", "checkbox_background_checked"),
                ("Checkbox Unchecked", "checkbox_background_unchecked"),
                ("Category/Combobox Background", "combobox_background"),
            ]),
            ("Game Table Colors", [
                ("Table Background", "table_background"),
                ("Table Selected Game Color", "table_item_selected"),
                ("Table Gridline & Header Color", "table_gridline_color"),
                ("Table Border Color", "table_border_color"),
            ]),
            ("Bar Colors", [
                ("Scroll/Progress Bar Handle", "bar_handle"),
                ("Scroll/Progress Bar Background", "bar_background"),
            ]),
        ]
        self.form_layouts = {}
        self.group_labels = {}
        self.color_picker_rows = {}

        for title, elements in self.groups:
            group_label = QLabel(title, objectName="Title", alignment=Qt.AlignCenter, fixedHeight=TITLE_HEIGHT)
            self.scroll_layout.addWidget(group_label)
            self.group_labels[title] = group_label
            form_layout = QFormLayout()
            form_layout.setVerticalSpacing(VERTICAL_SPACING_SMALL)
            for label, key in elements:
                self._add_color_picker_row(form_layout, label, key)
            self.scroll_layout.addLayout(form_layout)
            self.form_layouts[title] = form_layout
            spacer = QSpacerItem(0, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.scroll_layout.addSpacerItem(spacer)
            self.group_spacers[title] = spacer

        # Sliders
        sliders_label = QLabel("Size and Radius Sliders", objectName="Title", alignment=Qt.AlignCenter, fixedHeight=TITLE_HEIGHT)
        self.scroll_layout.addWidget(sliders_label)
        self.group_labels["Sliders"] = sliders_label
        sliders = [
            ("Corner Radius", "border_radius", 0, BUTTON_HEIGHT // 2, DEFAULT_RADIUS),
            ("Checkbox Radius", "checkbox_radius", 0, CHECKBOX_SIZE // 2, DEFAULT_CHECKBOX_RADIUS),
            ("Bar Radius", "bar_radius", 0, self.bar_thickness // 2, DEFAULT_BAR_RADIUS),
            ("Bar Thickness", "bar_thickness", 8, 16, DEFAULT_BAR_THICKNESS),
            ("Border Thickness", "border_size", 0, 2, DEFAULT_BORDER_SIZE),
        ]
        for label, key, min_val, max_val, default_val in sliders:
            self._add_slider_row(self.scroll_layout, label, key, min_val, max_val, default_val)
            self.scroll_layout.setSpacing(VERTICAL_SPACING_SMALL)

        # Bottom controls
        bottom_controls_group = QGroupBox()
        bottom_controls_layout = QHBoxLayout(bottom_controls_group)
        ui_options_layout = QHBoxLayout()
        self.merge_edges_checkbox = QCheckBox("Unified Buttons")
        self.merge_edges_checkbox.setChecked(self.merge_edges)
        self.merge_edges_checkbox.stateChanged.connect(self.on_merge_edges_changed)
        ui_options_layout.addWidget(self.merge_edges_checkbox)
        self.swap_input_search_checkbox = QCheckBox("Alternative UI Layout")
        self.swap_input_search_checkbox.setChecked(self.swap_input_search)
        self.swap_input_search_checkbox.stateChanged.connect(self.on_swap_input_search_changed)
        ui_options_layout.addWidget(self.swap_input_search_checkbox)
        bottom_controls_layout.addLayout(ui_options_layout, 0)
        bottom_controls_layout.addStretch(1)
        self.reset_all_button = QPushButton("Reset To Default", objectName="ResetButton")
        self.reset_all_button.clicked.connect(self.reset_all_settings)
        bottom_controls_layout.addWidget(self.reset_all_button)
        main_layout.setSpacing(VERTICAL_SPACING)
        main_layout.addWidget(bottom_controls_group)

    def _add_color_picker_row(self, layout, label, key):
        color_name = self.current_colors.get(key, "")
        button = QPushButton(color_name or "Default", fixedWidth=150)
        button.clicked.connect(lambda _, btn=button, k=key: self.choose_color(btn, k))
        reset_button = QPushButton("X", objectName="ResetButtonHalf", fixedWidth=ICON_BUTTON_WIDTH)
        reset_button.clicked.connect(lambda _, btn=button, k=key: self.reset_element(btn, k))
        self.set_reset_button_style(reset_button, flat_left=True)
        self.reset_buttons.append(reset_button)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addWidget(reset_button)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(1, 1, 1, 1)
        label_widget = QLabel(label)
        row_layout.addWidget(label_widget, 0)
        row_layout.addLayout(button_layout, 1)
        layout.addRow(row_widget)
        self.color_picker_rows[key] = row_widget
        self.color_pickers[key] = button
        if color_name:
            self.set_button_color(button, color_name)
        else:
            self.update_default_button_style(button)

    def _add_slider_row(self, layout, label, key, min_val, max_val, default_val):
        label_widget = QLabel(label)
        slider = FilledSlider(Qt.Horizontal)
        slider.setFixedWidth(265)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(getattr(self, key))
        theme_colors = Theme(self.theme, self.current_colors).colors
        slider.setTrackColor(theme_colors["bar_background"])
        slider.setFillColor(theme_colors["bar_handle"])
        slider.updateFromTheme(self.bar_thickness, self.bar_radius)
        value_edit = SliderValueEdit(str(getattr(self, key)))
        value_edit.setFixedWidth(35)
        value_edit.setAlignment(Qt.AlignCenter)
        value_edit.setObjectName("CategoryLineEdit")
        value_edit.setValidator(QIntValidator(min_val, max_val))
        slider.valueChanged.connect(lambda val: self.slider_value_changed(val, value_edit, key))
        slider.sliderReleased.connect(lambda k=key: self.auto_save_setting(k))
        if key == "bar_radius":
            slider.valueChanged.connect(self.update_all_sliders)
        value_edit.textChanged.connect(lambda text: self.on_value_edit_text_changed(text, value_edit, slider, key, min_val, max_val))
        value_edit.editingFinished.connect(lambda k=key: self.auto_save_setting(k))
        value_edit.installEventFilter(self)
        reset_button = QPushButton("X", objectName="ResetButtonHalf", fixedWidth=ICON_BUTTON_WIDTH)
        reset_button.clicked.connect(lambda _, s=slider, d=default_val, v=value_edit, k=key: 
                                    self.reset_element(s, k, default_value=d, value_edit=v))
        self.set_reset_button_style(reset_button, flat_left=False)
        self.reset_buttons.append(reset_button)
        label_slider_layout = QHBoxLayout()
        label_slider_layout.addWidget(label_widget)
        label_slider_layout.addWidget(slider)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(0)
        controls_layout.addWidget(value_edit)
        controls_layout.addWidget(reset_button)
        slider_layout = QHBoxLayout()
        slider_layout.addLayout(label_slider_layout, 1)
        slider_layout.addLayout(controls_layout)
        layout.addLayout(slider_layout)
        setattr(self, f"{key}_slider", slider)
        setattr(self, f"{key}_value_edit", value_edit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self.adjust_margins_for_bar)
        
    def adjust_margins_for_bar(self):
        bar = self.scroll_area.verticalScrollBar()
        
        # Check if the bar is visible and has a range
        is_visible = bar.isVisible() and bar.maximum() > 0
        right_margin = 8 if is_visible else 2
        self.scroll_layout.setContentsMargins(2, 2, right_margin, 2)
        
        # Force a layout update to apply the margin changes immediately
        self.scroll_area.widget().updateGeometry()
        self.scroll_area.updateGeometry()

    # Rest of the existing methods remain unchanged
    def filter_items(self):
        search_text = self.search_bar.text().lower()
        
        # Track which groups are visible to handle spacers appropriately
        visible_groups = []

        for group_title, elements in self.groups:
            form_layout = self.form_layouts[group_title]
            group_label = self.group_labels[group_title]

            group_visible = False
            visible_rows = 0
            
            # Process all the color picker rows
            for label, key in elements:
                if hasattr(self, 'color_picker_rows') and key in self.color_picker_rows:
                    row_widget = self.color_picker_rows[key]
                    row_visible = search_text in label.lower()
                    
                    # Update visibility and layout based on search results
                    row_widget.setVisible(row_visible)
                    
                    # Adjust row height based on visibility
                    if row_visible:
                        row_widget.setMinimumHeight(BUTTON_HEIGHT + 2)
                        row_widget.setMaximumHeight(BUTTON_HEIGHT + 2)
                        visible_rows += 1
                        group_visible = True
                    else:
                        row_widget.setMinimumHeight(0)
                        row_widget.setMaximumHeight(0)

            # Handle slider sections (keep existing code)
            for row in range(form_layout.rowCount()):
                label_item = form_layout.itemAt(row, QFormLayout.LabelRole)
                field_item = form_layout.itemAt(row, QFormLayout.FieldRole)

                if label_item and field_item:
                    if not hasattr(self, 'color_picker_rows') or not any(key in self.color_picker_rows for _, key in elements):
                        # Only process rows that aren't managed by color_picker_rows
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

            # Update group label visibility
            group_label.setVisible(group_visible)
            
            # Keep track of which groups are visible
            if group_visible:
                visible_groups.append(group_title)

            # Adjust form layout spacing based on visible rows
            if group_visible:
                if visible_rows == 0:
                    form_layout.setVerticalSpacing(0)
                else:
                    form_layout.setVerticalSpacing(VERTICAL_SPACING_SMALL)
            else:
                form_layout.setContentsMargins(0, 0, 0, 0)
                form_layout.setVerticalSpacing(0)
        
        # Handle the sliders section specifically
        sliders_visible = False
        for key in self.SLIDER_KEYS:
            slider_label = getattr(self, f"{key}_slider", None)
            if slider_label and slider_label.isVisible():
                sliders_visible = True
                break
        
        self.group_labels["Sliders"].setVisible(sliders_visible)
        if sliders_visible:
            visible_groups.append("Sliders")
                
        # Update spacing between groups
        for title, spacer in self.group_spacers.items():
            # Show spacer if this group is visible and it's not the last visible group
            show_spacer = title in visible_groups and title != visible_groups[-1]
            height = 15 if show_spacer else 0
            spacer.changeSize(0, height, QSizePolicy.Minimum, QSizePolicy.Fixed)
            
        # Force layout update to apply spacers
        self.scroll_layout.invalidate()
        self.scroll_area.widget().updateGeometry()
        QTimer.singleShot(10, self.adjust_margins_for_bar)

    def on_value_edit_text_changed(self, text, edit_field, slider, key, min_val, max_val):
        """Handle real-time updates as user types in the value edit field"""
        if not text or text == '-':
            return
        
        try:
            value = int(text)
            # For bar_radius, always use the current slider maximum (may have changed)
            if key == "bar_radius":
                max_val = self.bar_radius_slider.maximum()
            # Clamp value to allowed range
            if value > max_val:
                value = max_val
                edit_field.setText(str(max_val))
            elif value < min_val:
                value = min_val
                edit_field.setText(str(min_val))
            slider.setValue(value)
            
            # Special case for bar_thickness
            if key == "bar_thickness":
                self.update_bar_thickness(value)
            else:
                self.update_value(key, value)
        except ValueError:
            pass

    def eventFilter(self, obj, event):
        # Handle focus out events for line edits
        if isinstance(obj, QLineEdit) and event.type() == QEvent.FocusOut:
            for key in self.SLIDER_KEYS:
                if hasattr(self, f"{key}_value_edit") and obj == getattr(self, f"{key}_value_edit"):
                    slider = getattr(self, f"{key}_slider")
                    min_val = slider.minimum()
                    max_val = slider.maximum()
                    self.edit_value_changed(obj, slider, key, min_val, max_val)
                    break
        return super().eventFilter(obj, event)

    def slider_value_changed(self, value, edit_field, key):
        edit_field.setText(str(value))
        self.update_value(key, value)

    def edit_value_changed(self, edit_field, slider, key, min_val, max_val):
        try:
            value = int(edit_field.text())
            # For bar_radius, always use the current slider maximum (may have changed)
            if key == "bar_radius":
                max_val = self.bar_radius_slider.maximum()
            # Clamp value to allowed range
            if value > max_val:
                value = max_val
            elif value < min_val:
                value = min_val
            slider.setValue(value)
            # Update text in case the value was clamped
            edit_field.setText(str(value))
            self.update_value(key, value)
        except ValueError:
            # Revert to current slider value if input is invalid
            edit_field.setText(str(slider.value()))

    def update_value(self, key, value):
        # Only update if value has changed
        if self._last_update.get(key) != value:
            self._last_update[key] = value
            setattr(self, key, value)
            
            # Update the preview
            self.parent().apply_custom_colors(
                self.current_colors,
                self.border_radius,
                self.border_size,
                self.checkbox_radius,
                self.bar_radius,
                self.bar_thickness
            )

    def update_bar_thickness(self, value):
        # Calculate new max radius
        max_radius = value // 2
        self.bar_radius_slider.setMaximum(max_radius)

        if hasattr(self, 'bar_radius_value_edit'):
            self.bar_radius_value_edit.setValidator(QIntValidator(0, max_radius))
        
        # Only adjust the scroll radius if it's higher than the new maximum
        if self.bar_radius > max_radius:
            self.update_value("bar_radius", max_radius)
            if hasattr(self, 'bar_radius_value_edit'):
                self.bar_radius_value_edit.setText(str(max_radius))
        
        # Update the bar dimensions
        self.update_value("bar_thickness", value)
        self.update_all_sliders()

    def update_all_sliders(self):
        """Update colors and dimensions for all FilledSliders based on current theme colors"""
        theme_colors = Theme(self.theme, self.current_colors).colors # Use imported Theme
        handle_color = theme_colors["bar_handle"]
        background_color = theme_colors["bar_background"]
        
        for key in self.SLIDER_KEYS:
            if hasattr(self, f"{key}_slider"):
                slider = getattr(self, f"{key}_slider")
                if isinstance(slider, FilledSlider):
                    slider.setTrackColor(background_color)
                    slider.setFillColor(handle_color)
                    slider.updateFromTheme(self.bar_thickness, self.bar_radius)

    def reset_element(self, element, key, default_value=None, value_edit=None):
        """Unified reset method for both color pickers and sliders"""
        if isinstance(element, QSlider):
            # Handle slider reset
            if key == "bar_radius":
                current_width = self.bar_thickness
                
                # Calculate if the default radius would exceed half the current width
                if default_value > current_width / 2:
                    required_width = default_value * 2
                    
                    self.bar_thickness_slider.setValue(required_width)
                    self.bar_thickness_value_edit.setText(str(required_width))
                    self.update_value("bar_thickness", required_width)
            
            # Set value to default
            element.setValue(default_value)
            if value_edit:
                value_edit.setText(str(default_value))
            
            # Update the actual property value
            self.update_value(key, default_value)
        else:
            # Handle button/color reset
            element.setText("Default")
            self.update_default_button_style(element)
            self.current_colors.pop(key, None)
            
        # Handle special updates based on the key
        self.maybe_update_special(key)
        self.update_preview()
        self.auto_save_setting(key)  # Auto-save on reset

    def maybe_update_special(self, key):
        if key in ["bar_handle", "bar_background"]:
            self.update_all_sliders()
        if key == "reset_button_background":
            self.update_all_reset_buttons()

    def choose_color(self, button, key):
        # Get current color from button text or default theme color
        current_color_hex = button.text()
        default_theme_colors = Theme(self.theme).colors  # Use imported Theme
        default_color_hex = default_theme_colors.get(key, "#ffffff")  # Fallback to white
        
        if not current_color_hex.startswith("#"):
            # If button shows "Default", get the default color for the current theme
            current_color_hex = default_color_hex

        initial_color = QColor(current_color_hex)
        
        # Create a preview callback function to handle real-time updates
        def preview_update_callback(color):
            # Store the original value to restore if cancelled
            if not hasattr(self, '_original_color_values'):
                self._original_color_values = {}
            
            if key not in self._original_color_values:
                self._original_color_values[key] = self.current_colors.get(key, None)
            
            # Apply the preview color
            preview_color_name = color.name()
            self.current_colors[key] = preview_color_name
            
            # Update button appearance for immediate feedback
            button.setText(preview_color_name)
            self.set_button_color(button, preview_color_name)
            
            # Update any special UI elements that depend on this color
            self.maybe_update_special(key)
            
            # Apply the temporary change to the UI
            self.update_preview()

        # Use the custom color picker dialog with preview support
        color = CustomColorPickerDialog.getColorWithPreview(
            initial_color, self, key, preview_callback=preview_update_callback)

        if color and color.isValid():
            color_name = color.name()
            
            # Check if the selected color is the same as the default theme color
            if color_name.lower() == default_color_hex.lower():
                button.setText("Default")
                self.update_default_button_style(button)
                if key in self.current_colors:
                    self.current_colors.pop(key, None)  # Remove from custom colors if it's the default
            else:
                button.setText(color_name)
                self.set_button_color(button, color_name)
                self.current_colors[key] = color_name
                
            self.maybe_update_special(key)
            self.update_preview()
            self.auto_save_setting(key)  # Auto-save on color change
        elif color is None:
            # If dialog was cancelled, restore the original color
            if hasattr(self, '_original_color_values') and key in self._original_color_values:
                original_value = self._original_color_values[key]
                if original_value is None:
                    # If there was no custom color originally
                    if key in self.current_colors:
                        self.current_colors.pop(key, None)
                    button.setText("Default")
                    self.update_default_button_style(button)
                else:
                    # If there was a custom color previously
                    self.current_colors[key] = original_value
                    button.setText(original_value)
                    self.set_button_color(button, original_value)
                
                self.maybe_update_special(key)
                self.update_preview()
                
                # Clean up
                del self._original_color_values[key]

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
        base_color = self.current_colors.get("reset_button_background") or Theme(self.theme).colors["reset_button_background"] # Use imported Theme
        hover_color = self.brightness_adjuster.adjust_brightness_dynamically(base_color, DBH)
        pressed_color = self.brightness_adjuster.adjust_brightness(base_color, DBP)
        border_style = COLOR_RESET_BUTTON_STYLE if flat_left else ""
        
        style = f"""
            #ResetButton, #ResetButtonHalf {{background-color: {base_color}; {border_style};}}
            #ResetButton:hover, #ResetButtonHalf:hover {{background-color: {hover_color};}}
            #ResetButton:pressed, #ResetButtonHalf:pressed {{background-color: {pressed_color}}}
        """
        reset_button.setStyleSheet(style)

    def update_all_reset_buttons(self):
        for button in self.reset_buttons:
            flat_left = "border-top-left-radius: 0px" in button.styleSheet()
            self.set_reset_button_style(button, flat_left)

    def update_default_button_style(self, button):
        text_color = "black" if self.theme == "light" else "white"
        button.setStyleSheet(f"color: {text_color}; {COLOR_PICKER_BUTTON_STYLE};")

    def contrast_color(self, hex_color):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#FFFFFF"

    def apply_colors(self):
        self.accept()
        
    def closeEvent(self, event):
        self.status_message_label.emit("Saved Theme Settings", True)
        self.auto_save_setting()  # Ensure everything is saved on close
        self.accept()
        super().closeEvent(event)

    def update_preview(self):
        self.update_all_sliders()
        
        # Directly update preview
        self.parent().apply_custom_colors(
            self.current_colors,
            self.border_radius,
            self.border_size,
            self.checkbox_radius,
            self.bar_radius,
            self.bar_thickness
        )

    def on_merge_edges_changed(self, state):
        self.merge_edges = bool(state)
        self.merge_edges_changed.emit(self.merge_edges)

    def update_all_button_styles(self):
        """Update all color picker button styles to match the current theme"""
        for key, button in self.color_pickers.items():
            if button.text() == "Default" or not button.text().startswith("#"):
                self.update_default_button_style(button)
            else:
                # For buttons with custom colors, ensure text color contrast is correct
                self.set_button_color(button, button.text())

    def on_theme_changed(self):
        """Handle theme selection change"""
        selected_theme = self.theme_selector.currentText().lower()
        if (selected_theme != self.theme):
            # Store current slider values to prevent flickering with old values
            current_values = {}
            for key in self.SLIDER_KEYS:
                current_values[key] = getattr(self, key)
            
            self.theme = selected_theme
            # Update button styles to match the new theme
            self.update_all_button_styles()
            self.update_all_reset_buttons()
            
            # Update slider colors based on new theme while preserving values
            theme_colors = Theme(self.theme, self.current_colors).colors # Use imported Theme
            for key in self.SLIDER_KEYS:
                if hasattr(self, f"{key}_slider"):
                    slider = getattr(self, f"{key}_slider")
                    if isinstance(slider, FilledSlider):
                        # Update appearance but keep value
                        slider.setTrackColor(theme_colors["bar_background"])
                        slider.setFillColor(theme_colors["bar_handle"])
                        slider.updateFromTheme(self.bar_thickness, self.bar_radius)
                        
                        # Ensure the slider maintains its current value
                        slider.blockSignals(True)
                        slider.setValue(current_values[key])
                        slider.blockSignals(False)
            
            # Emit the signal to inform parent about theme change
            self.theme_changed.emit(selected_theme)
            
            # Update the preview with the preserved values
            self.parent().apply_custom_colors(
                self.current_colors,
                current_values["border_radius"],
                current_values["border_size"],
                current_values["checkbox_radius"],
                current_values["bar_radius"],
                current_values["bar_thickness"]
            )

    def reset_all_settings(self):
        confirm = QMessageBox.question(self, "Reset All Settings",
                                       "Are you sure you want to reset all theme settings to defaults?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            # Clear all custom colors
            self.current_colors.clear()
            
            # Reset all color pickers
            for key, button in self.color_pickers.items():
                button.setText("Default")
                self.update_default_button_style(button)
            
            # Update reset button styles
            self.update_all_reset_buttons()
                
            # Reset all sliders with their default values
            slider_defaults = {
                "border_radius": DEFAULT_RADIUS,
                "border_size": DEFAULT_BORDER_SIZE,
                "checkbox_radius": DEFAULT_CHECKBOX_RADIUS,
                "bar_thickness": DEFAULT_BAR_THICKNESS,
                "bar_radius": DEFAULT_BAR_RADIUS
            }
            
            # Apply each default value
            for key, default_val in slider_defaults.items():
                slider = getattr(self, f"{key}_slider")
                value_edit = getattr(self, f"{key}_value_edit")
                slider.setValue(default_val)
                value_edit.setText(str(default_val))
                setattr(self, key, default_val)
            
            # Update the preview with all default values
            self.update_preview()

    def on_swap_input_search_changed(self, state):
        self.swap_input_search = bool(state)
        self.swap_input_search_changed.emit(self.swap_input_search)

    def auto_save_setting(self, key=None):
        parent = self.parent()
        if parent and hasattr(parent, "config_manager"):
            config_manager = parent.config_manager
            config_manager.update({
                "custom_colors": self.current_colors,
                "border_radius": self.border_radius,
                "border_size": self.border_size,
                "checkbox_radius": self.checkbox_radius,
                "bar_thickness": self.bar_thickness,
                "bar_radius": self.bar_radius,
                "merge_edges": self.merge_edges,
                "swap_input_search": self.swap_input_search,
                "theme": self.theme,
                "using_custom_colors": True
            })