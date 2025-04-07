from picamera2 import Picamera2
import socket
import threading
import time
import cv2
import numpy as np
import io

class CameraStream:
    def __init__(self, server_ip='192.168.1.100', server_port=8000):
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False
        self.picam2 = None
        
    def initialize(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
        self.picam2.configure(config)
        
    def start(self):
        if self.picam2 is None:
            self.initialize()
            
        self.picam2.start()
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.picam2:
            self.picam2.stop()
            
    def _stream_loop(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_ip, self.server_port))
        
        try:
            while self.running:
                frame = self.picam2.capture_array()
                # Convert to jpg for efficient streaming
                _, buffer = cv2.imencode('.jpg', frame)
                size = len(buffer)
                # Send size followed by frame data
                client_socket.sendall(size.to_bytes(4, byteorder='big'))
                client_socket.sendall(buffer)
                time.sleep(0.03)  # ~30 FPS
        finally:
            client_socket.close()