# Category_Menu.py
from functools import partial
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QDialog, QGroupBox, QScrollArea, QSizePolicy, QMessageBox
from PySide6.QtCore import Signal, QTimer
from Theme_Menu import BUTTON_HEIGHT
from Config import ConfigManager, UI_MARGIN, HORIZONTAL_SPACING, ICON_BUTTON_WIDTH

class CategoryManagerDialog(QDialog):
    status_message_label = Signal(str, bool)
    
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories.copy()
        self.category_map = {}  # Maps old category names to new ones
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.setMinimumSize(250, 200)
        self.resize(350, 398)

    def setup_ui(self):
        self.setWindowTitle("Category Menu")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*UI_MARGIN)

        # Category Adding Group
        add_group = QGroupBox()
        add_layout = QHBoxLayout(add_group)
        
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("New category name")
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_category)
        
        add_layout.addWidget(self.new_category_input)
        add_layout.addWidget(add_button)

        # Create a new group box for the categories section
        categories_group = QGroupBox()
        categories_layout = QVBoxLayout(categories_group)
        
        # Create a scroll area inside the categories group box
        self.scroll_area = QScrollArea(objectName="DynamicVScrollBar")
        self.scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)  # Base margins
        self.scroll_layout.setSpacing(HORIZONTAL_SPACING)  # Space between category entries
        self.scroll_layout.addStretch(1)  # Force entries to the top
        self.scroll_area.setWidget(scroll_widget)
        
        # Add scroll area to categories layout
        categories_layout.addWidget(self.scroll_area)
        
        # Connect to bar signals for margin adjustments
        bar = self.scroll_area.verticalScrollBar()
        bar.rangeChanged.connect(self.adjust_margins_for_bar)
        
        # Initial adjustment after showing
        QTimer.singleShot(10, self.adjust_margins_for_bar)

        # Final Layout     
        layout.addWidget(add_group)
        layout.addSpacing(HORIZONTAL_SPACING)
        layout.addWidget(categories_group)
        
        self.refresh_categories()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self.adjust_margins_for_bar)
        
    def adjust_margins_for_bar(self):
        # Simple check for bar visibility and apply appropriate margins
        bar = self.scroll_area.verticalScrollBar()
        right_margin = 8 if bar.isVisible() and bar.maximum() > 0 else 2
        self.scroll_layout.setContentsMargins(2, 2, right_margin, 2)

    def refresh_categories(self):
        # Clear existing widgets
        for i in reversed(range(self.scroll_layout.count() - 1)):  # Exclude stretch item
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add category widgets
        for category in self.categories:
            self.add_category_widget(category)
            
        # Check if we need to adjust margins after adding/removing categories
        self.adjust_margins_for_bar()
    
    # Override closeEvent to automatically save changes when dialog is closed
    def closeEvent(self, event):
        self.status_message_label.emit("Saved Categories", True)
        self.accept()
        super().closeEvent(event)

    def add_category_widget(self, category):
        name_edit = QLineEdit(category, fixedHeight=BUTTON_HEIGHT)
        name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_edit.editingFinished.connect(partial(self.update_category, category, name_edit))

        if category != "New":
            name_edit.setObjectName("CategoryLineEdit")
        if category == "New":
            name_edit.setDisabled(True)

        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(1, 1, 1, 1)
        hbox.addWidget(name_edit)

        if category != "New":
            delete_btn = QPushButton("X", objectName="ResetButtonHalf", fixedWidth=ICON_BUTTON_WIDTH, fixedHeight=BUTTON_HEIGHT)
            delete_btn.clicked.connect(partial(self.delete_category, category))
            hbox.addWidget(delete_btn)

        container = QWidget()
        container.setLayout(hbox)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, container)

    def add_category(self):
        name = self.new_category_input.text().strip()
        if name and name not in self.categories:
            self.categories.append(name)
            self.new_category_input.clear()
            self.refresh_categories()
        else:
            QMessageBox.warning(self, "Error", "Category name is empty or already exists.")

    def delete_category(self, category):
        if len(self.categories) > 1:
            new_default_category = "New"
            msg_box = QMessageBox.question(
                self, 
                "Confirm Deletion", 
                f"Are you sure you want to remove the category: {category}? \nAll entries using this category will default to {new_default_category}", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if msg_box == QMessageBox.Yes:
                self.categories.remove(category)
                self.refresh_categories()
        else:
            QMessageBox.warning(self, "Error", "Cannot delete the last category.")

    def update_category(self, old_category, line_edit):
        new_name = line_edit.text().strip()
        if new_name and new_name != old_category and new_name not in self.categories:
            self.categories[self.categories.index(old_category)] = new_name
            self.category_map[old_category] = new_name
            self.refresh_categories()
        elif not new_name:
            QMessageBox.warning(self, "Error", "Category name cannot be empty.")
        elif new_name in self.categories:
            QMessageBox.warning(self, "Error", "Category name already exists.")