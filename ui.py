import sys
import cv2
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap

import video
import network

class VideoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P2P Video Call Demo")
        self.setGeometry(100, 100, 1000, 600)

        # Initialize core components
        try:
            self.camera = video.VideoCamera()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not access camera: {e}")
            sys.exit(1)
            
        self.connection_manager = network.ConnectionManager()
        self.connection_manager.set_camera(self.camera)

        # Setup UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Top Controls
        self.controls_layout = QHBoxLayout()
        
        self.ip_input = QLineEdit("c0aaeec3f161.ngrok-free.app")
        self.ip_input.setPlaceholderText("Host Address (IP or URL)")
        self.ip_input.setFixedWidth(200)
        
        self.port_input = QLineEdit("9999")
        self.port_input.setPlaceholderText("Port")
        self.port_input.setFixedWidth(60)

        self.btn_host = QPushButton("Start as Host")
        self.btn_host.clicked.connect(self.start_host)

        self.btn_connect = QPushButton("Connect Check")
        self.btn_connect.clicked.connect(self.start_client)
        self.btn_connect.setText("Connect")
        
        self.btn_stop = QPushButton("End Call")
        self.btn_stop.clicked.connect(self.stop_connection)
        self.btn_stop.setEnabled(False)

        self.controls_layout.addWidget(QLabel("Addr:"))
        self.controls_layout.addWidget(self.ip_input)
        self.controls_layout.addWidget(QLabel("Port:"))
        self.controls_layout.addWidget(self.port_input)
        self.controls_layout.addWidget(self.btn_host)
        self.controls_layout.addWidget(self.btn_connect)
        self.controls_layout.addWidget(self.btn_stop)
        
        self.layout.addLayout(self.controls_layout)

        # Video Display Area
        self.video_layout = QHBoxLayout()
        
        # Local Video
        self.local_video_label = QLabel("Local Video")
        self.local_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.local_video_label.setStyleSheet("border: 1px solid black; background-color: #eee;")
        self.local_video_label.setFixedSize(480, 360)
        
        # Remote Video
        self.remote_video_label = QLabel("Remote Video")
        self.remote_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remote_video_label.setStyleSheet("border: 1px solid black; background-color: #333; color: white;")
        self.remote_video_label.setFixedSize(480, 360)

        self.video_layout.addWidget(self.local_video_label)
        self.video_layout.addWidget(self.remote_video_label)
        
        self.layout.addLayout(self.video_layout)

        # Status Bar
        self.status_label = QLabel("Status: Idle")
        self.layout.addWidget(self.status_label)

        # Signals
        self.connection_manager.connected.connect(self.on_connected)
        self.connection_manager.disconnected.connect(self.on_disconnected)
        self.connection_manager.error.connect(self.on_error)
        self.connection_manager.new_frame_received.connect(self.update_remote_frame)

        # Timer for local video preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_local_frame)
        self.timer.start(33) # ~30 FPS for local preview

    def update_local_frame(self):
        frame = self.camera.get_frame()
        if frame is not None:
            # Convert to QPixmap for display
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
            self.local_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(480, 360, Qt.AspectRatioMode.KeepAspectRatio))

    def update_remote_frame(self, q_img):
        self.remote_video_label.setPixmap(QPixmap.fromImage(q_img).scaled(480, 360, Qt.AspectRatioMode.KeepAspectRatio))

    def start_host(self):
        port_str = self.port_input.text()
        if not port_str.isdigit():
            QMessageBox.warning(self, "Input Error", "Port must be a number.")
            return
            
        port = int(port_str)
        self.status_label.setText(f"Status: Listening on port {port}...")
        self.set_ui_connected(False) # Disable connect buttons
        self.connection_manager.start_host(port)

    def start_client(self):
        addr = self.ip_input.text().strip()
        port_str = self.port_input.text()
        
        if not addr:
             QMessageBox.warning(self, "Input Error", "Address is required.")
             return

        # Construct WebSocket URI
        # Heuristic: if it looks like an ngrok address (no periods or just alphanumeric), or user forgot protocol
        if "://" not in addr:
             # If port is 443 or user implies secure, default to wss://, else ws://
             if "ngrok" in addr:
                 uri = f"wss://{addr}"
             else:
                 uri = f"ws://{addr}:{port_str}"
        else:
             # Auto-convert http->ws and https->wss
             if addr.startswith("https://"):
                 uri = addr.replace("https://", "wss://", 1)
             elif addr.startswith("http://"):
                 uri = addr.replace("http://", "ws://", 1)
             else:
                 uri = addr
             
        self.status_label.setText(f"Status: Connecting to {uri}...")
        self.set_ui_connected(False)
        self.connection_manager.start_client(uri)

    def stop_connection(self):
        self.connection_manager.stop_connection()

    def on_connected(self):
        self.status_label.setText("Status: CONNECTED")
        self.set_ui_connected(True)

    def on_disconnected(self):
        self.status_label.setText("Status: Disconnected")
        self.remote_video_label.clear()
        self.remote_video_label.setText("Remote Video")
        self.set_ui_connected(False)
        self.btn_host.setEnabled(True)
        self.btn_connect.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def on_error(self, msg):
        self.status_label.setText(f"Status: Error - {msg}")
        QMessageBox.warning(self, "Connection Error", msg)
        self.on_disconnected()

    def set_ui_connected(self, connected):
        """
        Updates button states based on connection status.
        'connected' is True if a call is effectively active (streaming), which enables 'End Call'.
        During 'connecting' or 'listening', we disable start buttons but might not enable 'End Call' fully yet 
        or we treat it differently. Here we simplify:
        If we are trying to connect/host, we disable Host/Connect buttons.
        If we are actually connected, we enable End Call.
        """
        if connected:
            self.btn_host.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            # This state is tricky because 'start_host' disables them too.
            # We handle re-enabling in on_disconnected.
            pass

    def closeEvent(self, event):
        self.connection_manager.stop_connection()
        self.camera.release()
        event.accept()
