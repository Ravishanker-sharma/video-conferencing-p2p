from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFrame, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal

class LoginWidget(QWidget):
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout centered
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card Frame
        card = QFrame()
        card.setFixedSize(400, 550)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 16px;
                border: 1px solid #3d3d3d;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 50, 50, 50)
        card_layout.setSpacing(25)

        # Logo / Title
        title_label = QLabel("Secure Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: bold; border: none;")
        
        subtitle = QLabel("Post-Quantum Video Link")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 14px; margin-bottom: 20px; border: none;")

        # Inputs
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")
        self.email_input.setStyleSheet(self.input_style())
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(self.input_style())

        # Login Button
        self.btn_login = QPushButton("Sign In")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
        """)
        self.btn_login.clicked.connect(self.handle_login)

        # Mock "Forgot Password"
        forgot_label = QLabel("Forgot Password?")
        forgot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_label.setStyleSheet("color: #007bff; font-size: 12px; border: none;")
        forgot_label.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout.addStretch()
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(self.btn_login)
        card_layout.addWidget(forgot_label)
        card_layout.addStretch()

        main_layout.addWidget(card)

    def input_style(self):
        return """
            QLineEdit {
                background-color: #1f1f1f;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
        """

    def handle_login(self):
        # Mock validation
        if not self.email_input.text() or not self.pass_input.text():
            # In a real app we'd show an error, but for simulation we just proceed or maybe shake
            pass
        
        # Proceed regardless for simulation
        self.login_successful.emit()
