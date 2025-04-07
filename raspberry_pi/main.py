from camera_stream import CameraStream
from audio_stream import AudioStream
from output_service import OutputService
import time
import signal
import sys

def signal_handler(sig, frame):
    print("Shutting down...")
    camera_stream.stop()
    audio_stream.stop()
    output_service.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Configure these with your PC's IP address
    PC_IP = "192.168.1.100"  
    
    # Initialize services
    camera_stream = CameraStream(server_ip=PC_IP, server_port=8000)
    audio_stream = AudioStream(server_ip=PC_IP, server_port=8001)
    output_service = OutputService(port=8002)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start services
        camera_stream.start()
        print("Camera stream started")
        
        audio_stream.start()
        print("Audio stream started")
        
        output_service.start()
        print("Output service started")
        
        print("All services running. Press Ctrl+C to exit.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        camera_stream.stop()
        audio_stream.stop()
        output_service.stop()