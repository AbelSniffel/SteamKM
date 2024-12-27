# SteamKM_Category_Menu.py
from functools import partial
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QDialog, 
    QGroupBox, QScrollArea, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt
from SteamKM_Themes import BUTTON_HEIGHT, COLOR_RESET_BUTTON_STYLE

class CategoryManagerDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories.copy()
        self.category_map = {}  # Maps old category names to new ones
        self.setup_ui()
        self.resize(350, 400)

    def setup_ui(self):
        self.setWindowTitle("Manage Categories")
        layout = QVBoxLayout(self)

        # Category list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)  # Fixed gap between entries
        self.scroll_layout.addStretch(1)  # Force entries to the top
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Add new category section
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

        self.refresh_categories()

    def refresh_categories(self):
        # Clear existing widgets
        for i in reversed(range(self.scroll_layout.count() - 1)):  # Exclude stretch item
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add category widgets
        for category in self.categories:
            self.add_category_widget(category)

    def add_category_widget(self, category):
        count_label = QLabel(f"{self.categories.index(category) + 1}  ")
        count_label.setStyleSheet("font-size: 15px;")

        name_edit = QLineEdit(category)
        name_edit.setObjectName("CustomLineEdit")
        name_edit.setFixedHeight(33)
        name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_edit.editingFinished.connect(partial(self.update_category, category, name_edit))

        delete_btn = QPushButton("X")
        delete_btn.setObjectName("resetButton")
        delete_btn.setFixedSize(BUTTON_HEIGHT + 2, BUTTON_HEIGHT)
        delete_btn.setStyleSheet(f"QPushButton {{{COLOR_RESET_BUTTON_STYLE}}}")
        delete_btn.clicked.connect(partial(self.delete_category, category))

        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 5, 10, 0)
        hbox.addWidget(count_label)
        hbox.addWidget(name_edit)
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
                f"Are you sure you want to remove the category: {category}? \nAll entries using this category will default to '{new_default_category}'.", 
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
