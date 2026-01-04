import sys
import cv2
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox)
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
        
        # Host Inputs (Ports)
        self.host_layout = QVBoxLayout()
        self.video_port_input = QLineEdit("9000")
        self.video_port_input.setPlaceholderText("Video Port")
        self.audio_port_input = QLineEdit("9001")
        self.audio_port_input.setPlaceholderText("Audio Port")
        self.host_layout.addWidget(QLabel("Host Ports (Video / Audio):"))
        self.host_layout.addWidget(self.video_port_input)
        self.host_layout.addWidget(self.audio_port_input)

        # Client Inputs (URIs)
        self.client_layout = QVBoxLayout()
        self.video_uri_input = QLineEdit("ws://localhost:9000")
        self.video_uri_input.setPlaceholderText("Video URI (ws://...)")
        self.audio_uri_input = QLineEdit("ws://localhost:9001")
        self.audio_uri_input.setPlaceholderText("Audio URI (ws://...)")
        self.client_layout.addWidget(QLabel("Client URIs (Video / Audio):"))
        self.client_layout.addWidget(self.video_uri_input)
        self.client_layout.addWidget(self.audio_uri_input)

        self.btn_host = QPushButton("Start as Host")
        self.btn_host.clicked.connect(self.start_host)

        self.btn_connect = QPushButton("Connect Check")
        self.btn_connect.clicked.connect(self.start_client)
        self.btn_connect.setText("Connect")
        
        self.btn_stop = QPushButton("End Call")
        self.btn_stop.clicked.connect(self.stop_connection)
        self.btn_stop.setEnabled(False)

        self.check_mute_mic = QCheckBox("Mute Mic")
        self.check_mute_mic.toggled.connect(self.toggle_mic)
        
        self.check_mute_speaker = QCheckBox("Mute Speaker")
        self.check_mute_speaker.toggled.connect(self.toggle_speaker)

        self.controls_layout.addLayout(self.host_layout)
        self.controls_layout.addWidget(self.btn_host)
        
        # Spacer
        self.controls_layout.addSpacing(20)
        
        self.controls_layout.addLayout(self.client_layout)
        self.controls_layout.addWidget(self.btn_connect)
        
        self.controls_layout.addWidget(self.btn_stop)
        self.controls_layout.addWidget(self.check_mute_mic)
        self.controls_layout.addWidget(self.check_mute_speaker)
        
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
        v_port_str = self.video_port_input.text()
        a_port_str = self.audio_port_input.text()
        
        if not v_port_str.isdigit() or not a_port_str.isdigit():
            QMessageBox.warning(self, "Input Error", "Ports must be numbers.")
            return

        v_port = int(v_port_str)
        a_port = int(a_port_str)
        
        self.status_label.setText(f"Status: Hosting on Ports {v_port} (Video) & {a_port} (Audio)...")
        self.set_ui_connected(False) 
        self.connection_manager.start_host(v_port, a_port)

    def start_client(self):
        v_uri = self.video_uri_input.text().strip()
        a_uri = self.audio_uri_input.text().strip()

        if not v_uri or not a_uri:
             QMessageBox.warning(self, "Input Error", "Both URIs are required.")
             return
             
        # Helper to fix common protocol omissions
        def fix_uri(u):
            if "://" not in u:
                return "ws://" + u
            if u.startswith("https://"): return u.replace("https://", "wss://", 1)
            if u.startswith("http://"): return u.replace("http://", "ws://", 1)
            return u

        v_uri = fix_uri(v_uri)
        a_uri = fix_uri(a_uri)

        self.status_label.setText(f"Status: Connecting...")
        self.set_ui_connected(False)
        self.connection_manager.start_client(v_uri, a_uri)

    def stop_connection(self):
        self.connection_manager.stop_connection()

    def toggle_mic(self, checked):
        # We need to expose this in ConnectionManager/AudioManager
        # For now, simplistic approach: set a flag in audio manager if accessible, 
        # or handle in ConnectionManager on_audio_input.
        # But wait, audio_manager is private in ConnectionManager.
        # Let's add a method to ConnectionManager.
        self.connection_manager.set_mic_mute(checked)

    def toggle_speaker(self, checked):
        self.connection_manager.set_speaker_mute(checked)

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
