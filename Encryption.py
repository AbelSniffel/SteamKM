# Encryption.py
import base64
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from Config import ConfigManager, get_config_dir
from Theme_Menu import Theme

class InitialPasswordDialog(QDialog):
    """A password dialog that applies theming before the main application is loaded"""
    def __init__(self, title="Password", message="Enter Password:"):
        super().__init__(None)
        self.setWindowTitle(title)
        self.setFixedWidth(270)
        
        # Initialize config and theme
        self.config_manager = ConfigManager()
        self.apply_theme()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFixedWidth(250)
        layout.addWidget(message_label)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_field)
        
        # Status label (initially hidden)
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusNeutral")
        self.status_label.setWordWrap(True)
        # Fixed width for status label too
        self.status_label.setFixedWidth(250)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Open Sesame")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("No Thanks")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Set layout and adjust size to content
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.adjustSize()
    
    def apply_theme(self):
        """Apply theme based on config settings"""
        # Get theme settings from config
        theme_name = self.config_manager.get("theme", "dark")
        using_custom_colors = self.config_manager.get("using_custom_colors", False)
        custom_colors = self.config_manager.get("custom_colors", {})
        border_radius = self.config_manager.get("border_radius", 8)
        border_size = self.config_manager.get("border_size", 1)
        border_size_interactables = self.config_manager.get("border_size_interactables", 1)
        checkbox_radius = self.config_manager.get("checkbox_radius", 3)
        bar_radius = self.config_manager.get("bar_radius", 3)
        bar_thickness = self.config_manager.get("bar_thickness", 10)
        
        # Create Theme instance based on settings
        if using_custom_colors:
            theme = Theme(theme_name, custom_colors, border_radius, border_size, 
                          checkbox_radius, bar_radius, bar_thickness)
        else:
            theme = Theme(theme_name)
            
        # Apply stylesheet to dialog
        stylesheet = theme.generate_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def show_error(self, message):
        """Display an error message in the status label"""
        self.status_label.setText(message)
        self.status_label.setObjectName("StatusError")
        self.status_label.setVisible(True)
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def get_password(self):
        return self.password_field.text()

class PasswordChangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setFixedSize(340, 170)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Password fields
        layout.addWidget(QLabel("New Password:"))
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_password)
        
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_password)
        
        # Status label and button in the same horizontal layout
        status_button_layout = QHBoxLayout()
        
        # Status label with improved visibility
        self.status_label = QLabel("Waiting for password", objectName="StatusNeutral")
        self.status_label.setWordWrap(True)
        status_button_layout.addWidget(self.status_label, 1)  # Give the label more space
        
        # Create the button with more visible disabled state
        self.ok_button = QPushButton("Change Password")
        self.ok_button.setEnabled(False)  # Disabled initially
        self.ok_button.clicked.connect(self.accept)
        status_button_layout.addWidget(self.ok_button)
        
        # Add the horizontal layout to the main vertical layout
        layout.addLayout(status_button_layout)
        
        # Connect text changed signals
        self.new_password.textChanged.connect(self.validate_passwords)
        self.confirm_password.textChanged.connect(self.validate_passwords)
    
    def validate_passwords(self):
        new_pass = self.new_password.text()
        confirm_pass = self.confirm_password.text()
        
        if not new_pass:
            self.status_label.setText("Password cannot be empty")
            self.status_label.setObjectName("StatusError")
            self.ok_button.setEnabled(False)
        elif new_pass != confirm_pass:
            self.status_label.setText("Passwords don't match")
            self.status_label.setObjectName("StatusError")
            self.ok_button.setEnabled(False)
        else:
            self.status_label.setText("Passwords match")
            self.status_label.setObjectName("StatusSuccess")
            self.ok_button.setEnabled(True)
        
        # Force style update after changing the object name
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def get_password(self):
        return self.new_password.text()

class PasswordDialog(QDialog):
    def __init__(self, parent=None, title="Password", message="Enter Password:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(230)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_field)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Create fixed width buttons
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_password(self):
        return self.password_field.text()

class EncryptionManager:
    def __init__(self, main_window):
        self.main_window = main_window
        data_dir = get_config_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = data_dir / "steam_keys.json"
        self.encrypted_data_file = data_dir / "steam_keys.json.enc"
        self.password = None
        self.wrong_password_attempts = 0  # Track wrong password attempts

    def _generate_key(self, password, salt=None):
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return kdf.derive(password.encode()), salt

    def _cipher_factory(self, password, salt=None, iv=None):
        key, salt = self._generate_key(password, salt)
        iv = iv or os.urandom(16)
        return Cipher(algorithms.AES(key), modes.CBC(iv)), salt, iv

    def encrypt_data(self, data, password):
        cipher, salt, iv = self._cipher_factory(password)
        encryptor = cipher.encryptor()
        padded_data = data + (16 - len(data) % 16) * chr(16 - len(data) % 16)
        ct = encryptor.update(padded_data.encode()) + encryptor.finalize()
        return base64.b64encode(salt + iv + ct).decode('utf-8')

    def decrypt_data(self, data, password):
        raw = base64.b64decode(data)
        salt, iv, ct = raw[:16], raw[16:32], raw[32:]
        cipher, _, _ = self._cipher_factory(password, salt, iv)
        decryptor = cipher.decryptor()
        try:
            pt = decryptor.update(ct) + decryptor.finalize()
            return pt[:-ord(pt[-1:])].decode('utf-8')
        except Exception:  # Correctly handle decryption errors
            return None

    def show_themed_password_dialog(self, title, message):
        dialog = PasswordDialog(self.main_window, title, message)
        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.get_password(), True
        else:
            return "", False

    def show_initial_password_dialog(self, title, message):
        """Show the initial password dialog with theming"""
        dialog = InitialPasswordDialog(title, message)
        result = dialog.exec()
        if result == QDialog.Accepted:
            password = dialog.get_password()
            if not password:
                dialog.show_error("Password cannot be empty.")
                return self.show_initial_password_dialog(title, message)
            return password, True
        else:
            return "", False

    def prompt_password(self):
        if not self.encrypted_data_file.exists() and not self.data_file.exists():
            text = "No data file found. \nPlease set up an encryption key:"
            while True:
                password, ok = self.show_initial_password_dialog("SteamKM Encryption", text)
                if not ok:
                    sys.exit(0)
                if password:
                    self.password = password
                    self.save_data("{}") # Save empty data to create encrypted file
                    return password
                else:
                    continue  # Error already shown by the dialog
        elif not self.encrypted_data_file.exists():
            text = "Found unencrypted game keys file!\nPlease set up an encryption key:"
        else:
            text = "Enter encryption key:"
        
        dialog = InitialPasswordDialog("SteamKM Encryption", text)
        self.wrong_password_attempts = 0  # Reset counter at start

        fun_texts = [
            "Wrong password, please try again",
            "Still not right! Try again",
            "Maybe your caps lock is on?",
            "Are you sure you remember it?",
            "Persistence is key... but not this key",
            "Hint: It's not chicken, or maybe it is?",
            "Umm...",
            "Did you know that tangerines are not oranges?",
            "Horses jump higher than rabbits",
            "Want a hint? I don't know it either",
            "Okay, last try?",
            "...",
            "...",
            "...",
            "I'm judging you now",
            "This is actually your last chance",
        ]

        while True:
            result = dialog.exec()
            if result != QDialog.Accepted:
                sys.exit(0)
                return None

            password = dialog.get_password()
            if not password:
                dialog.show_error("Password cannot be empty.")
                continue

            if not self.encrypted_data_file.exists():
                return password
            elif self.decrypt_data(self.encrypted_data_file.read_text(), password) is not None:
                return password
            else:
                msg_idx = min(self.wrong_password_attempts, len(fun_texts) - 1)
                dialog.show_error(fun_texts[msg_idx])
                # Only exit after showing the last message and one more wrong attempt
                if self.wrong_password_attempts >= len(fun_texts):
                    sys.exit(0)
                self.wrong_password_attempts += 1

    def change_password(self):
        # Loop to handle wrong old password attempts
        while True:
            old_password, ok = QInputDialog.getText(self.main_window, "Old Password", "Enter Old Password:", QLineEdit.Password)
            if not ok:
                return
            
            if old_password != self.password:
                QMessageBox.warning(self.main_window, "Error", "Wrong password, try again.")
                continue
            
            # Show the new password change dialog
            password_dialog = PasswordChangeDialog(self.main_window)
            if password_dialog.exec() != QDialog.Accepted:
                return
                
            new_password = password_dialog.get_password()
                
            try:
                decrypted_data = self.decrypt_data(self.encrypted_data_file.read_text(), old_password)
                if decrypted_data is None:
                    QMessageBox.critical(self.main_window, "Error", "Failed to decrypt data with old password.")
                    return

                self.password = new_password
                self.save_data(decrypted_data)
                QMessageBox.information(self.main_window, "Success", "Password changed successfully.")
                return
            except Exception as e:
                QMessageBox.critical(self.main_window, "Error", f"An error occurred: {e}")
                return

    def load_data(self):
        # Neither encrypted nor plaintext file exists
        if not self.encrypted_data_file.exists() and not self.data_file.exists():
            self.password = self.prompt_password()
            if self.password is None:
              return None
            return "{}"  # Return an empty JSON object to start fresh

        # Encrypted file doesn't exist, but plaintext does
        elif not self.encrypted_data_file.exists() and self.data_file.exists():
            if self.password is None:
                self.password = self.prompt_password()
                if self.password is None:
                    return None
            plaintext_data = self.data_file.read_text()
            self.encrypted_data_file.write_text(self.encrypt_data(plaintext_data, self.password))
            self.data_file.unlink()
            return plaintext_data

        # Encrypted file exists
        elif self.encrypted_data_file.exists():
            if self.password is None:
                self.password = self.prompt_password()
            if self.password is None:
                return None
            try:
                decrypted_data = self.decrypt_data(self.encrypted_data_file.read_text(), self.password)
                if decrypted_data:
                    return decrypted_data
                else:
                  QMessageBox.critical(self.main_window, "Error", "Incorrect password or corrupted data.")
                  self.password = None
                  return self.load_data()
            except Exception as e:
                QMessageBox.critical(self.main_window, "Error", f"Failed to load data: {e}")
                self.main_window.close()
                return None

    def save_data(self, data):
        if not self.password:
            QMessageBox.critical(self.main_window, "Error", "Password not set.")
            self.main_window.close()
            return
        try:
            encrypted_data = self.encrypt_data(data, self.password)
            if self.encrypted_data_file.exists():
                self.encrypted_data_file.replace(self.encrypted_data_file.with_suffix(".enc.bak"))
            self.encrypted_data_file.write_text(encrypted_data)
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to save data: {e}")