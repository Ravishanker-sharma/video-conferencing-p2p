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
    Manages P2P connections using two separate WebSockets (Video & Audio).
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
        self.audio_manager = audio.AudioManager()
        self.audio_queue = asyncio.Queue()

        self.ws_video = None
        self.ws_audio = None

    def set_camera(self, camera):
        self.video_camera = camera

    def set_mic_mute(self, muted):
        self.audio_manager.is_mic_muted = muted

    def set_speaker_mute(self, muted):
        self.audio_manager.is_speaker_muted = muted
    
    def start_audio(self):
        self.audio_manager.start_streams(self.on_audio_input)

    def on_audio_input(self, data):
        if self.loop and self.running:
             self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, data)

    def start_host(self, video_port, audio_port):
        """
        Starts two WebSocket servers.
        """
        self.running = True
        self.thread = threading.Thread(target=self._run_server_loop, args=(video_port, audio_port), daemon=True)
        self.thread.start()

    def start_client(self, video_uri, audio_uri):
        """
        Connects to two WebSocket servers.
        """
        self.running = True
        self.thread = threading.Thread(target=self._run_client_loop, args=(video_uri, audio_uri), daemon=True)
        self.thread.start()

    def stop_connection(self):
        self.running = False
        self.audio_manager.stop_streams()
        
        if self.loop:
            # Try to close sockets
            if self.ws_video:
                asyncio.run_coroutine_threadsafe(self.ws_video.close(), self.loop)
            if self.ws_audio:
                asyncio.run_coroutine_threadsafe(self.ws_audio.close(), self.loop)
        
        self.disconnected.emit()

    # --- Server Logic ---

    def _run_server_loop(self, v_port, a_port):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._serve_forever(v_port, a_port))
        except Exception as e:
            self.error.emit(f"Server Error: {e}")
        finally:
            self.loop.close()

    async def _serve_forever(self, v_port, a_port):
        # We start two servers
        # Note: We need to bind to 0.0.0.0
        async with websockets.serve(self._handle_video_connection, "0.0.0.0", v_port) as server_v, \
                   websockets.serve(self._handle_audio_connection, "0.0.0.0", a_port) as server_a:
            
            # Start sender task (it will wait for connections to appear)
            sender_task = asyncio.create_task(self._sender_loop())
            
            # Run forever
            await asyncio.Future()
            sender_task.cancel()

    async def _handle_video_connection(self, websocket):
        self.ws_video = websocket
        # If we have both, emit connected? Or just emit whenever one connects?
        # Let's emit connected when we get Video (primary)
        self.connected.emit()
        
        try:
            async for message in websocket:
                if not self.running: break
                # Expected: Just raw JPEG bytes (no 'V' prefix needed if ports separate, 
                # but legacy code might have it. Let's assume raw or handle prefix if we want robustness.
                # Since we have separate ports, we can send raw Data.)
                # HOWEVER, to be safe against mixed packets or restarts, let's keep it simple: Raw Data.
                self._process_video_frame(message)
        except:
            pass
        finally:
            self.ws_video = None

    async def _handle_audio_connection(self, websocket):
        self.ws_audio = websocket
        
        try:
            async for message in websocket:
                if not self.running: break
                self.audio_manager.write_audio(message)
        except:
            pass
        finally:
            self.ws_audio = None

    # --- Client Logic ---

    def _run_client_loop(self, v_uri, a_uri):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._client_handler(v_uri, a_uri))
        except Exception as e:
            self.error.emit(f"Client Error: {e}")
        finally:
            self.loop.close()

    async def _client_handler(self, v_uri, a_uri):
        # Connect to both concurrently
        # We use a TaskGroup or gather, but we want to maintain them.
        
        sender_task = asyncio.create_task(self._sender_loop())

        async def connect_video():
            try:
                # Handle ngrok https -> wss conversion if needed, but user might provide wss directly.
                # Let's assume input is valid WSS/WS.
                async with websockets.connect(v_uri) as ws:
                    self.ws_video = ws
                    self.connected.emit()
                    async for message in ws:
                        if not self.running: break
                        self._process_video_frame(message)
            except Exception as e:
                print(f"Video Connect Error: {e}")
            finally:
                self.ws_video = None

        async def connect_audio():
            try:
                async with websockets.connect(a_uri) as ws:
                    self.ws_audio = ws
                    async for message in ws:
                        if not self.running: break
                        self.audio_manager.write_audio(message)
            except Exception as e:
                print(f"Audio Connect Error: {e}")
            finally:
                self.ws_audio = None

        await asyncio.gather(connect_video(), connect_audio())
        sender_task.cancel()
        self.disconnected.emit()

    # --- Sender Logic ---

    async def _sender_loop(self):
        self.start_audio()
        
        while self.running:
            try:
                # Video
                if self.ws_video:
                    frame = self.video_camera.get_frame()
                    if frame is not None:
                         # encode with low quality as requested earlier (5)
                        jpeg_bytes = utils.encode_frame(frame, quality=5)
                        try:
                            await self.ws_video.send(jpeg_bytes)
                        except:
                            pass # Socket might have closed
                
                # Audio
                if self.ws_audio:
                    while not self.audio_queue.empty():
                        audio_data = await self.audio_queue.get()
                        try:
                            await self.ws_audio.send(audio_data)
                        except:
                            pass

                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Sender Loop Error: {e}")
                break

    # --- Processing ---

    def _process_video_frame(self, frame_data):
        try:
            frame = utils.decode_frame(frame_data)
            if frame is None: return

            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
            self.new_frame_received.emit(q_img)
        except Exception:
            pass
