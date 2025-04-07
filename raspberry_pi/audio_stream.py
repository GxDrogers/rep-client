import pyaudio
import socket
import threading

class AudioStream:
    def __init__(self, server_ip='192.168.1.100', server_port=8001):
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _stream_loop(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.format, channels=self.channels,
                            rate=self.rate, input=True,
                            frames_per_buffer=self.chunk)
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_ip, self.server_port))
        
        try:
            while self.running:
                data = stream.read(self.chunk)
                client_socket.sendall(len(data).to_bytes(4, byteorder='big'))
                client_socket.sendall(data)
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            client_socket.close()
