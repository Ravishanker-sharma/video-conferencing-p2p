from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from user_profile import UserProfile
from profile_widget import ProfileWidget

class ModeSelectionWidget(QWidget):
    mode_selected = pyqtSignal(str) # Emits "HOST" or "CLIENT"

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(60)

        # Header Frame/Layout to hold potentially Title and Profile
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 20, 20, 0)
        
        # Profile Button (Top Right)
        self.profile_btn = QPushButton()
        self.profile_btn.setFixedSize(50, 50)
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_profile_button()
        self.profile_btn.clicked.connect(self.open_profile)

        # Title Section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(15)
        
        main_title = QLabel("Team Connect")
        main_title.setStyleSheet("font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: 1px;")
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sub_title = QLabel("Secure High-Fidelity Video Conferencing")
        sub_title.setStyleSheet("font-size: 16px; color: #888888; font-weight: 500;")
        sub_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(main_title)
        title_layout.addWidget(sub_title)

        # Top Bar assembly
        # We want the profile button to be on the right, title in center
        # HBox: [Stretch] [Title Layout] [Stretch w/ Profile at end?]
        # Easier: Just use a Relative layout or add profile to a top HBox and Title below.
        
        # Let's put Profile Button in a top bar, and Title below it.
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.addStretch()
        top_layout.addWidget(self.profile_btn)
        
        layout.addWidget(top_container)
        layout.addLayout(title_layout)

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

    def update_profile_button(self):
        profile = UserProfile()
        initials = profile.get_initials()
        self.profile_btn.setText(initials)
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 25px;
                font-weight: bold;
                font-size: 18px;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

    def open_profile(self):
        # Create a menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007bff;
            }
        """)
        
        # Actions
        act_account = QAction("Account Settings", self)
        act_account.triggered.connect(lambda: print("Account settings clicked")) # Placeholder
        
        act_settings = QAction("Settings", self)
        act_settings.triggered.connect(self.show_settings_dialog)
        
        act_help = QAction("Help", self)
        act_help.triggered.connect(lambda: print("Help clicked")) # Placeholder
        
        menu.addAction(act_account)
        menu.addSeparator()
        menu.addAction(act_settings)
        menu.addSeparator()
        menu.addAction(act_help)
        
        # Show menu at button position
        menu.exec(self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft()))

    def show_settings_dialog(self):
        self.profile_window = ProfileWidget() # Keep reference
        self.profile_window.show()

