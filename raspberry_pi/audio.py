import pyaudio
import socket
import threading
import wave
import time

class Audio:
    def __init__(self, server_ip, audio_port):
        self.server_ip = server_ip
        self.audio_port = audio_port
        self.audio = None
        self.audio_socket = None
        self.streaming = False
        
        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        
    def initialize(self):
        # Initialize audio
        self.audio = pyaudio.PyAudio()
        
        # Connect to server
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket.connect((self.server_ip, self.audio_port))
        print(f"Audio connected to server at {self.server_ip}:{self.audio_port}")
        
        # Start listener thread for audio output
        self.listener_thread = threading.Thread(target=self.listen_for_audio)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
    def stream_mic(self):
        if not self.audio or not self.audio_socket:
            raise Exception("Audio not initialized")
            
        self.streaming = True
        stream = self.audio.open(format=self.format,
                                channels=self.channels,
                                rate=self.rate,
                                input=True,
                                frames_per_buffer=self.chunk)
        
        try:
            while self.streaming:
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.audio_socket.sendall(data)
        except Exception as e:
            print(f"Audio streaming error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            
    def listen_for_audio(self):
        # Socket for receiving audio output from server
        playback_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        playback_socket.connect((self.server_ip, self.audio_port + 100))
        
        stream = self.audio.open(format=self.format,
                                channels=self.channels,
                                rate=self.rate,
                                output=True,
                                frames_per_buffer=self.chunk)
        
        try:
            while True:
                data = playback_socket.recv(self.chunk)
                if not data:
                    time.sleep(0.1)
                    continue
                stream.write(data)
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            playback_socket.close()
            
    def release(self):
        self.streaming = False
        if self.audio:
            self.audio.terminate()
        if self.audio_socket:
            self.audio_socket.close()