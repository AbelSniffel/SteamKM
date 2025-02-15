# SteamKM_Edit_Menu.py
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from SteamKM_Config import load_config

class EditGameDialog(QDialog):
    def __init__(self, parent=None, games=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Games Menu")
        self.resize(450, 350)
        self.games = games if games else []
        self.categories = load_config().get("categories", ["Premium", "Good", "Low Effort", "Bad", "VR", "Used", "New"])
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area.setWidget(scroll_area_widget)
        scroll_area_layout = QVBoxLayout(scroll_area_widget)
        scroll_area_layout.setAlignment(Qt.AlignTop)

        self.group_boxes = []

        for idx, game in enumerate(self.games):
            hbox = QHBoxLayout()

            number_label = QLabel(f"{idx + 1}  ")
            number_label.setStyleSheet("font-size: 24px;")
            hbox.addWidget(number_label)

            group_box = QGroupBox()
            group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            form_layout = QFormLayout()

            title_edit = QLineEdit(game["title"], objectName="EncasedRadiusHalved")
            form_layout.addRow("Title:", title_edit)

            key_edit = QLineEdit(game["key"], objectName="EncasedRadiusHalved")
            form_layout.addRow("Key:", key_edit)

            category_combo = ScrollRejectionComboBox()
            category_combo.setObjectName("EncasedRadiusHalved")
            category_combo.addItems(self.categories)
            current_category = game["category"] if game["category"] in self.categories else "New"
            category_combo.setCurrentText(current_category)
            form_layout.addRow("Category:", category_combo)

            group_box.setLayout(form_layout)
            hbox.addWidget(group_box)

            scroll_area_layout.addLayout(hbox)
            scroll_area_layout.addSpacing(10)

            self.group_boxes.append((group_box, title_edit, key_edit, category_combo))

        main_layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(apply_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def apply_changes(self):
        for idx, (group_box, title_edit, key_edit, category_combo) in enumerate(self.group_boxes):
            self.games[idx]["title"] = title_edit.text()
            self.games[idx]["key"] = key_edit.text()
            self.games[idx]["category"] = category_combo.currentText()
        self.accept()

class ScrollRejectionComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()