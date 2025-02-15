# SteamKM_Encryption.py
import base64
import json
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QApplication

class EncryptionManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.data_file = Path("steam_keys.json")
        self.encrypted_data_file = Path("steam_keys.json.enc")
        self.password = None

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

    def prompt_password(self):
        if not self.encrypted_data_file.exists() and not self.data_file.exists():
            text = "No data file found. Please set up an encryption key:"
            while True:
                password, ok = QInputDialog.getText(self.main_window, "SteamKM Encryption", text, QLineEdit.Password)
                if not ok:
                    sys.exit(0)
                if password:
                    self.password = password
                    self.save_data("{}") # Save empty data to create encrypted file
                    return password
                else:
                    QMessageBox.critical(self.main_window, "Error", "Password cannot be empty.")
        elif not self.encrypted_data_file.exists():
            text = "Found unencrypted Steam Keys file!\nPlease set up an encryption key:"
        else:
            text = "Please enter encryption key:"
        while True:
            password, ok = QInputDialog.getText(self.main_window, "SteamKM Encryption", text, QLineEdit.Password)
            if not ok:
                sys.exit(0)
                return None
            if password:
                if not self.encrypted_data_file.exists():
                    return password
                elif self.decrypt_data(self.encrypted_data_file.read_text(), password) is not None:
                    return password
                else:
                    QMessageBox.critical(self.main_window, "Error", "Wrong password, please try again.")
            else:
                QMessageBox.critical(self.main_window, "Error", "Password cannot be empty.")

    def change_password(self):
        while True:
            old_password, ok = QInputDialog.getText(self.main_window, "Old Password", "Enter Old Password:", QLineEdit.Password)
            if not ok:
                return
            if old_password != self.password:
                QMessageBox.warning(self.main_window, "Error", "Wrong password, try again.")
                continue
            while True:
                new_password, ok = QInputDialog.getText(self.main_window, "New Password", "Enter New Password:", QLineEdit.Password)
                if not ok:
                    return
                if not new_password:
                    QMessageBox.warning(self.main_window, "Error", "New password cannot be empty.")
                    continue
                if new_password == old_password:
                    QMessageBox.warning(self.main_window, "Error", "New password cannot be the same as the old password.")
                    continue

                confirm_password, ok = QInputDialog.getText(self.main_window, "Confirm Password", "Confirm New Password:", QLineEdit.Password)
                if not ok:
                    return

                if new_password != confirm_password:
                    QMessageBox.warning(self.main_window, "Error", "Passwords don't match.")
                    continue

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