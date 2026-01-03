import socket
import threading
import struct
import time
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import utils

class ConnectionManager(QObject):
    """
    Manages the P2P connection, including hosting, connecting,
    and handling the send/receive threads.
    """
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    new_frame_received = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.sock = None
        self.server_sock = None
        self.send_thread = None
        self.recv_thread = None
        self.running = False
        self.video_camera = None

    def set_camera(self, camera):
        self.video_camera = camera

    def start_host(self, port):
        """
        Starts the socket server and waits for a client connection.
        Runs in a separate thread to avoid blocking UI.
        """
        threading.Thread(target=self._host_connection, args=(port,), daemon=True).start()

    def _host_connection(self, port):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(('0.0.0.0', port))
            self.server_sock.listen(1)
            
            # Accept only one connection
            self.sock, addr = self.server_sock.accept()
            self._start_streaming()
            
        except Exception as e:
            self.error.emit(f"Host Error: {e}")
            self.stop_connection()

    def start_client(self, ip, port):
        """
        Connects to a host.
        Runs in a separate thread to avoid blocking UI.
        """
        threading.Thread(target=self._client_connection, args=(ip, port), daemon=True).start()

    def _client_connection(self, ip, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self._start_streaming()
        except Exception as e:
            self.error.emit(f"Client Error: {e}")
            self.stop_connection()

    def _start_streaming(self):
        self.running = True
        self.connected.emit()

        # Start Send Thread
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()

        # Start Receive Thread
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _send_loop(self):
        while self.running and self.sock:
            try:
                frame = self.video_camera.get_frame()
                if frame is not None:
                    # Encode frame
                    jpeg_bytes = utils.encode_frame(frame)
                    
                    # Prepare header (4 bytes length, big-endian)
                    length = len(jpeg_bytes)
                    header = struct.pack('!I', length)
                    
                    # Send Header + Data
                    utils.send_all(self.sock, header + jpeg_bytes)
                
                # Limit FPS to ~15
                time.sleep(0.066)
            except Exception as e:
                # print(f"Send Error: {e}")
                self.stop_connection()
                break

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                # Read 4-byte header
                header = utils.recv_all(self.sock, 4)
                if not header:
                    break
                
                # Unpack length
                length = struct.unpack('!I', header)[0]
                
                # Read frame data
                frame_data = utils.recv_all(self.sock, length)
                if not frame_data:
                    break
                    
                # Decode frame
                frame = utils.decode_frame(frame_data)
                
                # Convert to QImage for PyQt
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                # OpenCV is BGR, PyQt needs RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                
                self.new_frame_received.emit(q_img)
                
            except Exception as e:
                # print(f"Recv Error: {e}")
                self.stop_connection()
                break
        
        # If loop exits, disconnect
        if self.running:
            self.stop_connection()

    def stop_connection(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
            self.server_sock = None
            
        self.disconnected.emit()
