import cv2

class VideoCamera:
    """
    Handles video capture from the webcam using OpenCV.
    """
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError("Could not open video source")
        
        # Set resolution to 640x480
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame(self):
        """
        Reads a frame from the camera, resizing if necessary.
        Returns the raw frame (numpy array) or None if failed.
        """
        if not self.cap.isOpened():
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        # Ensure frame is resized to standard size
        frame = cv2.resize(frame, (640, 480))
        return frame

    def release(self):
        """
        Releases the camera resource.
        """
        if self.cap.isOpened():
            self.cap.release()
