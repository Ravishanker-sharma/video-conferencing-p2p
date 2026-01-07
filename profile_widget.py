from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QHBoxLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from user_profile import UserProfile

class ProfileWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.user_profile = UserProfile()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Profile & Settings")
        self.setFixedSize(500, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QLabel("Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Name Section (Read Only)
        name_label = QLabel("Display Name")
        name_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        layout.addWidget(name_label)

        self.name_display = QLabel(self.user_profile.name)
        self.name_display.setStyleSheet("font-size: 18px; padding: 10px; background: #2d2d2d; border-radius: 8px;")
        layout.addWidget(self.name_display)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #333;")
        layout.addWidget(sep1)

        # Captions Text
        cap_label = QLabel("Simulated Captions Text")
        cap_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        layout.addWidget(cap_label)
        
        desc_cap = QLabel("This text will be cycled through when Captions are enabled.")
        desc_cap.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(desc_cap)

        self.captions_input = QTextEdit()
        self.captions_input.setPlainText(self.user_profile.captions_text)
        self.captions_input.setStyleSheet("background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 8px; padding: 8px;")
        layout.addWidget(self.captions_input)

        # MOM Text
        mom_label = QLabel("Simulated MOM Content")
        mom_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        layout.addWidget(mom_label)
        
        desc_mom = QLabel("Minutes of Meeting content for demo.")
        desc_mom.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(desc_mom)

        self.mom_input = QTextEdit()
        self.mom_input.setPlainText(self.user_profile.mom_text)
        self.mom_input.setStyleSheet("background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 8px; padding: 8px;")
        layout.addWidget(self.mom_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_save.clicked.connect(self.save_changes)
        
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def save_changes(self):
        captions = self.captions_input.toPlainText()
        mom = self.mom_input.toPlainText()
        
        self.user_profile.update_settings(captions, mom)
        self.close()
