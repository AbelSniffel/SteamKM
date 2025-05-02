# CustomColorPicker.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QDialogButtonBox, QWidget, QGroupBox, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QColor, QIntValidator, QPainter, QBrush
from PySide6.QtCore import Qt, Signal
from CustomWidgets import FilledSlider
from Themes import Theme
import re

class ColorPreviewWidget(QWidget):
    """A simple widget to display a color preview circle."""
    def __init__(self, color=QColor("white"), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(26, 26) # Small fixed size circle

    def set_color(self, color):
        if self._color != color:
            self._color = color
            self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.NoPen) # No border for the circle
        # Draw circle centered in the widget
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 1 # Leave 1px margin
        painter.drawEllipse(center, radius, radius)

class CustomColorPickerDialog(QDialog):
    """A custom dialog for picking colors using RGB/HSV sliders and hex input."""
    colorSelected = Signal(QColor)
    colorPreview = Signal(QColor)  # Signal for real-time preview updates

    def __init__(self, initial_color=QColor("white"), parent=None, theme_colors=None, bar_thickness=12, bar_radius=6, color_key=None, theme_name=None):
        super().__init__(parent)
        self.setWindowTitle("Color Customization")
        self._current_color = initial_color
        self._initial_color = initial_color # Store initial color separately
        self._theme_colors = theme_colors if theme_colors else Theme().colors # Use imported Theme
        self._bar_thickness = bar_thickness
        self._bar_radius = bar_radius
        self._color_key = color_key  # Store the color key being edited
        self._theme_name = theme_name  # Store the current theme name
        self._updating_internally = False # Flag to prevent signal loops

        # Main layout
        layout = QVBoxLayout(self)

        # --- GroupBox 1: Color Controls (sliders only) ---
        controls_groupbox = QGroupBox()
        controls_groupbox_layout = QVBoxLayout(controls_groupbox)

        self.sliders = {}
        self.edits = {}

        # --- Helper for consistent slider row creation ---
        def create_slider_row(label_text, slider_range, gradient_type, validator_range, key, min_width=200):
            h_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(75)
            slider = FilledSlider(Qt.Horizontal)
            slider.setRange(*slider_range)
            slider.setGradientType(gradient_type)
            slider.setShowCursorInsteadOfFill(True)
            slider.setCursorColor(QColor("white"))
            slider.updateFromTheme(self._bar_thickness, self._bar_radius)
            slider.setMinimumWidth(min_width)  # Use minimum width, allow expansion
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            edit = QLineEdit()
            edit.setFixedWidth(55)
            edit.setAlignment(Qt.AlignCenter)
            edit.setValidator(QIntValidator(*validator_range))
            h_layout.addWidget(label)
            h_layout.addWidget(slider)
            h_layout.addSpacing(8)
            h_layout.addWidget(edit)
            return h_layout, slider, edit
        # -------------------------------------------------

        slider_layout = QVBoxLayout()
        slider_min_width = 200

        # RGB and Hue sliders
        for component in ("Red", "Green", "Blue"):
            h_layout, slider, edit = create_slider_row(component, (0, 255), component.lower(), (0, 255), component, min_width=slider_min_width)
            slider_layout.addLayout(h_layout)
            self.sliders[component] = slider
            self.edits[component] = edit
            slider.valueChanged.connect(self._update_from_sliders)
            edit.textChanged.connect(self._update_from_edits)

        # Hue slider
        h_layout, slider, edit = create_slider_row("Hue", (0, 359), "hue", (0, 359), "Hue", min_width=slider_min_width)
        slider_layout.addLayout(h_layout)
        self.sliders["Hue"] = slider
        self.edits["Hue"] = edit
        slider.valueChanged.connect(self._update_from_sliders)
        edit.textChanged.connect(self._update_from_edits)

        # --- Saturation slider ---
        h_layout, slider, edit = create_slider_row("Saturation", (0, 255), "saturation", (0, 255), "Saturation", min_width=slider_min_width)
        slider_layout.addLayout(h_layout)
        self.sliders["Saturation"] = slider
        self.edits["Saturation"] = edit
        slider.valueChanged.connect(self._update_from_sliders)
        edit.textChanged.connect(self._update_from_edits)
        # Set initial saturation gradient
        self._update_saturation_gradient(self._current_color)
        # ------------------------

        controls_groupbox_layout.addLayout(slider_layout)

        # Brightness slider
        brightness_layout, brightness_slider, brightness_edit = create_slider_row("Brightness", (0, 255), "value", (0, 255), "Brightness", min_width=slider_min_width)
        self.brightness_slider = brightness_slider
        self.brightness_edit = brightness_edit
        controls_groupbox_layout.addLayout(brightness_layout)
        self.brightness_slider.valueChanged.connect(self._update_from_brightness_slider)
        self.brightness_edit.textChanged.connect(self._update_from_brightness_edit)

        # Set initial brightness gradient
        self._update_brightness_gradient(self._current_color)

        layout.addWidget(controls_groupbox)
        # -------------------------------------------------

        # --- GroupBox 2: Hex & Preview ---
        hex_groupbox = QGroupBox()
        hex_groupbox_layout = QVBoxLayout(hex_groupbox)

        hex_preview_layout = QHBoxLayout()
        hex_preview_layout.addWidget(QLabel("Hex/Color Name:"))
        self.hex_edit = QLineEdit(alignment=Qt.AlignCenter)
        self.hex_edit.editingFinished.connect(self._update_from_hex)
        # Add textChanged signal to update in real-time as user types
        self.hex_edit.textChanged.connect(self._update_from_hex_text_changed)
        hex_preview_layout.addWidget(self.hex_edit)

        self.initial_preview = ColorPreviewWidget(self._initial_color)
        self.current_preview = ColorPreviewWidget(self._current_color)
        hex_preview_layout.addStretch(1)
        hex_preview_layout.addWidget(QLabel("Initial:"))
        hex_preview_layout.addWidget(self.initial_preview)
        hex_preview_layout.addWidget(QLabel("New:"))
        hex_preview_layout.addWidget(self.current_preview)

        hex_groupbox_layout.addLayout(hex_preview_layout)
        layout.addWidget(hex_groupbox)
        # ---------------------------------

        # --- Add vertical stretch between hex and actions ---
        controls_hex_stretch = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(controls_hex_stretch)
        # ---------------------------------------------------

        # --- GroupBox 3: Actions (buttons) ---
        actions_groupbox = QGroupBox()
        actions_groupbox_layout = QHBoxLayout(actions_groupbox)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        if color_key and theme_name:
            self.theme_default_button = QPushButton("Default Color")
            self.theme_default_button.clicked.connect(self._reset_to_theme_default)
            self.button_box.addButton(self.theme_default_button, QDialogButtonBox.ResetRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        actions_groupbox_layout.addWidget(self.button_box)
        layout.addWidget(actions_groupbox)
        # --------------------------------------

        # Initialize values
        self._update_controls(self._current_color)
        self.setMinimumWidth(350) # Set a reasonable minimum width

    def _update_color(self, color, sender_type=None, sender_key=None):
        """Updates the current color and controls, avoiding signal loops."""
        if self._updating_internally:
            return
        
        if color.isValid() and color != self._current_color:
            self._updating_internally = True # Prevent recursive updates
            try:
                self._current_color = color
                # Update the 'new' color preview
                self.current_preview.set_color(color)
                self._update_controls(color, sender_type, sender_key)
                # Update brightness slider gradient when color changes
                self._update_brightness_gradient(color)
                # Update saturation slider gradient when color changes
                self._update_saturation_gradient(color)
                
                # Emit the preview signal immediately for instant feedback
                self.colorPreview.emit(self._current_color)
            finally:
                self._updating_internally = False

    def _update_controls(self, color, sender_type=None, sender_key=None):
        """Updates all control elements based on the color."""
        # Update RGB Sliders and Edits
        for component in ("Red", "Green", "Blue"):
            value = getattr(color, component.lower())()
            slider = self.sliders[component]
            edit = self.edits[component]
            
            is_sender_slider = (sender_type == "slider" and sender_key == component)
            is_sender_edit = (sender_type == "edit" and sender_key == component)

            if not is_sender_slider:
                slider.blockSignals(True)
                slider.setValue(value)
                slider.blockSignals(False)
            if not is_sender_edit:
                edit.blockSignals(True)
                edit.setText(str(value))
                edit.blockSignals(False)
            # No need to update fill color for cursor sliders

        # Update Hue Slider and Edit
        hue_slider = self.sliders["Hue"]
        hue_edit = self.edits["Hue"]
        hue_value = color.hue() # Returns -1 for grayscale
        
        is_sender_hue_slider = (sender_type == "slider" and sender_key == "Hue")
        is_sender_hue_edit = (sender_type == "edit" and sender_key == "Hue")

        # Always keep hue controls enabled, even for grayscale colors
        display_hue = hue_value if hue_value != -1 else 0 

        if not is_sender_hue_slider:
            hue_slider.blockSignals(True)
            hue_slider.setValue(display_hue)
            hue_slider.blockSignals(False)
        if not is_sender_hue_edit:
            hue_edit.blockSignals(True)
            hue_edit.setText(str(display_hue))
            hue_edit.blockSignals(False)
        # No need to update fill color for cursor sliders

        # --- Update Saturation Slider and Edit ---
        sat_slider = self.sliders["Saturation"]
        sat_edit = self.edits["Saturation"]
        sat_value = color.saturation()
        is_sender_sat_slider = (sender_type == "slider" and sender_key == "Saturation")
        is_sender_sat_edit = (sender_type == "edit" and sender_key == "Saturation")
        if not is_sender_sat_slider:
            sat_slider.blockSignals(True)
            sat_slider.setValue(sat_value)
            sat_slider.blockSignals(False)
        if not is_sender_sat_edit:
            sat_edit.blockSignals(True)
            sat_edit.setText(str(sat_value))
            sat_edit.blockSignals(False)
        # Update saturation gradient to match current hue/value
        self._update_saturation_gradient(color)
        # -----------------------------------------

        # Update Brightness (Value) Slider and Edit
        value_slider = self.brightness_slider
        value_edit = self.brightness_edit
        value = color.value()
        is_sender_value_slider = (sender_type == "slider" and sender_key == "Brightness")
        is_sender_value_edit = (sender_type == "edit" and sender_key == "Brightness")
        if not is_sender_value_slider:
            value_slider.blockSignals(True)
            value_slider.setValue(value)
            value_slider.blockSignals(False)
        if not is_sender_value_edit:
            value_edit.blockSignals(True)
            value_edit.setText(str(value))
            value_edit.blockSignals(False)
        # Update brightness gradient to match current color
        self._update_brightness_gradient(color)

        # Update Hex Edit
        is_sender_hex = (sender_type == "hex")
        if not is_sender_hex:
            self.hex_edit.blockSignals(True)
            self.hex_edit.setText(color.name())
            self.hex_edit.blockSignals(False)

    def _update_from_sliders(self):
        """Handles updates when a slider value changes."""
        if self._updating_internally: return

        sender = self.sender()
        new_color = None

        if sender == self.sliders["Hue"]:
            hue = self.sliders["Hue"].value()
            # Get Saturation and Value from the current color
            sat = self._current_color.saturation()
            val = self._current_color.value()
            alpha = self._current_color.alpha()
            
            # If the color was grayscale (saturation = 0), apply a minimum saturation
            # when the user adjusts the hue to make the hue change visible
            if sat == 0:
                sat = 20  # Apply a minimum saturation of 20 (out of 255)
            
            # Create new color from HSV
            new_color = QColor.fromHsv(hue, sat, val, alpha)
            sender_key = "Hue"
        elif sender == self.sliders["Saturation"]:
            # Handle saturation slider
            hue = self.sliders["Hue"].value()
            sat = self.sliders["Saturation"].value()
            val = self._current_color.value()
            alpha = self._current_color.alpha()
            # If the color was grayscale (hue = -1), clamp hue to 0
            if hue == -1:
                hue = 0
            new_color = QColor.fromHsv(hue, sat, val, alpha)
            sender_key = "Saturation"
        elif sender == self.brightness_slider:
            # Handled by _update_from_brightness_slider
            return
        else: # RGB slider changed
            r = self.sliders["Red"].value()
            g = self.sliders["Green"].value()
            b = self.sliders["Blue"].value()
            alpha = self._current_color.alpha()
            new_color = QColor(r, g, b, alpha)
            # Determine which RGB slider sent the signal
            sender_key = next((key for key, slider in self.sliders.items() if slider == sender), None)

        if new_color and new_color.isValid():
            self._update_color(new_color, sender_type="slider", sender_key=sender_key)

    def _update_from_brightness_slider(self):
        """Handles updates when the brightness slider value changes."""
        if self._updating_internally: return
        value = self.brightness_slider.value()
        # Get current HSV
        color = self._current_color
        hue = color.hue()
        sat = color.saturation()
        alpha = color.alpha()
        # Clamp hue for grayscale
        if hue == -1:
            hue = 0
        new_color = QColor.fromHsv(hue, sat, value, alpha)
        self._update_color(new_color, sender_type="slider", sender_key="Brightness")

    def _update_from_brightness_edit(self):
        """Handles updates when the brightness edit field changes."""
        if self._updating_internally: return
        text = self.brightness_edit.text()
        if not text:
            return
        try:
            value = int(text)
            value = max(0, min(value, 255))
            color = self._current_color
            hue = color.hue()
            sat = color.saturation()
            alpha = color.alpha()
            if hue == -1:
                hue = 0
            new_color = QColor.fromHsv(hue, sat, value, alpha)
            self._update_color(new_color, sender_type="edit", sender_key="Brightness")
        except ValueError:
            pass

    def _update_from_edits(self):
        """Handles updates when an RGB or Hue edit field changes."""
        if self._updating_internally: return

        sender = self.sender()
        new_color = None
        sender_key = None

        try:
            if sender == self.edits["Hue"]:
                hue_text = self.edits["Hue"].text()
                if not hue_text: return # Ignore empty input temporarily
                hue = int(hue_text)
                hue = max(0, min(hue, 359)) # Clamp
                sat = self._current_color.saturation()
                val = self._current_color.value()
                alpha = self._current_color.alpha()
                new_color = QColor.fromHsv(hue, sat, val, alpha)
                sender_key = "Hue"
            elif sender == self.edits["Saturation"]:
                sat_text = self.edits["Saturation"].text()
                if not sat_text: return
                sat = int(sat_text)
                sat = max(0, min(sat, 255))
                hue = self.sliders["Hue"].value()
                val = self._current_color.value()
                alpha = self._current_color.alpha()
                if hue == -1:
                    hue = 0
                new_color = QColor.fromHsv(hue, sat, val, alpha)
                sender_key = "Saturation"
            elif sender == self.brightness_edit:
                # Handled by _update_from_brightness_edit
                return
            else: # RGB edit changed
                r = int(self.edits["Red"].text() or 0)
                g = int(self.edits["Green"].text() or 0)
                b = int(self.edits["Blue"].text() or 0)
                alpha = self._current_color.alpha()
                # Clamp values
                r = max(0, min(r, 255))
                g = max(0, min(g, 255))
                b = max(0, min(b, 255))
                new_color = QColor(r, g, b, alpha)
                sender_key = next((key for key, edit in self.edits.items() if edit == sender), None)

            if new_color and new_color.isValid():
                 self._update_color(new_color, sender_type="edit", sender_key=sender_key)

        except ValueError:
            pass # Ignore invalid input temporarily

    def _update_from_hex(self):
        """Handles updates when the hex edit field changes."""
        if self._updating_internally: return

        hex_code = self.hex_edit.text()
        hex_pattern = re.compile(r'^#?[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$')
        # If it matches hex with or without '#', ensure it starts with '#'
        if hex_pattern.match(hex_code):
            if not hex_code.startswith('#'):
                hex_code = '#' + hex_code
            new_color = QColor(hex_code)
        else:
            new_color = QColor(hex_code)
        if new_color.isValid():
            # If user entered a color name, convert to hex in the field and update color
            if not hex_code.startswith('#'):
                self.hex_edit.blockSignals(True)
                self.hex_edit.setText(new_color.name())
                self.hex_edit.blockSignals(False)
            self._update_color(new_color, sender_type="hex")
        else:
            # Revert to last valid color if hex is invalid
            self.hex_edit.blockSignals(True)
            self.hex_edit.setText(self._current_color.name())
            self.hex_edit.blockSignals(False)

    def _update_from_hex_text_changed(self):
        """Handles real-time updates as the user types in the hex field."""
        if self._updating_internally: return

        hex_code = self.hex_edit.text()
        hex_pattern = re.compile(r'^#?[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$')
        # If it matches hex with or without '#', ensure it starts with '#'
        if hex_pattern.match(hex_code):
            if not hex_code.startswith('#'):
                hex_code = '#' + hex_code
            if len(hex_code) == 7 or len(hex_code) == 9:
                new_color = QColor(hex_code)
                if new_color.isValid():
                    self._update_color(new_color, sender_type="hex")
        # If not a hex, but a valid color name, convert to hex and update in real time
        elif len(hex_code) > 0 and not hex_code.startswith('#'):
            new_color = QColor(hex_code)
            if new_color.isValid():
                self._updating_internally = True
                try:
                    self.hex_edit.setText(new_color.name())
                finally:
                    self._updating_internally = False
                self._update_color(new_color, sender_type="hex")

    def _reset_to_theme_default(self):
        """Reset color to the default color for this key in the current theme"""
        if self._color_key and self._theme_name:
            # Get the default color for this key from the theme
            theme = Theme(self._theme_name)
            if self._color_key in theme.colors:
                theme_default_color = QColor(theme.colors[self._color_key])
                if theme_default_color.isValid():
                    # Use _update_color to ensure all controls are updated correctly
                    self._update_color(theme_default_color) 

    def _update_brightness_gradient(self, color):
        """Update the brightness slider's gradient from black to the current color at max brightness."""
        if not hasattr(self, "brightness_slider"):
            return
        # Get the current color's HSV (use hue and saturation, value=255)
        hue = color.hue()
        sat = color.saturation()
        alpha = color.alpha()
        if hue == -1:
            # For grayscale, just use the color at value=255
            max_color = QColor(255, 255, 255, alpha)
        else:
            max_color = QColor.fromHsv(hue, sat, 255, alpha)
        # Set the gradient stops: black at 0, max_color at 255
        self.brightness_slider.setCustomGradient([
            (0.0, QColor(0, 0, 0, alpha)),
            (1.0, max_color)
        ])

    def _update_saturation_gradient(self, color):
        """Update the saturation slider's gradient from gray (no saturation) to full color (max saturation)."""
        if not hasattr(self, "sliders") or "Saturation" not in self.sliders:
            return
        slider = self.sliders["Saturation"]
        hue = color.hue()
        val = color.value()
        alpha = color.alpha()
        # For grayscale, just use value for both ends
        if hue == -1:
            left_color = QColor(val, val, val, alpha)
            right_color = QColor(val, val, val, alpha)
        else:
            left_color = QColor.fromHsv(hue, 0, val, alpha)      # No saturation (gray)
            right_color = QColor.fromHsv(hue, 255, val, alpha)   # Full saturation
        slider.setCustomGradient([
            (0.0, left_color),
            (1.0, right_color)
        ])

    def selected_color(self):
        """Returns the currently selected color."""
        return self._current_color

    @staticmethod
    def getColor(initial_color=QColor("white"), parent=None, color_key=None):
        """Static method to show the dialog and get the color."""
        # Retrieve theme settings from parent (ColorConfigDialog)
        theme_colors = {}
        bar_thickness = 12 # Default
        bar_radius = 6 # Default
        theme_name = None
        
        if parent and hasattr(parent, 'current_colors') and hasattr(parent, 'theme'):
            theme_name = parent.theme
            # Get combined theme colors (defaults + custom)
            base_theme = Theme(parent.theme) # Use imported Theme
            theme_colors = base_theme.colors.copy()
            if hasattr(parent, 'using_custom_colors') and parent.using_custom_colors and hasattr(parent, 'custom_colors'):
                theme_colors.update(parent.custom_colors)
            # Get bar dimensions
            if hasattr(parent, 'bar_thickness'):
                bar_thickness = parent.bar_thickness
            if hasattr(parent, 'bar_radius'):
                bar_radius = parent.bar_radius

        dialog = CustomColorPickerDialog(initial_color, parent, theme_colors, 
                                        bar_thickness, bar_radius,
                                        color_key, theme_name)
        # Apply parent's stylesheet to the dialog for consistent theming
        if parent:
            dialog.setStyleSheet(parent.styleSheet())
            
        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.selected_color()
        return None # Return None if cancelled

    # Add a static method that includes preview signal handling
    @staticmethod
    def getColorWithPreview(initial_color=QColor("white"), parent=None, color_key=None, preview_callback=None):
        """Show the dialog and get the color with real-time preview support."""
        # Retrieve theme settings from parent (ColorConfigDialog)
        theme_colors = {}
        bar_thickness = 12 # Default
        bar_radius = 6 # Default
        theme_name = None
        
        if parent and hasattr(parent, 'current_colors') and hasattr(parent, 'theme'):
            theme_name = parent.theme
            # Get combined theme colors (defaults + custom)
            base_theme = Theme(parent.theme) # Use imported Theme
            theme_colors = base_theme.colors.copy()
            if hasattr(parent, 'using_custom_colors') and parent.using_custom_colors and hasattr(parent, 'custom_colors'):
                theme_colors.update(parent.custom_colors)
            # Get bar dimensions
            if hasattr(parent, 'bar_thickness'):
                bar_thickness = parent.bar_thickness
            if hasattr(parent, 'bar_radius'):
                bar_radius = parent.bar_radius

        dialog = CustomColorPickerDialog(initial_color, parent, theme_colors, 
                                        bar_thickness, bar_radius,
                                        color_key, theme_name)
        # Apply parent's stylesheet to the dialog for consistent theming
        if parent:
            dialog.setStyleSheet(parent.styleSheet())
        
        # Connect the preview signal if a callback was provided
        if preview_callback:
            dialog.colorPreview.connect(preview_callback)
            
        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.selected_color()
        return None # Return None if cancelled
