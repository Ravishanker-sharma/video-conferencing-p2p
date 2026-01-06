from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QScrollArea, QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette

class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #202124; border-bottom: 1px solid #3c4043;")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        
        title = QLabel("In-Call Messages")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        h_layout.addWidget(title)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("color: #9aa0a6; border: none; font-size: 16px; font-weight: bold;")
        close_btn.clicked.connect(self.hide)
        h_layout.addWidget(close_btn)
        
        layout.addWidget(header)

        # Messages Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #202124; }
            QScrollBar:vertical {
                border: none;
                background: #202124;
                width: 10px;
                margin: 0px; 
            }
            QScrollBar::handle:vertical {
                background: #5f6368;
                min-height: 20px;
                border-radius: 5px;
            }
        """)
        
        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background-color: #202124;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(15)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # Input Area
        input_area = QFrame()
        input_area.setStyleSheet("background-color: #202124; border-top: 1px solid #3c4043;")
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Send a message...")
        self.msg_input.returnPressed.connect(self.send_message)
        self.msg_input.setStyleSheet("""
            QLineEdit {
                background-color: #303134;
                border-radius: 20px;
                padding: 10px 15px;
                color: white;
                border: none;
                font-size: 14px;
            }
            QLineEdit:focus {
                background-color: #3c4043;
            }
        """)
        
        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8ab4f8;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #303134;
                border-radius: 20px;
            }
        """)

        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_area)

    def send_message(self):
        text = self.msg_input.text().strip()
        if text:
            # Add my message
            self.add_message(text, is_me=True)
            self.message_sent.emit(text)
            self.msg_input.clear()

    def add_message(self, text, is_me=False):
        bubble_container = QHBoxLayout()
        bubble_container.setContentsMargins(0, 0, 0, 0)
        
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        # Max width 80% of container
        bubble.setMaximumWidth(240) 
        
        if is_me:
            bubble_container.setAlignment(Qt.AlignmentFlag.AlignRight)
            bg_color = "#8ab4f8"
            text_color = "#202124"
        else:
            bubble_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bg_color = "#3c4043"
            text_color = "white"

        bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 10px 15px;
                border-radius: 18px;
                font-size: 14px;
            }}
        """)
        
        bubble_container.addWidget(bubble)
        self.messages_layout.addLayout(bubble_container)
        
        # Auto scroll to bottom
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
