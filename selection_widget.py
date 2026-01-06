from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QHBoxLayout, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class ModeSelectionWidget(QWidget):
    mode_selected = pyqtSignal(str) # Emits "HOST" or "CLIENT"

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(60)

        # Header Section
        header = QVBoxLayout()
        header.setSpacing(15)
        
        main_title = QLabel("Team Connect")
        main_title.setStyleSheet("font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: 1px;")
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sub_title = QLabel("Secure High-Fidelity Video Conferencing")
        sub_title.setStyleSheet("font-size: 16px; color: #888888; font-weight: 500;")
        sub_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header.addWidget(main_title)
        header.addWidget(sub_title)
        layout.addLayout(header)

        # Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(50)
        
        # New Meeting (Host)
        self.btn_host = self.create_card(
            "NEW MEETING", 
            "Start a Session", 
            "Create a new secure meeting room and invite your team members.", 
            "#3b82f6", "HOST" # Blue
        )
        
        # Join Meeting (Client)
        self.btn_client = self.create_card(
            "JOIN", 
            "Join a Session", 
            "Enter a meeting code or address to connect to an ongoing call.", 
            "#10b981", "CLIENT" # Green
        )

        cards_layout.addStretch()
        cards_layout.addWidget(self.btn_host)
        cards_layout.addWidget(self.btn_client)
        cards_layout.addStretch()

        layout.addLayout(cards_layout)

    def create_card(self, badge_text, title_text, desc_text, accent_color, mode_key):
        container = QWidget()
        container.setFixedSize(320, 420)
        
        # Button acts as the card background
        btn = QPushButton(container)
        btn.setGeometry(0, 0, 320, 420)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Colors for states
        normal_bg = "#1e1e1e"
        hover_bg = "#252525"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_bg};
                border: 1px solid #333333;
                border-radius: 24px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent_color};
            }}
            QPushButton:pressed {{
                background-color: #1a1a1a;
            }}
        """)
        
        btn.clicked.connect(lambda: self.mode_selected.emit(mode_key))

        # Layout inside the card (we use a VBox on the container, but we need to make sure mouse clicks pass through labels)
        # Actually easiest is to just set a layout on the button itself if possible, or use a widget overlay. 
        # Making the button the parent of the layout works in PyQt.
        
        card_layout = QVBoxLayout(btn)
        card_layout.setContentsMargins(35, 45, 35, 45)
        card_layout.setSpacing(20)

        # Badge
        badge = QLabel(badge_text)
        badge.setFixedHeight(28)
        badge.setStyleSheet(f"""
            color: {accent_color};
            font-weight: 800;
            font-size: 13px;
            background-color: {accent_color}1a;
            border-radius: 6px;
            padding: 4px 12px;
            border: 1px solid {accent_color}33;
        """)
        # Hack to make badge fit content width
        badge_wrapper = QHBoxLayout()
        badge_wrapper.addWidget(badge)
        badge_wrapper.addStretch()
        
        # Icon Placeholder (Circle)
        icon_circle = QLabel()
        icon_circle.setFixedSize(64, 64)
        icon_circle.setStyleSheet(f"""
            background-color: {accent_color}1a;
            border-radius: 32px;
            border: 2px solid {accent_color};
        """)
        # We could put a text icon inside
        icon_text = "📹" if mode_key == "HOST" else "🔗"
        icon_label = QLabel(icon_text, icon_circle)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet(f"font-size: 28px; background: transparent; border: none; color: white;")


        # Title
        title = QLabel(title_text)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: white; border: none; background: transparent;")
        
        # Description
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 15px; color: #9ca3af; line-height: 1.5; border: none; background: transparent;")
        
        # Arrow Action
        arrow = QLabel("➜")
        arrow.setAlignment(Qt.AlignmentFlag.AlignRight)
        arrow.setStyleSheet(f"color: {accent_color}; font-size: 24px; font-weight: bold; border: none; background: transparent;")

        card_layout.addLayout(badge_wrapper)
        card_layout.addWidget(icon_circle)
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addStretch()
        card_layout.addWidget(arrow)

        # Make sure labels don't block button click
        for w in [badge, icon_circle, icon_label, title, desc, arrow]:
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        return container
