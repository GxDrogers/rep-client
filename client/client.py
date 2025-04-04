import socket
import time
import cv2
import pickle
import numpy as np
import pyaudio
import threading
import os
import subprocess
from gtts import gTTS
import pygame
from io import BytesIO

class AttendanceClient:
    def __init__(self, server_host='192.168.1.100', server_port=9999):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.camera = None
        self.audio = None
        self.audio_stream = None
        self.connected = False
        self.stop_flag = False
        
        # Initialize pygame for audio playback
        pygame.init()
        pygame.mixer.init()
        
        # Audio recording parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.record_seconds = 5
    
    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.connected = False
            return False
    
    def initialize_camera(self):
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("Error: Could not open camera")
                return False
            
            # Set camera resolution to reduce bandwidth
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print("Camera initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
    
    def initialize_audio(self):
        try:
            self.audio = pyaudio.PyAudio()
            print("Audio system initialized")
            return True
        except Exception as e:
            print(f"Error initializing audio: {e}")
            return False
    
    def start_camera_stream(self):
        if not self.connected or not self.camera:
            print("Cannot start camera stream: not connected or camera not initialized")
            return
        
        threading.Thread(target=self._camera_stream_thread, daemon=True).start()
    
    def _camera_stream_thread(self):
        print("Starting camera stream...")
        try:
            while not self.stop_flag and self.connected:
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame")
                    time.sleep(1)
                    continue
                
                # Resize frame to reduce bandwidth
                frame = cv2.resize(frame, (320, 240))
                
                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                jpg_as_bytes = buffer.tobytes()
                
                try:
                    # Send data type indicator ('I' for image)
                    self.socket.sendall(b"I")
                    
                    # Send image size
                    size = len(jpg_as_bytes)
                    size_bytes = size.to_bytes(8, byteorder='big')
                    self.socket.sendall(size_bytes)
                    
                    # Send image data
                    self.socket.sendall(jpg_as_bytes)
                    
                    # Check for recognition response (non-blocking)
                    self.socket.setblocking(0)
                    try:
                        response = self.socket.recv(1024).decode()
                        if response.startswith("R"):
                            names = response[1:].split(",")
                            self.speak_welcome(names)
                    except:
                        pass
                    self.socket.setblocking(1)
                    
                except Exception as e:
                    print(f"Error sending image: {e}")
                    break
                
                time.sleep(0.1)  # Limit to ~10 FPS
        
        except Exception as e:
            print(f"Camera stream error: {e}")
        finally:
            print("Camera stream stopped")
    
    def speak_welcome(self, names):
        name_str = ", ".join(names)
        message = f"Welcome {name_str}. Your attendance has been marked."
        self.speak(message)
    
    def start_listening(self):
        if not self.connected or not self.audio:
            print("Cannot start listening: not connected or audio not initialized")
            return
        
        print("Press ENTER to start recording a voice query...")
        
        def input_thread():
            while not self.stop_flag:
                input()
                if self.stop_flag:
                    break
                print("Recording... Speak now for 5 seconds.")
                self.record_and_send_audio()
                print("Press ENTER to record another query...")
        
        threading.Thread(target=input_thread, daemon=True).start()
    
    def record_and_send_audio(self):
        try:
            self.audio_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("Recording...")
            frames = []
            
            for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
                data = self.audio_stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
            
            print("Finished recording")
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            
            # Combine all audio frames
            audio_data = b''.join(frames)
            
            try:
                # Send data type indicator ('A' for audio)
                self.socket.sendall(b"A")
                
                # Send audio size
                size = len(audio_data)
                size_bytes = size.to_bytes(8, byteorder='big')
                self.socket.sendall(size_bytes)
                
                # Send audio data
                self.socket.sendall(audio_data)
                
                # Wait for response
                response = self.socket.recv(4096).decode()
                if response.startswith("T"):
                    text_response = response[1:]
                    print(f"Server response: {text_response}")
                    self.speak(text_response)
            
            except Exception as e:
                print(f"Error sending audio or receiving response: {e}")
        
        except Exception as e:
            print(f"Error recording audio: {e}")
    
    def speak(self, text):
        try:
            # Create a text-to-speech object
            tts = gTTS(text=text, lang='en')
            
            # Save to a BytesIO object
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            # Play the audio
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        
        except Exception as e:
            print(f"Error speaking: {e}")
    
    def shutdown(self):
        self.stop_flag = True
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.camera:
            self.camera.release()
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        
        if self.audio:
            self.audio.terminate()
        
        pygame.mixer.quit()
        pygame.quit()
        
        print("Client shutdown complete")

def main():
    # Change this to your server's IP address
    SERVER_HOST = "192.168.1.100"  # Replace with your laptop/PC IP address
    SERVER_PORT = 9999

    client = AttendanceClient(server_host=SERVER_HOST, server_port=SERVER_PORT)
    
    try:
        # Initialize hardware
        if not client.initialize_camera():
            print("Failed to initialize camera. Exiting...")
            return
        
        if not client.initialize_audio():
            print("Failed to initialize audio. Exiting...")
            return
        
        # Connect to server
        if not client.connect_to_server():
            print("Failed to connect to server. Exiting...")
            return
        
        # Start camera stream
        client.start_camera_stream()
        
        # Start listening for voice queries
        client.start_listening()
        
        # Keep running until keyboard interrupt
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        client.shutdown()

if __name__ == "__main__":
    main()


    
