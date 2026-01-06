import sys
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QFrame,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

import video
import network

class VideoCallWidget(QWidget):
    call_ended = pyqtSignal()

    def __init__(self, mode="HOST"):
        super().__init__()
        self.mode = mode 
        
        # Initialize core components
        try:
            self.camera = video.VideoCamera()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not access camera: {e}")
            self.camera = None 
            
        self.connection_manager = network.ConnectionManager()
        if self.camera:
            self.connection_manager.set_camera(self.camera)

        self.init_ui()
        
        # Signals
        self.connection_manager.connected.connect(self.on_connected)
        self.connection_manager.disconnected.connect(self.on_disconnected)
        self.connection_manager.error.connect(self.on_error)
        self.connection_manager.new_frame_received.connect(self.update_remote_frame)

        # Timer for local video preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_local_frame)
        self.timer.start(33) 

        # Auto-start hosting if in host mode
        if self.mode == "HOST":
            QTimer.singleShot(500, self.start_host)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # -- Toolbar --
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #333;")
        toolbar.setFixedHeight(70)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        
        # Title depending on mode
        title_text = "Team Meeting Room" if self.mode == "HOST" else "Joining Meeting..."
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        
        # Status Badge
        self.status_badge = QLabel("Initializing...")
        self.status_badge.setStyleSheet("""
            background-color: #333; 
            color: #aaa; 
            padding: 4px 12px; 
            border-radius: 12px; 
            font-size: 12px; 
            font-weight: bold;
        """)

        tb_layout.addWidget(self.lbl_title)
        tb_layout.addSpacing(15)
        tb_layout.addWidget(self.status_badge)
        tb_layout.addStretch()

        # Input fields (Only for Client)
        self.ip_input = QLineEdit("c0aaeec3f161.ngrok-free.app")
        # Hidden input for port to keep logic simple but not show user
        self.port_input = QLineEdit("8000") # Default hardcoded port
        self.port_input.setVisible(False)
        
        if self.mode == "CLIENT":
            self.ip_input.setPlaceholderText("Meeting Address")
            self.ip_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2b2b2b;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: white;
                    min-width: 250px;
                }
                QLineEdit:focus { border-color: #0d6efd; }
            """)
            
            self.btn_connect = QPushButton("Join Now")
            self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_connect.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #059669; }
            """)
            self.btn_connect.clicked.connect(self.start_client)
            
            tb_layout.addWidget(self.ip_input)
            tb_layout.addWidget(self.btn_connect)

        # End Call Button
        self.btn_stop = QPushButton("Leave Meeting")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_connection)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb2d3b; }
        """)
        tb_layout.addWidget(self.btn_stop)

        self.layout.addWidget(toolbar)

        # -- Main Content Area (Grid for "Group" feel) --
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #121212;")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # We will make them equal size to look like a 1:1 meeting in a grid
        # Local Video
        self.local_container = self.create_video_frame("You")
        self.local_video_label = self.local_container.findChild(QLabel, "video_label")
        
        # Remote Video
        # We label it "Remote User" or "Team Member"
        self.remote_container = self.create_video_frame("Team Member")
        self.remote_video_label = self.remote_container.findChild(QLabel, "video_label")

        content_layout.addWidget(self.local_container)
        content_layout.addWidget(self.remote_container)
        
        # Initial State: Hide remote until connected
        self.remote_container.setVisible(False)
        
        self.layout.addWidget(content_area)

    def create_video_frame(self, label_text):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #000;
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0,0,0,0)
        
        # Video Area
        vid_label = QLabel()
        vid_label.setObjectName("video_label")
        vid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vid_label.setStyleSheet("background-color: black; border-radius: 12px;")
        # Fix for growing window: Ignore size policy so it scales down too
        vid_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
        # Overlay Label (Bottom Left name tag)
        name_bar = QFrame()
        name_bar.setFixedHeight(40)
        name_bar.setStyleSheet("background-color: transparent;")
        nb_layout = QHBoxLayout(name_bar)
        nb_layout.setContentsMargins(15, 0, 15, 10)
        
        name_tag = QLabel(label_text)
        name_tag.setStyleSheet("""
            background-color: rgba(0,0,0,0.6);
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 13px;
        """)
        nb_layout.addWidget(name_tag)
        nb_layout.addStretch()

        layout.addWidget(vid_label)
        layout.addWidget(name_bar) 
        
        return frame

    def update_local_frame(self):
        if self.camera:
            frame = self.camera.get_frame()
            if frame is not None:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                q_img = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
                
                # Get size of container
                w = self.local_video_label.width()
                h = self.local_video_label.height()
                if w > 0 and h > 0:
                    # Use KeepAspectRatio to avoid pushing boundaries excessively if aspect ratio mismatches
                    self.local_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio))

    def update_remote_frame(self, q_img):
        w = self.remote_video_label.width()
        h = self.remote_video_label.height()
        if w > 0 and h > 0:
            self.remote_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio))

    def start_host(self):
        # Always use 8000
        port = 8000
        self.status_badge.setText("LIVE ●")
        self.status_badge.setStyleSheet("background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;")
        self.lbl_title.setText("Meeting in Progress")
        
        self.connection_manager.start_host(port)

    def start_client(self):
        addr = self.ip_input.text().strip()
        # Default port 8000 if not specified (though logic handles split)
        port_str = "8000"
        
        if not addr:
             QMessageBox.warning(self, "Input Error", "Meeting Address is required.")
             return

        if "://" not in addr:
             if "ngrok" in addr:
                 uri = f"wss://{addr}"
             else:
                 uri = f"ws://{addr}:{port_str}"
        else:
             if addr.startswith("https://"):
                 uri = addr.replace("https://", "wss://", 1)
             elif addr.startswith("http://"):
                 uri = addr.replace("http://", "ws://", 1)
             else:
                 uri = addr
             
        self.status_badge.setText("Connecting...")
        self.status_badge.setStyleSheet("background-color: #ffc107; color: black; padding: 4px 12px; border-radius: 12px; font-weight: bold;")
        self.btn_connect.setEnabled(False)
        self.connection_manager.start_client(uri)

    def stop_connection(self):
        self.connection_manager.stop_connection()
        self.call_ended.emit()

    def on_connected(self):
        self.status_badge.setText("CONNECTED")
        self.status_badge.setStyleSheet("background-color: #198754; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;")
        self.remote_container.setVisible(True) # Show remote video
        
        if self.mode == "CLIENT":
            self.lbl_title.setText("Connected to Meeting")
            self.btn_connect.setVisible(False)
            self.ip_input.setVisible(False)

    def on_disconnected(self):
        self.status_badge.setText("DISCONNECTED")
        self.status_badge.setStyleSheet("background-color: #6c757d; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;")
        self.remote_video_label.clear()
        self.remote_container.setVisible(False) # Hide remote video
        
        if self.mode == "CLIENT":
            self.btn_connect.setEnabled(True)
            self.btn_connect.setVisible(True)
            self.ip_input.setVisible(True)

    def on_error(self, msg):
        self.status_badge.setText("ERROR")
        self.status_badge.setStyleSheet("background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;")
        QMessageBox.warning(self, "Connection Error", msg)
        self.on_disconnected()

    def cleanup(self):
        self.timer.stop()
        self.connection_manager.stop_connection()
        if self.camera:
            self.camera.release()
