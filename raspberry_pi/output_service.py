import socket
import threading
import pyaudio
import wave
import io
import time
from gtts import gTTS

class OutputService:
    def __init__(self, host='0.0.0.0', port=8002):
        self.host = host
        self.port = port
        self.running = False
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _listen_loop(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        
        try:
            while self.running:
                client, _ = server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client,)).start()
        finally:
            server_socket.close()
    
    def _handle_client(self, client):
        size_bytes = client.recv(4)
        size = int.from_bytes(size_bytes, byteorder='big')
        
        audio_data = b''
        while len(audio_data) < size:
            chunk = client.recv(min(4096, size - len(audio_data)))
            if not chunk:
                break
            audio_data += chunk
            
        client.close()
        
        # Play the audio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
        p.terminate()