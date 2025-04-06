import cv2
import socket
import pickle
import struct
import time

class Camera:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.camera = None
        self.client_socket = None
        
    def initialize(self):
        # Initialize camera (Pi Camera v2)
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Connect to server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.port))
        print(f"Connected to server at {self.server_ip}:{self.port}")
        
    def stream(self):
        if not self.camera or not self.client_socket:
            raise Exception("Camera not initialized")
            
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                    
                # Compress and serialize frame
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                data = pickle.dumps(buffer)
                
                # Send frame size followed by frame data
                message_size = struct.pack("L", len(data))
                self.client_socket.sendall(message_size + data)
                
                # Limit frame rate to reduce bandwidth
                time.sleep(0.04)  # ~25 FPS
                
        except Exception as e:
            print(f"Streaming error: {e}")
        finally:
            self.release()
            
    def release(self):
        if self.camera:
            self.camera.release()
        if self.client_socket:
            self.client_socket.close()