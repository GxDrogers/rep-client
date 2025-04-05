# client.py
import cv2
import socket
import pickle
import threading
import pyaudio
import wave
import time
import io
import pygame
import os
import queue
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from PIL import Image, ImageTk
import warnings
warnings.filterwarnings("ignore")

# Initialize SDL for Raspberry Pi
os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ['DISPLAY'] = ':0'

# Configuration
SERVER_IP = '127.0.0.1'  # Change this to your actual server IP
SERVER_PORT = 9999
CAMERA_WIDTH = 320  # Reduced for Raspberry Pi
CAMERA_HEIGHT = 240  # Reduced for Raspberry Pi
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

# Global variables
running = True
audio_queue = queue.Queue()
response_queue = queue.Queue()

class AttendanceClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Attendance System")
        
        # Get screen dimensions
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
        except:
            screen_width = 800
            screen_height = 480
        
        self.root.geometry(f"{screen_width}x{screen_height}")
        
        # Force window to show on top
        try:
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.attributes('-topmost', False)
        except:
            pass
        
        self.style = ttk.Style(theme="darkly")
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)
        
        # Create left frame for video
        self.left_frame = ttk.Frame(main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Create label for displaying camera feed
        self.video_label = ttk.Label(self.left_frame)
        self.video_label.pack(fill="both", expand=True)
        
        # Create right frame for status and controls
        self.right_frame = ttk.Frame(main_frame)
        self.right_frame.pack(side="right", fill="both", expand=False, padx=10, pady=10, ipadx=10)
        
        # Status information
        ttk.Label(self.right_frame, text="Attendance System", font=("TkDefaultFont", 16)).pack(pady=10)
        
        self.status_label = ttk.Label(self.right_frame, text="Ready")
        self.status_label.pack(pady=10)
        
        self.recognition_label = ttk.Label(self.right_frame, text="No one recognized")
        self.recognition_label.pack(pady=10)
        
        # Voice command button
        self.voice_button = ttk.Button(
            self.right_frame, 
            text="Hold to Speak", 
            style="success.TButton",
            command=None
        )
        self.voice_button.pack(pady=10, fill="x")
        self.voice_button.bind("<ButtonPress>", self.start_recording)
        self.voice_button.bind("<ButtonRelease>", self.stop_recording)
        
        # Last response display
        ttk.Label(self.right_frame, text="Last Response:").pack(pady=(20, 5), anchor="w")
        self.response_text = tk.Text(self.right_frame, height=5, width=25, wrap="word")
        self.response_text.pack(pady=5, fill="x")
        self.response_text.insert("1.0", "No responses yet")
        self.response_text.config(state="disabled")
        
        # Initialize camera
        self.init_camera()
        
        # Connect to server
        self.connect_to_server()
        
        # Initialize audio
        self.init_audio()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Start update loop
        self.update()
        
        # Start response processing loop
        response_thread = threading.Thread(target=self.process_responses)
        response_thread.daemon = True
        response_thread.start()
    
    def init_camera(self):
        try:
            # Try different camera indices for Raspberry Pi
            camera_indices = [0, -1, 2, 1]
            for idx in camera_indices:
                self.cap = cv2.VideoCapture(idx)
                if self.cap.isOpened():
                    print(f"Camera opened successfully on index {idx}")
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    break
            
            if not self.cap.isOpened():
                self.status_label.config(text="Error: Could not open camera")
                print("Error: Could not open camera")
                
        except Exception as e:
            self.status_label.config(text=f"Camera error: {str(e)}")
            print(f"Camera error: {str(e)}")
    
    def init_audio(self):
        try:
            # Set default audio device
            self.audio = pyaudio.PyAudio()
            default_input = self.audio.get_default_input_device_info()
            default_output = self.audio.get_default_output_device_info()
            
            # Update AUDIO_FORMAT configuration
            global AUDIO_FORMAT, CHANNELS, RATE, CHUNK
            AUDIO_FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100  # More common sample rate
            CHUNK = 1024  # Smaller chunk size
            
            self.recording = False
        except Exception as e:
            self.status_label.config(text=f"Audio error: {str(e)}")
            print(f"Audio error: {str(e)}")
    
    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_IP, SERVER_PORT))
            self.status_label.config(text="Connected to server")
            print("Connected to server")
            
            # Start thread for sending frames
            self.send_thread = threading.Thread(target=self.send_frames)
            self.send_thread.daemon = True
            self.send_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"Connection error: {str(e)}")
            print(f"Connection error: {str(e)}")
    
    def send_frames(self):
        last_sent_time = 0
        
        while running:
            try:
                # Send frame every 1 second to reduce load
                current_time = time.time()
                if current_time - last_sent_time >= 1:
                    ret, frame = self.cap.read()
                    if ret:
                        # Resize frame for network efficiency
                        small_frame = cv2.resize(frame, (320, 240))
                        
                        # Prepare message
                        message = {
                            'type': 'frame',
                            'data': pickle.dumps(small_frame)
                        }
                        
                        # Send message
                        message_bytes = pickle.dumps(message)
                        size = len(message_bytes).to_bytes(4, byteorder='big')
                        self.client_socket.sendall(size + message_bytes)
                        
                        last_sent_time = current_time
                
                # Process any response from server
                try:
                    header = self.client_socket.recv(4, socket.MSG_DONTWAIT)
                    if header:
                        size = int.from_bytes(header, byteorder='big')
                        data = b''
                        while len(data) < size:
                            packet = self.client_socket.recv(size - len(data))
                            if not packet:
                                break
                            data += packet
                        
                        if data:
                            response = pickle.loads(data)
                            response_queue.put(response)
                except BlockingIOError:
                    # No data available
                    pass
                except Exception as e:
                    print(f"Error receiving data: {e}")
                
                time.sleep(0.1)  # Small sleep to prevent high CPU usage
                
            except Exception as e:
                print(f"Error in send_frames: {e}")
                time.sleep(1)  # Wait before retrying
    
    def start_recording(self, event):
        if not hasattr(self, 'audio'):
            self.status_label.config(text="Audio not initialized")
            return
        
        self.recording = True
        self.status_label.config(text="Recording...")
        
        def record_audio():
            try:
                stream = self.audio.open(format=AUDIO_FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)
                
                frames = []
                
                while self.recording:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
                # Convert audio data to bytes
                audio_data = b''.join(frames)
                
                # Put audio data in queue
                message = {
                    'type': 'audio',
                    'data': audio_data,
                    'user_id': getattr(self, 'current_user_id', None)
                }
                
                # Send audio to server
                message_bytes = pickle.dumps(message)
                size = len(message_bytes).to_bytes(4, byteorder='big')
                self.client_socket.sendall(size + message_bytes)
                
            except Exception as e:
                print(f"Error recording audio: {e}")
        
        record_thread = threading.Thread(target=record_audio)
        record_thread.daemon = True
        record_thread.start()
    
    def stop_recording(self, event):
        self.recording = False
        self.status_label.config(text="Processing...")
    
    def process_responses(self):
        while running:
            try:
                if not response_queue.empty():
                    response = response_queue.get()
                    response_type = response.get('type')
                    
                    if response_type == 'speech':
                        text = response.get('text', '')
                        
                        # Update response text in UI
                        self.response_text.config(state="normal")
                        self.response_text.delete("1.0", "end")
                        self.response_text.insert("1.0", text)
                        self.response_text.config(state="disabled")
                        
                        # Convert text to speech
                        self.speak_text(text)
                        
                        # Extract user ID if present in response
                        if "Hello" in text and "your attendance has been marked" in text:
                            name = text.split("Hello ")[1].split(",")[0]
                            self.recognition_label.config(text=f"Recognized: {name}")
                    
                    response_queue.task_done()
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing responses: {e}")
                time.sleep(1)
    
    def speak_text(self, text):
        try:
            # Simple TTS using gTTS (Google Text-to-Speech)
            # We'll use a very basic approach to avoid dependencies
            
            # Save response to a temporary WAV file using sox
            with open('response.txt', 'w') as f:
                f.write(text)
            
            os.system(f'espeak -f response.txt -w response.wav')
            
            # Play the audio file
            pygame.mixer.music.load('response.wav')
            pygame.mixer.music.play()
            
            # Clean up the file after playing
            def cleanup():
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                try:
                    os.remove('response.txt')
                    os.remove('response.wav')
                except:
                    pass
            
            cleanup_thread = threading.Thread(target=cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
        except Exception as e:
            print(f"Error in TTS: {e}")
    
    def update(self):
        try:
            if hasattr(self, 'cap') and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Convert frame to a format tkinter can display
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img = ImageTk.PhotoImage(image=img)
                    
                    # Update the image in the label
                    self.video_label.config(image=img)
                    self.video_label.image = img
        except Exception as e:
            print(f"Error updating frame: {e}")
        
        # Schedule the next update
        self.root.after(33, self.update)  # ~30 FPS

def main():
    global running
    
    try:
        # Enable better error reporting
        import sys
        import traceback
        
        def handle_exception(exc_type, exc_value, exc_traceback):
            print("An error occurred:")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = handle_exception
        
        # Create Tkinter root with error handling
        root = ttk.Window()
        root.protocol("WM_DELETE_WINDOW", lambda: cleanup(root))
        
        # Create client app
        app = AttendanceClient(root)
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Critical error in main: {e}")
        traceback.print_exc()
    finally:
        running = False

def cleanup(root):
    global running
    running = False
    root.destroy()



# # Install required system packages
# sudo apt-get update
# sudo apt-get install -y python3-pygame python3-tk python3-pil python3-pil.imagetk portaudio19-dev python3-pyaudio

# # Configure audio
# sudo modprobe snd_bcm2835
# sudo usermod -a -G audio $USER

# # Fix video permissions
# sudo usermod -a -G video $USER
