import cv2
import numpy as np
import time
import threading

class CameraModule:
    def __init__(self):
        self.camera = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        
        # Initialize the camera
        self.initialize_camera()
        
    def initialize_camera(self):
        """Initialize the Raspberry Pi camera"""
        try:
            # Try to access the camera
            self.camera = cv2.VideoCapture(0)  # Use camera index 0
            
            # Check if camera opened successfully
            if not self.camera.isOpened():
                print("Error: Could not open camera.")
                return False
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Start capturing in a separate thread
            self.running = True
            self.capture_thread = threading.Thread(target=self.capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Camera initialization error: {str(e)}")
            return False
    
    def capture_loop(self):
        """Continuously capture frames in a background thread"""
        while self.running:
            ret, frame = self.camera.read()
            if ret:
                with self.lock:
                    self.frame = frame
            time.sleep(0.03)  # ~30fps
    
    def get_frame(self):
        """Get the latest frame from the camera"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def take_photo(self):
        """Take a high-quality photo"""
        # For a real implementation, you might want to:
        # 1. Temporarily stop the capture loop
        # 2. Set higher resolution
        # 3. Take a photo
        # 4. Reset resolution
        # 5. Resume capture loop
        return self.get_frame()
    
    def release(self):
        """Release the camera resources"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        
        if self.camera:
            self.camera.release()