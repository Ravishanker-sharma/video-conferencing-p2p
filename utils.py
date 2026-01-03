import cv2
import struct
import numpy as np

def encode_frame(frame, quality=60):
    """
    Encodes a raw frame to JPEG format.
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
    return jpeg.tobytes()

def decode_frame(frame_bytes):
    """
    Decodes a JPEG byte stream back to a raw frame.
    """
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame

def send_all(sock, data):
    """
    Helper to ensure all bytes are sent over the socket.
    """
    sock.sendall(data)

def recv_all(sock, count):
    """
    Helper to ensure exactly `count` bytes are received.
    """
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf
