import sys
import os
import threading
import time

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_IP, VIDEO_PORT, AUDIO_PORT, COMMAND_PORT

from camera import Camera
from audio import Audio
from client import CommandClient

def main():
    print("Starting AI Academic Assistant Client (Raspberry Pi)")
    
    # Initialize components
    try:
        # Setup camera
        camera = Camera(SERVER_IP, VIDEO_PORT)
        camera.initialize()
        
        # Setup audio
        audio = Audio(SERVER_IP, AUDIO_PORT)
        audio.initialize()
        
        # Setup command client
        cmd_client = CommandClient(SERVER_IP, COMMAND_PORT)
        cmd_client.initialize()
        
        # Start threads
        camera_thread = threading.Thread(target=camera.stream)
        camera_thread.daemon = True
        camera_thread.start()
        
        audio_thread = threading.Thread(target=audio.stream_mic)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if 'camera' in locals():
            camera.release()
        if 'audio' in locals():
            audio.release()
        if 'cmd_client' in locals():
            cmd_client.release()

if __name__ == "__main__":
    main()
