# SteamKM_Category_Menu.py 
# Need to do: Make the categories part scrollable
from functools import partial
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QMessageBox, QLineEdit, QDialog, QFormLayout, 
    QGroupBox, QScrollArea, QSpacerItem, QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt
from SteamKM_Themes import BUTTON_HEIGHT, COLOR_PICKER_BUTTON_STYLE, COLOR_RESET_BUTTON_STYLE

class CategoryManagerDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories.copy()
        self.category_map = {}  # Maps old category names to new ones
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Manage Categories")
        layout = QVBoxLayout(self)
        
        # Category list
        self.group_box = QGroupBox()
        self.form_layout = QFormLayout()
        self.group_box.setLayout(self.form_layout)
        self.refresh_categories()
        layout.addWidget(self.group_box)

        # Add category section
        add_layout = QHBoxLayout()
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("New category name")
        add_button = QPushButton("Add Category")
        add_button.clicked.connect(self.add_category)
        add_layout.addWidget(self.new_category_input)
        add_layout.addWidget(add_button)
        layout.addLayout(add_layout)
        
        # Dialog buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)
        
        self.resize(400, 500)

    def refresh_categories(self):
        # Remove all items from the form layout
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        # Add DeepTitle label to the form layout
        group_box_label = QLabel("Categories")
        group_box_label.setObjectName("DeepTitle")
        group_box_label.setAlignment(Qt.AlignCenter)
        self.form_layout.addRow(group_box_label)  # Add this line
        
        for i, category in enumerate(self.categories):
            # Category name
            name_label = QLabel(category)
            
            # Actions widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(0)

            # Add a spacer to push buttons to the right
            spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            actions_layout.addItem(spacer)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(partial(self.edit_category, i))
            edit_btn.setFixedSize(100, BUTTON_HEIGHT)
            edit_btn.setStyleSheet(f""" QPushButton {{{ COLOR_PICKER_BUTTON_STYLE }}} """)
                
            delete_btn = QPushButton("X")
            delete_btn.setObjectName("resetButton")
            delete_btn.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
            delete_btn.clicked.connect(partial(self.delete_category, i))
            delete_btn.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
            delete_btn.setStyleSheet(f""" QPushButton {{{ COLOR_RESET_BUTTON_STYLE }}} """)
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.form_layout.addRow(name_label, actions_widget)

    def add_category(self):
        name = self.new_category_input.text().strip()
        if name and name not in self.categories:
            self.categories.append(name)
            self.new_category_input.clear()
            self.refresh_categories()
            
    def edit_category(self, row):
        old_name = self.categories[row]
        new_name, ok = QInputDialog.getText(self, "Edit Category", 
                                          "New category name:", 
                                          text=old_name)
        if ok and new_name.strip() and new_name != old_name:
            self.categories[row] = new_name
            self.category_map[old_name] = new_name
            self.refresh_categories()
            
    def delete_category(self, row):
        if len(self.categories) > 1:
            category = self.categories[row]
            self.categories.pop(row)
            self.refresh_categories()
        else:
            QMessageBox.warning(self, "Error", "Cannot delete the last category")
