import time
import socket
import json
import threading
import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from PIL import Image, ImageTk
import io
import struct

from camera import CameraModule
from audio import AudioModule
from display import DisplayManager

class AcademicAssistantClient:
    def __init__(self, master):
        self.master = master
        master.title("AI Academic Assistant")
        
        # Configure the window
        master.geometry("800x480")  # Common Raspberry Pi display resolution
        
        # Initialize the style
        self.style = Style(theme="darkly")
        
        # Initialize modules
        self.camera = CameraModule()
        self.audio = AudioModule()
        self.display = DisplayManager(master)
        
        # Server connection settings
        self.server_host = "192.168.83.133"  # Change to your server's IP
        self.server_port = 12345
        self.socket = None
        self.connected = False
        
        # Set up the UI
        self.setup_ui()
        
        # Connect to server
        self.connect_to_server()
        
        # Start capturing faces periodically
        self.start_face_recognition()
        
    def setup_ui(self):
        # Create tabs
        self.tabControl = ttk.Notebook(self.master)
        
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        
        self.tabControl.add(self.tab1, text="Attendance")
        self.tabControl.add(self.tab2, text="Help Assistant")
        
        self.tabControl.pack(expand=1, fill="both")
        
        # Tab 1 - Attendance System
        self.setup_attendance_tab()
        
        # Tab 2 - Chatbot Assistant
        self.setup_chatbot_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected to server")
        status_bar = ttk.Label(self.master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_attendance_tab(self):
        # Camera preview frame
        self.preview_frame = ttk.LabelFrame(self.tab1, text="Camera Preview")
        self.preview_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.camera_label = ttk.Label(self.preview_frame)
        self.camera_label.pack(pady=10, padx=10)
        
        # Recognition results
        self.results_frame = ttk.LabelFrame(self.tab1, text="Recognition Results")
        self.results_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(self.results_frame, height=10, width=40)
        self.results_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Manual capture button
        self.capture_btn = ttk.Button(self.tab1, text="Manual Capture", command=self.manual_capture)
        self.capture_btn.pack(pady=10, padx=10)
    
    def setup_chatbot_tab(self):
        # Chat history
        self.chat_frame = ttk.LabelFrame(self.tab2, text="Chat History")
        self.chat_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.chat_text = tk.Text(self.chat_frame, height=10, width=40)
        self.chat_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Input area
        self.input_frame = ttk.Frame(self.tab2)
        self.input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(self.input_frame, textvariable=self.query_var, width=50)
        self.query_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.send_btn = ttk.Button(self.input_frame, text="Send", command=self.send_query)
        self.send_btn.pack(side=tk.RIGHT, padx=5)
        
        # Voice input button
        self.voice_btn = ttk.Button(self.tab2, text="Voice Input", command=self.voice_input)
        self.voice_btn.pack(pady=10, padx=10)
    
    def connect_to_server(self):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            self.status_var.set(f"Connected to server: {self.server_host}:{self.server_port}")
            
            # Start a thread to receive messages from the server
            receiver_thread = threading.Thread(target=self.receive_messages)
            receiver_thread.daemon = True
            receiver_thread.start()
            
        except Exception as e:
            self.status_var.set(f"Connection error: {str(e)}")
            # Try to reconnect after a delay
            self.master.after(5000, self.connect_to_server)
    
    def receive_messages(self):
        """Receive and process messages from the server"""
        try:
            while self.connected:
                header = self.socket.recv(8)
                if not header:
                    break
                    
                msg_type, msg_len = header[:1], int.from_bytes(header[1:], byteorder='big')
                
                # Receive message in chunks
                data = b''
                remaining = msg_len
                while remaining > 0:
                    chunk = self.socket.recv(min(remaining, 4096))
                    if not chunk:
                        break
                    data += chunk
                    remaining -= len(chunk)
                
                if msg_type == b'R':  # Response from server
                    if self.tabControl.index(self.tabControl.select()) == 0:
                        # Attendance tab response
                        try:
                            response = json.loads(data.decode('utf-8'))
                            names = response.get('recognized', [])
                            timestamp = response.get('timestamp', '')
                            
                            if names:
                                self.results_text.insert(tk.END, f"{timestamp} - Recognized: {', '.join(names)}\n")
                            else:
                                self.results_text.insert(tk.END, f"{timestamp} - No one recognized\n")
                            self.results_text.see(tk.END)
                        except:
                            # If it's not JSON, it's probably a chatbot response
                            pass
                    else:
                        # Chatbot tab response
                        response = data.decode('utf-8')
                        self.chat_text.insert(tk.END, f"Assistant: {response}\n\n")
                        self.chat_text.see(tk.END)
                
        except Exception as e:
            self.status_var.set(f"Connection lost: {str(e)}")
            self.connected = False
            # Try to reconnect after a delay
            self.master.after(5000, self.connect_to_server)
    
    def start_face_recognition(self):
        """Start periodic face recognition"""
        self.update_camera_preview()
        # Capture faces every 10 seconds
        self.master.after(10000, self.capture_and_recognize)
    
    def update_camera_preview(self):
        """Update the camera preview"""
        frame = self.camera.get_frame()
        if frame is not None:
            # Convert frame to PhotoImage for display
            img = Image.fromarray(frame)
            img = img.resize((320, 240))  # Resize for display
            photo = ImageTk.PhotoImage(image=img)
            
            # Update the label
            self.camera_label.config(image=photo)
            self.camera_label.image = photo  # Keep a reference
        
        # Update preview every 100ms
        self.master.after(100, self.update_camera_preview)
    
    def capture_and_recognize(self):
        """Capture an image and send it to the server for recognition"""
        if self.connected:
            # Capture a frame
            frame = self.camera.get_frame()
            if frame is not None:
                # Convert to bytes
                img = Image.fromarray(frame)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_data = img_bytes.getvalue()
                
                # Send to server with header: type (I for image) + length (7 bytes)
                msg_len = len(img_data).to_bytes(7, byteorder='big')
                self.socket.sendall(b'I' + msg_len + img_data)
        
        # Schedule the next capture
        self.master.after(10000, self.capture_and_recognize)
    
    def manual_capture(self):
        """Manually trigger capture and recognition"""
        if self.connected:
            self.capture_and_recognize()
            self.status_var.set("Manual capture initiated")
    
    def send_query(self):
        """Send a chatbot query to the server"""
        query = self.query_var.get().strip()
        if query and self.connected:
            # Add query to chat
            self.chat_text.insert(tk.END, f"You: {query}\n")
            
            # Send to server with header: type (Q for query) + length (7 bytes)
            query_bytes = query.encode('utf-8')
            msg_len = len(query_bytes).to_bytes(7, byteorder='big')
            self.socket.sendall(b'Q' + msg_len + query_bytes)
            
            # Clear the input
            self.query_var.set("")
    
    def voice_input(self):
        """Activate voice input for queries"""
        # This would use the AudioModule to capture voice
        # and convert to text using speech recognition
        self.status_var.set("Voice input not implemented in prototype")
        # In a real implementation:
        # text = self.audio.capture_and_transcribe()
        # self.query_var.set(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = AcademicAssistantClient(root)
    root.mainloop()