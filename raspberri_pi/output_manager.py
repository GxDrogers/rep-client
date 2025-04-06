import pygame
import numpy as np
import io

class OutputManager:
    def __init__(self):
        pygame.mixer.init()
        
    def play_speech(self, text):
        """Play text as speech (audio file sent from server)"""
        if isinstance(text, dict) and 'audio_data' in text:
            # Convert base64 audio data to playable format
            audio_data = np.array(text['audio_data'], dtype=np.int16)
            sound = pygame.mixer.Sound(buffer=audio_data.tobytes())
            sound.play()
        else:
            print(f"Message: {text}")