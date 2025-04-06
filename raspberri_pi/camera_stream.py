import numpy as np
from picamera2 import Picamera2

class CameraStream:
    def __init__(self, width=640, height=480):
        self.picam2 = Picamera2()
        self.config = self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            formats={"main": "RGB888"}
        )
        self.picam2.configure(self.config)
        self.picam2.start()
        
    def get_frame(self):
        """Get a frame from the camera"""
        frame = self.picam2.capture_array()
        return frame