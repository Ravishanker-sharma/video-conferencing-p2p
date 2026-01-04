import asyncio
import threading
import websockets
import cv2
import time
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage
import utils
import audio

class ConnectionManager(QObject):
    """
    Manages the P2P connection using WebSockets.
    Runs an asyncio loop in a separate thread.
    """
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    new_frame_received = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.loop = None
        self.thread = None
        self.running = False
        self.video_camera = None
        self.websocket = None
        self.audio_manager = audio.AudioManager()
        self.audio_queue = asyncio.Queue()


    def set_camera(self, camera):
        self.video_camera = camera

    def set_mic_mute(self, muted):
        self.audio_manager.is_mic_muted = muted

    def set_speaker_mute(self, muted):
        self.audio_manager.is_speaker_muted = muted
    
    def start_audio(self):
        # Start audio streams and hook up callback
        self.audio_manager.start_streams(self.on_audio_input)

    def on_audio_input(self, data):
        if self.loop and self.running:
             # Thread-safe put into async queue
             self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, data)

    def start_host(self, port):
        """
        Starts a WebSocket server on localhost:port.
        """
        self.running = True
        self.thread = threading.Thread(target=self._run_server_loop, args=(port,), daemon=True)
        self.thread.start()

    def start_client(self, uri):
        """
        Connects to a WebSocket server at uri.
        """
        self.running = True
        self.thread = threading.Thread(target=self._run_client_loop, args=(uri,), daemon=True)
        self.thread.start()

    def stop_connection(self):
        self.running = False
        self.audio_manager.stop_streams()
        # The loop will check 'running' flag or we can cancel tasks,
        # but for simplicity we rely on the loops checking self.running or breaking on close.
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        self.disconnected.emit()

    def _run_server_loop(self, port):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._serve_forever(port))
        except Exception as e:
            self.error.emit(f"Server Error: {e}")
        finally:
            self.loop.close()

    async def _serve_forever(self, port):
        # We use 'async with' to manage the server lifecycle properly
        async with websockets.serve(self._handle_connection, "0.0.0.0", port):
            # Keep the server running until cancelled
            await asyncio.Future()


    async def _handle_connection(self, websocket):
        self.websocket = websocket
        self.connected.emit()
        
        # Start sender task
        sender_task = asyncio.create_task(self._sender(websocket))
        
        # Receiver loop (this coroutine acts as receiver)
        try:
            async for message in websocket:
                if not self.running:
                    break
                self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            self.error.emit(f"Receive Error: {e}")
        finally:
            self.running = False
            sender_task.cancel()
            self.disconnected.emit()

    def _run_client_loop(self, uri):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._client_handler(uri))
        self.loop.close()

    async def _client_handler(self, uri):
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connected.emit()
                
                # Start sender task
                sender_task = asyncio.create_task(self._sender(websocket))
                
                # Receiver loop
                try:
                    async for message in websocket:
                        if not self.running:
                            break
                        self._process_message(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    sender_task.cancel()

        except Exception as e:
            self.error.emit(f"Client Connection Error: {e}")
        finally:
            self.running = False
            self.disconnected.emit()

    async def _sender(self, websocket):
        """
        Continuously captures and sends frames and audio.
        """
        # Start audio hardware
        self.start_audio()

        while self.running:
            try:
                # 1. Video Frame
                # We throttle video to ~15 FPS
                # But we can't block audio. So we should probably decouple them or run them concurrently.
                # Simplest concurrency: check both in a loop with small sleep, or use separate tasks.
                # For simplicity in this single-loop structure:
                
                # Check video
                frame = self.video_camera.get_frame()
                if frame is not None:
                    jpeg_bytes = utils.encode_frame(frame)
                    # Prefix 'V' for video
                    await websocket.send(b'V' + jpeg_bytes)

                # Check audio queue - flush all available
                while not self.audio_queue.empty():
                    audio_data = await self.audio_queue.get()
                    # Prefix 'A' for audio
                    await websocket.send(b'A' + audio_data)
                
                # Sleep a bit to control video FPS, but this might add latency to audio if too long.
                # 0.066 is ~15ms, which is fine for audio chunks (usually 20ms+).
                # But to keep audio smooth, we might want a tighter loop or separate task.
                # Let's reduce sleep and use a timer for video capture if needed, 
                # or just accept that we check video every loop.
                # Better: Wait small amount, enabling high reactive loop
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # print(f"Send Error: {e}")
                break

    def _process_message(self, message):
        """
        Decodes a received message and routes it.
        """
        try:
            msg_type = message[0:1] # First byte
            payload = message[1:]

            if msg_type == b'V':
                self._process_frame(payload)
            elif msg_type == b'A':
                self.audio_manager.write_audio(payload)
        except Exception as e:
            print(f"Message Processing Error: {e}")

    def _process_frame(self, frame_data):
        """
        Decodes a received frame and emits it.
        """
        try:
            frame = utils.decode_frame(frame_data)
            if frame is None:
                return

            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # MUST copy() the image, because QImage(data, ...) uses the buffer directly.
            # If we don't copy, 'frame_rgb' is GC'd after this function ends, causing a Segfault.
            q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
            
            # emit must be thread-safe (signals are)
            self.new_frame_received.emit(q_img)
        except Exception as e:
            print(f"Frame Decode Error: {e}")
