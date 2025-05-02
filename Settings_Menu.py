# Settings_Menu.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from Config import UI_MARGIN, BUTTON_HEIGHT, VERTICAL_SPACING
import os

class SettingsMenuDialog(QDialog):
    settings_imported = Signal()  # Signal to notify import

    def __init__(self, parent=None, encryption_manager=None, config_path=None):
        super().__init__(parent)
        self.setWindowTitle("Settings Menu")
        self.setMinimumSize(350, 200) # Add an extra 35px to the height when using an extra row of buttons in a groupbox
        self.encryption_manager = encryption_manager
        self.config_path = config_path or os.path.join(os.getcwd(), "manager_settings.json")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*UI_MARGIN)
        layout.setAlignment(Qt.AlignTop)

        # Manager File GroupBox
        manager_group = QGroupBox()
        manager_layout = QVBoxLayout(manager_group)
        manager_label = QLabel("Manager Settings", objectName="Title", fixedHeight=BUTTON_HEIGHT)
        manager_label.setAlignment(Qt.AlignCenter)
        manager_layout.addWidget(manager_label)

        buttons_layout = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.import_settings)
        buttons_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_settings)
        buttons_layout.addWidget(self.export_button)

        manager_layout.addLayout(buttons_layout)
        layout.addWidget(manager_group)

        # Spacing between GroupBoxes
        layout.addSpacing(VERTICAL_SPACING)

        # Actions GroupBox
        actions_group = QGroupBox()
        actions_layout = QVBoxLayout(actions_group)
        actions_label = QLabel("Actions", objectName="Title", fixedHeight=BUTTON_HEIGHT)
        actions_label.setAlignment(Qt.AlignCenter)
        actions_layout.addWidget(actions_label)

        actions_buttons_layout = QHBoxLayout()
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.clicked.connect(self.change_password)
        actions_buttons_layout.addWidget(self.change_password_button)

        self.open_data_dir_button = QPushButton("Open Folder Location")
        self.open_data_dir_button.clicked.connect(self.open_data_directory)
        actions_buttons_layout.addWidget(self.open_data_dir_button)

        actions_layout.addLayout(actions_buttons_layout)
        layout.addWidget(actions_group)

    def import_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import manager_settings.json", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as src, open(self.config_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Import Successful", "Settings imported successfully.")
                self.settings_imported.emit()
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Error: {e}")

    def export_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export manager_settings.json", "manager_settings.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(self.config_path, "r", encoding="utf-8") as src, open(file_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Export Successful", "Settings exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error: {e}")

    def change_password(self):
        if self.encryption_manager:
            self.encryption_manager.change_password()
        else:
            QMessageBox.warning(self, "Unavailable", "Encryption manager not available.")

    def open_data_directory(self):
        data_dir = os.path.dirname(self.config_path)
        if os.path.exists(data_dir):
            os.startfile(data_dir)
        else:
            QMessageBox.warning(self, "Directory Not Found", f"{data_dir} does not exist.")
