from PySide6.QtWidgets import QSlider, QLineEdit, QTextEdit, QComboBox, QLabel, QWidget, QHBoxLayout, QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox, QSizePolicy, QStyleOptionSlider, QStyle, QCheckBox
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QLinearGradient, QPen, QFontMetrics
from PySide6.QtCore import Qt, QRect, QSize, QPoint, QRectF
from Config import TABLE_CELL_RADIUS, DEFAULT_DIALOG_WIDTH, DEFAULT_DIALOG_HEIGHT, DEFAULT_TEXT_BROWSER_MIN_HEIGHT, BUTTON_HEIGHT, DEFAULT_RADIUS

class PlainTextInput(QTextEdit): # Removes Rich Text Support
    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())

class ModernQLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setClearButtonEnabled(True)

# Custom QLineEdit that prevents Enter key propagation
class SliderValueEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            
    def keyPressEvent(self, event):
        # Prevent Enter key from propagating to parent widgets
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            event.accept()  # Accept the event to prevent propagation
            self.clearFocus()  # Clear focus to trigger the focus out event
        else:
            super().keyPressEvent(event)

class ScrollRejectionSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)
    def wheelEvent(self, event):
        event.ignore()

class ScrollRejectionComboBox(QComboBox):
    """ComboBox that ignores mouse wheel events to prevent accidental changes."""
    def wheelEvent(self, event):
        event.ignore()

class FilledSlider(QSlider):
    """A custom slider that fills the track or shows a cursor, with optional gradient backgrounds."""
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._track_color = QColor("#3d6452") # Default track color
        self._fill_color = QColor("#3be69f")  # Default fill color
        self._track_height = BUTTON_HEIGHT # Default track height
        self._track_radius = DEFAULT_RADIUS  # Default track radius
        # self._is_hue_slider = False # Replaced by _gradient_type
        self._gradient_type = None # Can be None, "hue", "red", "green", "blue"
        self._show_cursor_instead_of_fill = False # Flag to show cursor instead of fill
        self._cursor_color = QColor("white") # Default cursor color
        self._custom_gradient_stops = None  # Add this line

    def setTrackRadius(self, radius):
        if self._track_radius != radius:
            self._track_radius = radius
            self.update()
        
    def setTrackHeight(self, height):
        if self._track_height != height:
            self._track_height = height
            self.update()
        
    def setTrackColor(self, color):
        if self._track_color != color:
            self._track_color = color
            self.update()
        
    def setFillColor(self, color):
        if self._fill_color != color:
            self._fill_color = color
            self.update()
    
    # Update dimensions from theme settings
    def updateFromTheme(self, track_height, track_radius):
        """Updates the slider's track height and radius and triggers visual updates."""
        new_height = max(4, track_height) # Ensure minimum height
        # Clamp radius based on the new height
        new_radius = max(0, min(track_radius, new_height // 2)) 
        
        changed = False
        # Use internal attributes for comparison and assignment
        if self._track_height != new_height:
            self._track_height = new_height
            # Adjust minimum height of the widget itself to accommodate track + padding
            self.setMinimumHeight(new_height + 4) 
            changed = True

        if self._track_radius != new_radius:
            self._track_radius = new_radius
            changed = True

        if changed:
            # Inform layout system about potential size change
            self.updateGeometry() 
            # Trigger repaint with new dimensions
            self.update() 

    def setGradientType(self, gradient_type):
        """Set the type of gradient for the background (None, 'hue', 'red', 'green', 'blue')."""
        if self._gradient_type != gradient_type:
            self._gradient_type = gradient_type
            self.update() # Trigger repaint

    def setShowCursorInsteadOfFill(self, show_cursor):
        """Set whether to show a cursor marker instead of filling the track."""
        if self._show_cursor_instead_of_fill != show_cursor:
            self._show_cursor_instead_of_fill = show_cursor
            self.update() # Trigger repaint

    def setCursorColor(self, color):
        """Set the color of the cursor marker."""
        if self._cursor_color != color:
            self._cursor_color = color
            if self._show_cursor_instead_of_fill: # Only repaint if cursor is visible
                self.update()

    def setCustomGradient(self, stops):
        """Set a custom gradient for the slider track. Stops: list of (pos, QColor)."""
        self._custom_gradient_stops = stops
        self.update()

    def clearCustomGradient(self):
        """Clear any custom gradient and revert to default gradient/track color."""
        self._custom_gradient_stops = None
        self.update()

    def sizeHint(self):
        return QSize(200, max(self._track_height * 2, 16))
    
    def minimumSizeHint(self):
        return QSize(50, max(self._track_height * 2, 16))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        # Calculate track geometry using internal attributes
        groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        center_y = groove_rect.center().y()
        track_top = center_y - self._track_height // 2 # Use _track_height
        track_rect = QRect(groove_rect.left(), track_top, groove_rect.width(), self._track_height) # Use _track_height
        track_width = track_rect.width()

        # --- Draw the track background ---
        painter.setPen(Qt.NoPen)
        gradient = None
        if self._custom_gradient_stops:
            # Use custom gradient if set
            gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            for pos, color in self._custom_gradient_stops:
                gradient.setColorAt(pos, color)
        elif self._gradient_type == "hue":
            gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            gradient.setColorAt(0.0, QColor.fromHsv(0, 255, 255))   # Red
            gradient.setColorAt(1/6, QColor.fromHsv(60, 255, 255))  # Yellow
            gradient.setColorAt(2/6, QColor.fromHsv(120, 255, 255)) # Green
            gradient.setColorAt(3/6, QColor.fromHsv(180, 255, 255)) # Cyan
            gradient.setColorAt(4/6, QColor.fromHsv(240, 255, 255)) # Blue
            gradient.setColorAt(5/6, QColor.fromHsv(300, 255, 255)) # Magenta
            gradient.setColorAt(1.0, QColor.fromHsv(359, 255, 255)) # Red (close to 360)
        elif self._gradient_type == "red":
            gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            gradient.setColorAt(0.0, QColor(0, 0, 0))    # Black
            gradient.setColorAt(1.0, QColor(255, 0, 0))  # Red
        elif self._gradient_type == "green":
            gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            gradient.setColorAt(0.0, QColor(0, 0, 0))    # Black
            gradient.setColorAt(1.0, QColor(0, 255, 0))  # Green
        elif self._gradient_type == "blue":
            gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            gradient.setColorAt(0.0, QColor(0, 0, 0))    # Black
            gradient.setColorAt(1.0, QColor(0, 0, 255))  # Blue

        if gradient:
            painter.setBrush(gradient)
        else:
            # Draw Solid Track Background if no gradient type
            painter.setBrush(QBrush(self._track_color))
        
        painter.drawRoundedRect(track_rect, self._track_radius, self._track_radius) # Use _track_radius
        # --- End track background drawing ---


        # Calculate handle position using QStyle for accuracy
        handle_pos_x = self.style().sliderPositionFromValue(self.minimum(), self.maximum(), self.value(), track_width) + track_rect.left()

        if self._show_cursor_instead_of_fill:
            # --- Draw Dynamic Cursor Ring (Edge-Shrinking Logic) ---
            painter.setBrush(Qt.NoBrush) # Transparent center
            pen_width = 2
            painter.setPen(QPen(self._cursor_color, pen_width)) # Use thicker pen (2px)
            
            max_radius = self._track_height // 2 # Maximum radius is half the track height
            min_alloweDEFAULT_RADIUS = 3 # Smallest pixel radius allowed
            
            # Define the drawable area bounds (considering track radius for curves)
            # Add/subtract half pen width for accurate edge check
            half_pen = pen_width / 2.0
            drawable_left_edge = track_rect.left() + self._track_radius + half_pen
            drawable_right_edge = track_rect.right() - self._track_radius - half_pen
            
            # Calculate available space from handle center to the drawable edges
            space_to_left = handle_pos_x - drawable_left_edge
            space_to_right = drawable_right_edge - handle_pos_x
            
            # Radius is limited by the smaller available space or the max radius
            available_radius = min(space_to_left, space_to_right)
            dynamic_radius = max(min_alloweDEFAULT_RADIUS, min(max_radius, available_radius))

            # Clamp the center position to ensure the circle fits within the overall track rect
            # Use the calculated dynamic_radius for clamping
            clamped_min_x = track_rect.left() + dynamic_radius + half_pen
            clamped_max_x = track_rect.right() - dynamic_radius - half_pen

            # Ensure min/max don't cross if track is too narrow
            if clamped_min_x > clamped_max_x:
                clamped_min_x = clamped_max_x = track_rect.center().x()

            clamped_center_x = max(clamped_min_x, min(handle_pos_x, clamped_max_x))

            cursor_center = QPoint(int(clamped_center_x), center_y) # Use int for drawing coordinates
            painter.drawEllipse(cursor_center, int(dynamic_radius), int(dynamic_radius)) 
            # --- End dynamic cursor drawing ---
        else:
            # --- Draw the filled portion (existing logic) ---
            fill_width = handle_pos_x - track_rect.left()
            fill_rect = QRect(track_rect.left(), track_rect.top(), fill_width, self._track_height) # Use _track_height

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self._fill_color))
            
            path = QPainterPath()
            path.addRoundedRect(track_rect, self._track_radius, self._track_radius) # Use _track_radius
            painter.setClipPath(path) 
            
            # Use _track_radius here too
            fill_draw_rect = QRect(fill_rect.left(), fill_rect.top(), fill_rect.width() + self._track_radius, fill_rect.height()) 
            painter.drawRoundedRect(fill_draw_rect, self._track_radius, self._track_radius) # Use _track_radius

            painter.setClipping(False) # Reset clipping
            # --- End fill drawing ---

    def wheelEvent(self, event):
        # Ignore wheel events to prevent accidental value changes
        event.ignore()

class CenteredIconContainer(QWidget):
    """Container widget that centers its content in the available space"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setAlignment(Qt.AlignCenter)  # Center contents
        
    def setWidget(self, widget):
        # Clear any existing widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Add the new widget centered
        self.layout.addWidget(widget, 0, Qt.AlignCenter)

class RoundedImage(QLabel):
    """
    A centralized class for displaying images with rounded corners.
    """
    def __init__(self, parent=None, border_radius=TABLE_CELL_RADIUS, fixed_size=None):
        super().__init__(parent)
        self.pixmap_data = None
        self.border_radius = border_radius
        
        # Set fixed size if provided
        if fixed_size:
            if isinstance(fixed_size, (list, tuple)) and len(fixed_size) == 2:
                self.setFixedSize(fixed_size[0], fixed_size[1])
            else:
                self.setFixedSize(fixed_size, fixed_size)
        
    def setPixmap(self, pixmap):
        self.pixmap_data = pixmap
        super().setPixmap(pixmap)
    
    def setBorderRadius(self, radius):
        """Update the border radius used for the rounded corners"""
        if self.border_radius != radius:
            self.border_radius = radius
            self.update()
    
    def paintEvent(self, event):
        if self.pixmap_data:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Create rounded rect path
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)
            
            # Clip to rounded rectangle
            painter.setClipPath(path)
            
            # Calculate position to center the pixmap
            x = (self.width() - self.pixmap_data.width()) / 2
            y = (self.height() - self.pixmap_data.height()) / 2
            
            # Draw the pixmap
            painter.drawPixmap(int(x), int(y), self.pixmap_data)
        else:
            super().paintEvent(event)

class ScrollableMessageDialog(QDialog):
    """A reusable dialog with a scrollable text area for displaying lists of items."""
    
    def __init__(self, parent=None, title="Message", message="", 
                content="", min_width=DEFAULT_DIALOG_WIDTH, min_height=DEFAULT_DIALOG_HEIGHT, 
                buttons=QDialogButtonBox.Ok, extra_widgets=None, footer_text=None,
                text_browser_min_height=DEFAULT_TEXT_BROWSER_MIN_HEIGHT):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create header section
        header_container = None
        header_height = 0
        if message:
            header_container = QWidget()
            header_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            header_layout = QVBoxLayout(header_container)
            header_layout.setContentsMargins(0, 0, 0, 0)
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            header_layout.addWidget(message_label)
            layout.addWidget(header_container)
            header_height = header_container.sizeHint().height()
        
        # Scrollable content area
        self.content_browser = QTextBrowser()
        self.content_browser.setReadOnly(True)
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.setMinimumHeight(text_browser_min_height)
        
        # Set content (HTML or plain text)
        if content:
            if isinstance(content, list):
                # Convert list items to HTML bullet points
                html_content = "".join([f"• {item}<br>" for item in content])
                self.content_browser.setHtml(html_content)
            else:
                # Assume it's already HTML
                self.content_browser.setHtml(content)
        
        # Add scrollable area to layout with stretch
        layout.addWidget(self.content_browser, 1)
        
        # Create footer container with fixed size policy
        footer_container = QWidget()
        footer_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(6)  # Ensure proper spacing between footer items
        
        footer_height = 0
        # Add footer text if provided
        if footer_text:
            footer_label = QLabel(footer_text)
            footer_label.setWordWrap(True)
            footer_layout.addWidget(footer_label)
        
        # Add any extra widgets with fixed height policies
        if extra_widgets:
            for widget in extra_widgets:
                # Ensure radio buttons and other widgets have fixed height policies
                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                footer_layout.addWidget(widget)
        
        # Only add the footer container if it has content
        has_footer_content = footer_text or (extra_widgets and len(extra_widgets) > 0)
        if has_footer_content:
            layout.addWidget(footer_container)
            footer_height = footer_container.sizeHint().height() + 10  # Add padding
        
        # Add buttons with fixed height policy
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        buttons_height = self.button_box.sizeHint().height()
        
        # Calculate spacing height (layout spacing times number of sections)
        spacing_count = 1  # Always have spacing between content and buttons
        if header_container:
            spacing_count += 1  # Add spacing for header
        if has_footer_content:
            spacing_count += 1  # Add spacing for footer
        spacing_height = layout.spacing() * spacing_count
        
        # Calculate appropriate minimum size with a safety margin
        adjusted_min_height = header_height + text_browser_min_height + footer_height + buttons_height + spacing_height + 10
        adjusted_min_width = max(min_width, 300)  # Ensure reasonable minimum width
        
        # Set dialog minimum size
        self.setMinimumSize(adjusted_min_width, adjusted_min_height)
    
    def get_content_browser(self):
        """Get the content browser widget for advanced customization."""
        return self.content_browser

def create_scrollable_message_dialog(parent, title, message, content, 
                                    min_width=DEFAULT_DIALOG_WIDTH, min_height=DEFAULT_DIALOG_HEIGHT, 
                                    buttons=QDialogButtonBox.Ok, extra_widgets=None, footer_text=None,
                                    text_browser_min_height=DEFAULT_TEXT_BROWSER_MIN_HEIGHT):
    dialog = ScrollableMessageDialog(
        parent=parent,
        title=title,
        message=message,
        content=content,
        min_width=min_width,
        min_height=min_height,
        buttons=buttons,
        extra_widgets=extra_widgets,
        footer_text=footer_text,
        text_browser_min_height=text_browser_min_height
    )
    
    return dialog, dialog.get_content_browser

class CustomCheckBox(QCheckBox):
    """
    A custom checkbox that draws a thin, rounded strip below the text.
    When checked, the strip and text are highlighted.

    Usage:
        cb = CustomCheckBox("Label")
        # Optionally customize appearance:
        cb.setCheckedColor("#45e09a")
        cb.setUncheckedColor("#2b7b55")
    """
    def __init__(
        self,
        text="",
        parent=None,
        checked_color="#45e09a",
        unchecked_color="#2b7b55"
    ):
        super().__init__(text, parent)
        self._checked_color = checked_color
        self._unchecked_color = unchecked_color
        self._strip_thickness = 4  # px
        self._strip_margin = 12    # px shorter than text width (6px each side)
        self.setCursor(Qt.PointingHandCursor)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(BUTTON_HEIGHT)

    def setCheckedColor(self, color):
        self._checked_color = color
        self.update()

    def setUncheckedColor(self, color):
        self._unchecked_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Determine strip and text color
        color = self._checked_color if self.isChecked() else self._unchecked_color

        # Calculate text rect
        fm = QFontMetrics(self.font())
        text = self.text()
        text_rect = fm.boundingRect(text)
        padding = 10
        rect_width = text_rect.width() + padding * 2
        rect_height = BUTTON_HEIGHT
        rect = QRectF(
            0,
            0,
            rect_width,
            rect_height
        )

        # Center horizontally in widget
        x_offset = (self.width() - rect.width()) / 2
        rect.moveLeft(x_offset)

        # Draw text centered inside border, with color depending on checked state
        painter.setPen(QColor(color))
        painter.drawText(rect, Qt.AlignCenter, text)

        # Draw the rounded strip below the text
        strip_length = max(10, text_rect.width() - self._strip_margin)
        strip_radius = self._strip_thickness / 2
        strip_x = rect.center().x() - strip_length / 2
        strip_y = rect.bottom() - 4  # Pixel above the bottom edge

        strip_rect = QRectF(strip_x, strip_y, strip_length, self._strip_thickness)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(strip_rect, strip_radius, strip_radius)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        text_rect = fm.boundingRect(self.text())
        padding = 10
        width = text_rect.width() + padding * 2
        height = BUTTON_HEIGHT
        return QSize(width, height)