import sys
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QFrame,
                             QSizePolicy, QStackedLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

import video
import network
from chat_widget import ChatWidget

class VideoCallWidget(QWidget):
    call_ended = pyqtSignal()

    def __init__(self, mode="HOST"):
        super().__init__()
        self.mode = mode 
        
        # UI State
        self.is_mic_on = True
        self.is_camera_on = True
        self.is_cc_on = False
        
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
        self.connection_manager.chat_message_received.connect(self.on_chat_received)

        # Timer for local video preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_local_frame)
        self.timer.start(33) 

        # Auto-start hosting if in host mode
        if self.mode == "HOST":
            QTimer.singleShot(500, self.start_host)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # -- Middle Area (Video + Chat) --
        # We use a HBox. Chat is initially hidden (width 0 or hidden widget)
        middle_area = QWidget()
        middle_layout = QHBoxLayout(middle_area)
        middle_layout.setContentsMargins(0,0,0,0)
        middle_layout.setSpacing(0)
        
        # Video Area
        video_area = QWidget()
        video_area.setStyleSheet("background-color: #121212;")
        video_layout = QHBoxLayout(video_area)
        video_layout.setContentsMargins(20, 20, 20, 20)
        video_layout.setSpacing(20)

        # Local Video
        self.local_container = self.create_video_frame("You")
        self.local_video_label = self.local_container.findChild(QLabel, "video_label")
        
        # Remote Video
        self.remote_container = self.create_video_frame("Team Member")
        self.remote_video_label = self.remote_container.findChild(QLabel, "video_label")

        video_layout.addWidget(self.local_container)
        video_layout.addWidget(self.remote_container)
        self.remote_container.setVisible(False)
        
        # Chat Widget
        self.chat_widget = ChatWidget()
        self.chat_widget.hide() # Hidden by default
        self.chat_widget.message_sent.connect(self.send_chat)

        middle_layout.addWidget(video_area)
        middle_layout.addWidget(self.chat_widget)
        
        self.main_layout.addWidget(middle_area)

        # -- Bottom Control Bar --
        self.create_bottom_bar()
        self.main_layout.addWidget(self.bottom_bar)
        
        # -- Overlay Info / Input for Client (Floating or Top) --
        # Since we removed the top toolbar, we need a place for "Connecting..." status or Input
        # We can implement a simple overlay dialog or just a top bar that hides given the user request
        # User request didn't explicitly ask to remove the top bar, but "improve meeting page".
        # Let's keep a minimal top connection bar ONLY if Client and not connected.
        
        self.top_connection_bar = QFrame()
        self.top_connection_bar.setFixedHeight(50)
        self.top_connection_bar.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #333;")
        top_layout = QHBoxLayout(self.top_connection_bar)
        
        if self.mode == "CLIENT":
            self.ip_input = QLineEdit("c0aaeec3f161.ngrok-free.app")
            self.ip_input.setPlaceholderText("Meeting Address")
            self.ip_input.setStyleSheet("background-color: #333; color: white; padding: 5px; border-radius: 4px;")
            self.btn_connect = QPushButton("Join")
            self.btn_connect.clicked.connect(self.start_client)
            self.btn_connect.setStyleSheet("background-color: #10b981; color: white; padding: 5px 15px; border-radius: 4px;")
            
            top_layout.addWidget(self.ip_input)
            top_layout.addWidget(self.btn_connect)
        else:
            # Host mode: Hide top bar as per user request
            self.top_connection_bar.setVisible(False)
            
        top_layout.addStretch()
        # Insert at top
        self.main_layout.insertWidget(0, self.top_connection_bar)


    def create_bottom_bar(self):
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(80)
        self.bottom_bar.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #333;")
        
        layout = QHBoxLayout(self.bottom_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # Left: Info
        self.lbl_time = QLabel("10:00 AM") # Dummy time
        self.lbl_time.setStyleSheet("color: white; font-weight: bold;")
        self.lbl_id = QLabel("|  Team Meeting")
        self.lbl_id.setStyleSheet("color: #aaa;")
        
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.lbl_id)
        layout.addStretch()
        
        # Center: Controls
        self.btn_mic = self.create_control_btn("🎤", "Mute")
        self.btn_mic.clicked.connect(self.toggle_mic)
        
        self.btn_cam = self.create_control_btn("📹", "Stop Video")
        self.btn_cam.clicked.connect(self.toggle_cam)
        
        self.btn_cc = self.create_control_btn("💬", "Captions")
        self.btn_cc.clicked.connect(self.toggle_cc)
        
        self.btn_chat = self.create_control_btn("🗨", "Chat")
        self.btn_chat.clicked.connect(self.toggle_chat)
        
        self.btn_leave = QPushButton("📞")
        self.btn_leave.setFixedSize(60, 40)
        self.btn_leave.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_leave.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover { background-color: #bb2d3b; }
        """)
        self.btn_leave.clicked.connect(self.stop_connection)

        layout.addWidget(self.btn_mic)
        layout.addWidget(self.btn_cam)
        layout.addWidget(self.btn_cc)
        layout.addWidget(self.btn_chat)
        layout.addWidget(self.btn_leave)
        
        layout.addStretch()
        
        # Spacer to balance left side
        # (Could add more icons here)
        spacer = QWidget()
        spacer.setFixedWidth(100)
        layout.addWidget(spacer)

    def create_control_btn(self, icon, tooltip):
        btn = QPushButton(icon)
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3c4043;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 20px;
            }
            QPushButton:hover { background-color: #5f6368; }
            QPushButton:checked { background-color: #8ab4f8; color: #3c4043; }
        """)
        return btn

    def toggle_mic(self):
        self.is_mic_on = not self.is_mic_on
        if self.is_mic_on:
            self.btn_mic.setStyleSheet(self.btn_mic.styleSheet().replace("background-color: #ea4335;", "background-color: #3c4043;"))
            self.btn_mic.setText("🎤")
        else:
            self.btn_mic.setStyleSheet(self.btn_mic.styleSheet().replace("background-color: #3c4043;", "background-color: #ea4335;"))
            self.btn_mic.setText("🚫") # Muted icon

    def toggle_cam(self):
        self.is_camera_on = not self.is_camera_on
        if self.is_camera_on:
            self.btn_cam.setStyleSheet(self.btn_cam.styleSheet().replace("background-color: #ea4335;", "background-color: #3c4043;"))
            self.btn_cam.setText("📹")
            self.local_video_label.setVisible(True)
        else:
            self.btn_cam.setStyleSheet(self.btn_cam.styleSheet().replace("background-color: #3c4043;", "background-color: #ea4335;"))
            self.btn_cam.setText("🚫")
            self.local_video_label.setVisible(False) 
            # Note: We should technically stop sending frames, 
            # but setting visible(False) effectively stops update_local_frame from processing (visuals only)
            # To stop sending: handled in get_frame logic check

    def toggle_cc(self):
        self.is_cc_on = not self.is_cc_on
        if self.is_cc_on:
            self.btn_cc.setStyleSheet(self.btn_cc.styleSheet().replace("background-color: #3c4043;", "background-color: #8ab4f8;").replace("color: white;", "color: black;"))
            QMessageBox.information(self, "Captions", "Captions enabled (Simulation)")
        else:
            self.btn_cc.setStyleSheet(self.btn_cc.styleSheet().replace("background-color: #8ab4f8;", "background-color: #3c4043;").replace("color: black;", "color: white;"))

    def toggle_chat(self):
        if self.chat_widget.isVisible():
            self.chat_widget.hide()
            self.btn_chat.setStyleSheet(self.btn_chat.styleSheet().replace("background-color: #8ab4f8;", "background-color: #3c4043;").replace("color: black;", "color: white;"))
        else:
            self.chat_widget.show()
            self.btn_chat.setStyleSheet(self.btn_chat.styleSheet().replace("background-color: #3c4043;", "background-color: #8ab4f8;").replace("color: white;", "color: black;"))

    def send_chat(self, text):
        self.connection_manager.send_chat_message(text)

    def on_chat_received(self, text):
        if not self.chat_widget.isVisible():
            self.toggle_chat() # Auto open chat
        self.chat_widget.add_message(text, is_me=False)

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
        vid_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
        # Bottom Name Tag
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
        if not self.is_camera_on:
             return
        if not self.local_video_label.isVisible():
             return

        if self.camera:
            frame = self.camera.get_frame()
            if frame is not None:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                q_img = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
                
                w = self.local_video_label.width()
                h = self.local_video_label.height()
                if w < 10 or h < 10: return
                
                self.local_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio))

    def update_remote_frame(self, q_img):
        if not self.remote_container.isVisible():
            return
            
        w = self.remote_video_label.width()
        h = self.remote_video_label.height()
        if w < 10 or h < 10: return

        self.remote_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio))

    def start_host(self):
        port = 8000
        # self.top_connection_bar.setVisible(True) # Hidden for clean UI
        self.connection_manager.start_host(port)

    def start_client(self):
        addr = self.ip_input.text().strip()
        port_str = "8000"
        
        if not addr: return
        
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
             
        self.btn_connect.setText("Connect...")
        self.btn_connect.setEnabled(False)
        self.connection_manager.start_client(uri)

    def stop_connection(self):
        self.connection_manager.stop_connection()
        self.call_ended.emit()

    def on_connected(self):
        self.remote_container.setVisible(True)
        if self.mode == "CLIENT":
            self.top_connection_bar.setVisible(False) # Hide input when connected

    def on_disconnected(self):
        self.remote_video_label.clear()
        self.remote_container.setVisible(False)
        
        if self.mode == "CLIENT":
            self.btn_connect.setText("Join")
            self.btn_connect.setEnabled(True)
            self.top_connection_bar.setVisible(True)

    def on_error(self, msg):
        QMessageBox.warning(self, "Connection Error", msg)
        self.on_disconnected()

    def cleanup(self):
        self.timer.stop()
        self.connection_manager.stop_connection()
        if self.camera:
            self.camera.release()
