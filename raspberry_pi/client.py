import time
import requests
import json
import threading
import logging
from camera import capture_image
from audio import record_audio, play_audio, speech_to_text, text_to_speech
from config import SERVER_URL, CAPTURE_INTERVAL, WAKE_WORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("RaspberryPiClient")

# Global flags for controlling processes
running = True
listening_mode = False

def check_server_connection():
    """Check if the server is reachable."""
    try:
        response = requests.get(f"{SERVER_URL}/api/status", timeout=5)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to connect to server: {e}")
        return False

def send_attendance_image():
    """Capture and send an image for attendance processing."""
    try:
        # Capture image
        image_path = capture_image()
        if not image_path:
            logger.error("Failed to capture image")
            return False
        
        # Prepare the image for sending
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
            
            # Send to server
            response = requests.post(
                f"{SERVER_URL}/api/attendance",
                files=files,
                data=data,
                timeout=10
            )
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Attendance processed: {result}")
            
            # Announce results
            if result.get('status') == 'success':
                faces_detected = result.get('detected_faces', 0)
                attendance_recorded = result.get('attendance_recorded', 0)
                
                if faces_detected > 0:
                    message = f"Detected {faces_detected} faces. Recorded attendance for {attendance_recorded} students."
                    text_to_speech(message)
                else:
                    text_to_speech("No faces detected in the image.")
            
            return True
        else:
            logger.error(f"Error from server: {response.text}")
            text_to_speech("Failed to process attendance. Please try again.")
            return False
    
    except Exception as e:
        logger.error(f"Error sending attendance image: {e}")
        text_to_speech("Error processing attendance. Please check the system.")
        return False

def send_query(query_text, student_id=None):
    """Send a student query to the server and get a response."""
    try:
        # Prepare data
        data = {
            "query": query_text,
        }
        
        if student_id:
            data["student_id"] = student_id
        
        # Send to server
        response = requests.post(
            f"{SERVER_URL}/api/query",
            json=data,
            timeout=10
        )
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                return result.get('response')
            else:
                logger.error(f"Query error: {result.get('message')}")
                return "Sorry, I couldn't process your question. Please try again."
        else:
            logger.error(f"Error from server: {response.text}")
            return "Sorry, I'm having trouble connecting to the server."
    
    except Exception as e:
        logger.error(f"Error sending query: {e}")
        return "Sorry, there was an error processing your request."

def attendance_thread_function():
    """Thread function for periodically capturing attendance."""
    global running
    
    logger.info("Starting attendance thread")
    
    while running:
        # Check if it's during class hours
        current_hour = int(time.strftime('%H'))
        if 8 <= current_hour <= 17:  # 8 AM to 5 PM
            logger.info("Capturing attendance")
            
            if check_server_connection():
                send_attendance_image()
            else:
                logger.warning("Server not reachable, skipping attendance capture")
                text_to_speech("Warning: Server connection lost. Attendance not recorded.")
        
        # Sleep until next capture interval
        time.sleep(CAPTURE_INTERVAL)

def voice_assistant_thread_function():
    """Thread function for voice assistant functionality."""
    global running, listening_mode
    
    logger.info("Starting voice assistant thread")
    
    while running:
        # Check if we're actively listening for commands
        if listening_mode:
            logger.info("Listening for commands...")
            text_to_speech("Listening for your question...")
            
            # Record audio and convert to text
            audio_file = record_audio(duration=5)
            if audio_file:
                query_text = speech_to_text(audio_file)
                
                if query_text:
                    logger.info(f"Detected query: {query_text}")
                    
                    # Process special commands
                    if "stop listening" in query_text.lower():
                        listening_mode = False
                        text_to_speech("Voice assistant deactivated.")
                        continue
                    
                    # Send query to server
                    if check_server_connection():
                        text_to_speech("Processing your question...")
                        response = send_query(query_text)
                        text_to_speech(response)
                    else:
                        text_to_speech("Sorry, I can't connect to the server right now.")
                else:
                    text_to_speech("I didn't catch that. Could you repeat?")
            
            # After processing, go back to passive listening
            listening_mode = False
            
        else:
            # Passive listening for wake word
            audio_file = record_audio(duration=2)
            if audio_file:
                text = speech_to_text(audio_file)
                
                if text and WAKE_WORD.lower() in text.lower():
                    listening_mode = True
                    logger.info("Wake word detected, activating assistant")
                    text_to_speech("Yes, how can I help you?")
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.5)

def main():
    """Main function to start the client."""
    global running
    
    logger.info("Starting AI Academic Assistant Client")
    text_to_speech("Academic Assistant is starting up.")
    
    # Check server connection
    if not check_server_connection():
        logger.warning("Cannot connect to server. Will continue trying.")
        text_to_speech("Warning: Cannot connect to server. Some features may be limited.")
    else:
        text_to_speech("Server connection established.")
    
    # Start attendance thread
    attendance_thread = threading.Thread(target=attendance_thread_function)
    attendance_thread.daemon = True
    attendance_thread.start()
    
    # Start voice assistant thread
    voice_thread = threading.Thread(target=voice_assistant_thread_function)
    voice_thread.daemon = True
    voice_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        running = False
        text_to_speech("Shutting down Academic Assistant.")
        time.sleep(2)  # Give threads time to clean up

if __name__ == "__main__":
    main()