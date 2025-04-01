import cv2
import requests
import json
import base64
import websocket
import threading
import time
import pyaudio
import wave
import speech_recognition as sr
import pyttsx3
import argparse
import os



# Initialize argument parser
parser = argparse.ArgumentParser(description='AI Academic Assistant Client')
parser.add_argument('--server', type=str, default='http://localhost:8000',
                    help='Server URL (default: http://localhost:8000)')
parser.add_argument('--interval', type=int, default=5,
                    help='Facial recognition interval in seconds (default: 5)')
parser.add_argument('--debug', action='store_true',
                    help='Enable debug mode with additional logging')
args = parser.parse_args()

# Server URL
SERVER_URL = args.server
WEBSOCKET_URL = SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws'
DEBUG = args.debug

# Initialize GPIO


# Initialize text-to-speech engine
engine = pyttsx3.init()

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")



def speak(text):
    debug_print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()

class AcademicAssistantClient:
    def __init__(self):
        self.ws = None
        self.camera = None
        self.recognizer = sr.Recognizer()
        self.ws_thread = None
        self.running = False
        self.last_recognition_time = 0
        self.recognition_interval = args.interval  # seconds

    def connect_websocket(self):
        debug_print(f"Connecting to WebSocket at {WEBSOCKET_URL}")
        self.ws = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            debug_print(f"Received message: {data}")
            
            if "type" in data and data["type"] == "recognition_result":
                if data["status"] == "success":
                    debug_print("Status: Processing")
                    students = data["recognized_students"]
                    if students:
                        speak(f"Hello, {', '.join([s['name'] for s in students])}. Attendance recorded.")
                else:
                    debug_print("Status: error")
                    speak("No registered students recognized.")
            
            elif "response" in data:
                debug_prin("Status: ready")
                speak(data["response"])
                
        except Exception as e:
            debug_print(f"Error processing message: {e}")
            debug_print("Status: error")

    def on_error(self, ws, error):
        debug_print(f"WebSocket error: {error}")
        debug_print("Status: error")
        speak("Connection error. Please check the server.")
        time.sleep(5)
        self.connect_websocket()

    def on_close(self, ws, close_status_code, close_msg):
        debug_print("WebSocket connection closed")
        debug_print("Status: error")
        if self.running:
            speak("Connection lost. Attempting to reconnect.")
            time.sleep(5)
            self.connect_websocket()

    def on_open(self, ws):
        debug_print("WebSocket connection established")
        debug_print("Status: ready")
        speak("System ready. Hello, I am your academic assistant.")

    def init_camera(self):
        debug_print("Initializing camera")
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            debug_print("Error: Could not open camera")
            
            speak("Camera error. Please check the connection.")
            return False
        return True

    def capture_image(self):
        ret, frame = self.camera.read()
        if not ret:
            debug_print("Error: Could not capture image")
            return None
        return frame

    def encode_image(self, image):
        ret, buffer = cv2.imencode('.jpg', image)
        if not ret:
            debug_print("Error: Could not encode image")
            return None
        return base64.b64encode(buffer).decode('utf-8')

    def recognize_face(self):
        current_time = time.time()
        if current_time - self.last_recognition_time < self.recognition_interval:
            return
        
        debug_print("Status: Processing")
        debug_print("Capturing image for face recognition")
        frame = self.capture_image()
        if frame is None:
            set_led_status("error")
            return
        
        encoded_image = self.encode_image(frame)
        if encoded_image is None:
            debug_print("Status: error")
            return
        
        try:
            message = {
                "type": "face_recognition",
                "image": encoded_image
            }
            self.ws.send(json.dumps(message))
            self.last_recognition_time = current_time
        except Exception as e:
            debug_print(f"Error sending face recognition data: {e}")
            debug_print("Status: error")

    def listen_for_query(self):
        debug_print("Status: Processing")
        speak("I'm listening. Please ask your question.")
        
        with sr.Microphone() as source:
            debug_print("Adjusting for ambient noise")
            self.recognizer.adjust_for_ambient_noise(source)
            debug_print("Listening for query")
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                debug_print("Processing speech to text")
                query = self.recognizer.recognize_google(audio)
                debug_print(f"Recognized: {query}")
                
                message = {
                    "type": "query",
                    "content": query
                }
                
                self.ws.send(json.dumps(message))
                
            except sr.WaitTimeoutError:
                debug_print("Status: ready")
                speak("Sorry, I didn't hear anything. Please try again.")
            except sr.UnknownValueError:
                debug_print("Status: ready")
                speak("Sorry, I didn't understand that. Please try again.")
            except Exception as e:
                debug_print(f"Error processing speech: {e}")
                debug_print("Status: error")
                speak("An error occurred. Please try again.")

    def run(self):
        self.running = True
        debug_print("Status: Processing")
        
        # Connect to WebSocket
        self.connect_websocket()
        
        # Initialize camera
        if not self.init_camera():
            return
        
        time.sleep(2)  # Wait for WebSocket connection
        
        speak("System initialized. Press the button or say 'Hello Assistant' to begin.")
        
        try:
            
            
            # Setup wake word detection
            wake_word_recognizer = sr.Recognizer()
            
            while self.running:
                # Check for face recognition (periodically)
                self.recognize_face()
                
                # Listen for wake word in the background
                with sr.Microphone() as source:
                    wake_word_recognizer.adjust_for_ambient_noise(source)
                    try:
                        audio = wake_word_recognizer.listen(source, timeout=1, phrase_time_limit=3)
                        wake_text = wake_word_recognizer.recognize_google(audio)
                        if "hello assistant" in wake_text.lower():
                            debug_print("Wake word detected - entering query mode")
                            self.listen_for_query()
                    except:
                        pass  # Ignore errors in wake word detection
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            debug_print("Keyboard interrupt detected")
        finally:
            self.cleanup()

    def cleanup(self):
        debug_print("Cleaning up resources")
        self.running = False
        
        if self.camera is not None:
            self.camera.release()
        
        if self.ws is not None:
            self.ws.close()
        

        
        debug_print("Cleanup complete")

if __name__ == "__main__":
    client = AcademicAssistantClient()
    try:
        client.run()
    except Exception as e:
        debug_print(f"Error: {e}")
        speak("A critical error occurred. System shutting down.")
       
