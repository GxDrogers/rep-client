import os
import time
import logging
import subprocess
from gtts import gTTS
import speech_recognition as sr

# Configure logging
logger = logging.getLogger("Audio")

# Create directories for storing audio files
AUDIO_DIR = "audio"
RECORDINGS_DIR = os.path.join(AUDIO_DIR, "recordings")
RESPONSES_DIR = os.path.join(AUDIO_DIR, "responses")

os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

def record_audio(duration=5, filename=None):
    """
    Record audio from the microphone.
    
    Args:
        duration: Recording duration in seconds
        filename: Optional filename to save the recording
    
    Returns:
        str: Path to the saved audio file, or None if failed
    """
    # Generate filename if not provided
    if filename is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"recording_{timestamp}.wav"
    
    audio_path = os.path.join(RECORDINGS_DIR, filename)
    
    try:
        # Using arecord for audio recording (common on Raspberry Pi)
        cmd = [
            "arecord",
            "-D", "plughw:1,0",  # USB microphone usually at card 1, device 0
            "-f", "cd",          # CD quality
            "-d", str(duration), # Duration
            audio_path           # Output file
        ]
        
        subprocess.run(cmd, check=True)
        logger.info(f"Audio recorded: {audio_path}")
        
        return audio_path
    
    except Exception as e:
        logger.error(f"Error recording audio: {e}")
        return None

def play_audio(audio_file):
    """
    Play an audio file.
    
    Args:
        audio_file: Path to the audio file to play
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Using aplay for audio playback
        cmd = ["aplay", audio_file]
        subprocess.run(cmd, check=True)
        
        logger.info(f"Audio played: {audio_file}")
        return True
    
    except Exception as e:
        logger.error(f"Error playing audio: {e}")
        return False

def speech_to_text(audio_file):
    """
    Convert speech audio to text.
    
    Args:
        audio_file: Path to the audio file to convert
    
    Returns:
        str: Transcribed text, or None if failed
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
            # Use Google Speech Recognition
            text = recognizer.recognize_google(audio_data)
            logger.info(f"Speech recognized: {text}")
            
            return text
    
    except sr.UnknownValueError:
        logger.warning("Speech Recognition could not understand audio")
        return None
    
    except sr.RequestError as e:
        logger.error(f"Could not request results from Speech Recognition service: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Error in speech to text conversion: {e}")
        return None

def text_to_speech(text, filename=None, play=True):
    """
    Convert text to speech and optionally play it.
    
    Args:
        text: Text to convert to speech
        filename: Optional filename to save the audio
        play: Whether to play the audio immediately
    
    Returns:
        str: Path to the saved audio file, or None if failed
    """
    # Generate filename if not provided
    if filename is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"response_{timestamp}.mp3"
    
    audio_path = os.path.join(RESPONSES_DIR, filename)
    
    try:
        # Generate speech from text
        tts = gTTS(text=text, lang='en')
        tts.save(audio_path)
        
        logger.info(f"Text-to-speech generated: {audio_path}")
        
        # Play the audio if requested
        if play:
            # Convert to wav for compatibility with aplay
            wav_path = audio_path.replace('.mp3', '.wav')
            cmd = ["ffmpeg", "-i", audio_path, wav_path]
            subprocess.run(cmd, check=True)
            
            play_audio(wav_path)
        
        return audio_path
    
    except Exception as e:
        logger.error(f"Error in text to speech conversion: {e}")
        return None