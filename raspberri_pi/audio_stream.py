import numpy as np
import pyaudio

class AudioStream:
    def __init__(self, format=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
    def get_audio(self):
        """Get audio chunk from microphone"""
        data = self.stream.read(self.chunk)
        return np.frombuffer(data, dtype=np.int16)
        
    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()