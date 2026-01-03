import cv2
import numpy as np

def encode_frame(frame, quality=60):
    """
    Encodes a raw frame to JPEG format (bytes).
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
    return jpeg.tobytes()

def decode_frame(frame_bytes):
    """
    Decodes JPEG bytes back to a raw frame.
    """
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame

# Framing helpers (send_all, recv_all) are NOT needed for WebSockets
# as WebSockets handles message boundaries automatically.
