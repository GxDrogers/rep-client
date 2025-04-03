import cv2
import socket
import threading
import pyaudio
import wave
import struct
import time
import os
import subprocess
import json
import numpy as np
from PIL import Image
import io

# Configuration
SERVER_IP = '192.168.83.133'  # Change to your server's IP address
SERVER_PORT_VIDEO = 8000
SERVER_PORT_AUDIO = 8001
SERVER_PORT_COMMANDS = 8002
SERVER_PORT_RESPONSE = 8003

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 10
AUDIO_CHUNK = 1024
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE = 16000
RECORDING_SECONDS = 5  # Duration to record when activated

class AttendanceClient:
    def __init__(self):
        self.camera = None
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.should_exit = False
        self.response_thread = None
        self.speaking = False
        
    def setup(self):
        """Set up the camera and connections"""
        print("Setting up client...")
        
        # Initialize camera
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, FPS)
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
            
        # Start response listener thread
        self.response_thread = threading.Thread(target=self.listen_for_responses)
        self.response_thread.daemon = True
        self.response_thread.start()
        
        return True
        
    def compress_frame(self, frame):
        """Compress the frame to JPEG to reduce size"""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()
        
    def send_video_frame(self, frame):
        """Send a video frame to the server"""
        try:
            # Compress the frame
            compressed_frame = self.compress_frame(frame)
            
            # Create a socket and connect to server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_IP, SERVER_PORT_VIDEO))
                
                # Send frame size first, then the frame
                size = len(compressed_frame)
                sock.sendall(struct.pack('>I', size))
                sock.sendall(compressed_frame)
                
        except ConnectionRefusedError:
            print("Could not connect to server. Make sure server is running.")
        except Exception as e:
            print(f"Error sending video frame: {e}")
    
    def record_audio(self):
        """Record audio from microphone and send to server"""
        self.is_recording = True
        
        # Open audio stream
        stream = self.audio.open(
            format=AUDIO_FORMAT,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RATE,
            input=True,
            frames_per_buffer=AUDIO_CHUNK
        )
        
        print("Recording...")
        
        frames = []
        for i in range(0, int(AUDIO_RATE / AUDIO_CHUNK * RECORDING_SECONDS)):
            if not self.is_recording:
                break
            data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
            frames.append(data)
            
        print("Recording complete")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save audio to a temporary file
        temp_file = "temp_audio.wav"
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(AUDIO_CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(AUDIO_FORMAT))
        wf.setframerate(AUDIO_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Send audio file to server
        self.send_audio_file(temp_file)
        
        # Clean up
        os.remove(temp_file)
        self.is_recording = False
    
    def send_audio_file(self, file_path):
        """Send audio file to server"""
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_IP, SERVER_PORT_AUDIO))
                
                # Send audio size first, then the audio data
                size = len(audio_data)
                sock.sendall(struct.pack('>I', size))
                sock.sendall(audio_data)
                
            print("Audio sent to server")
            
        except Exception as e:
            print(f"Error sending audio: {e}")
    
    def send_command(self, command):
        """Send a command to the server"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_IP, SERVER_PORT_COMMANDS))
                sock.sendall(command.encode('utf-8'))
        except Exception as e:
            print(f"Error sending command: {e}")
    
    def listen_for_responses(self):
        """Listen for responses from the server"""
        while not self.should_exit:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)  # 1 second timeout
                    sock.bind(('0.0.0.0', SERVER_PORT_RESPONSE))
                    sock.listen(1)
                    
                    while not self.should_exit:
                        try:
                            conn, addr = sock.accept()
                            with conn:
                                # Get message size
                                size_data = conn.recv(4)
                                if not size_data:
                                    continue
                                    
                                size = struct.unpack('>I', size_data)[0]
                                data = b''
                                
                                # Receive data
                                while len(data) < size:
                                    packet = conn.recv(size - len(data))
                                    if not packet:
                                        break
                                    data += packet
                                
                                if len(data) == size:
                                    # Process response
                                    response = json.loads(data.decode('utf-8'))
                                    if response['type'] == 'text':
                                        self.speak_response(response['message'])
                                    elif response['type'] == 'attendance':
                                        print(f"Attendance recorded: {response['message']}")
                                    
                        except socket.timeout:
                            continue
                            
            except Exception as e:
                print(f"Error in response listener: {e}")
                time.sleep(5)  # Wait before trying to reconnect
    
    def speak_response(self, text):
        """Use text-to-speech to speak the response"""
        if self.speaking:
            return
            
        self.speaking = True
        try:
            # Using espeak for simplicity
            subprocess.run(['espeak', text])
        except Exception as e:
            print(f"Error speaking response: {e}")
        finally:
            self.speaking = False
    
    def run(self):
        """Main client loop"""
        if not self.setup():
            print("Failed to set up client")
            return
            
        print("Client running. Press 'q' to quit, 'r' to record audio.")
        
        last_frame_time = time.time()
        frame_interval = 1.0 / FPS
        
        try:
            while not self.should_exit:
                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Send frame at desired FPS
                current_time = time.time()
                if current_time - last_frame_time >= frame_interval:
                    self.send_video_frame(frame)
                    last_frame_time = current_time
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.should_exit = True
                elif key == ord('r') and not self.is_recording:
                    threading.Thread(target=self.record_audio).start()
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
        finally:
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
            self.audio.terminate()
            print("Client shutdown complete")

if __name__ == "__main__":
    client = AttendanceClient()
    client.run()
