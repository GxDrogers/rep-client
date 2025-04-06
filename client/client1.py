# client.py - Runs on Raspberry Pi
import cv2
import socket
import threading
import time
import os
import json
import requests
import pyaudio
import numpy as np
from flask import Flask, Response, request

# Configuration
SERVER_IP = '192.168.1.100'  # Change to your laptop's IP
SERVER_PORT = 5000
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
PI_ID = "main_entrance"  # Identifier for this Pi

# Initialize Flask app
app = Flask(__name__)

# Initialize camera
def init_camera():
    try:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return camera
    except Exception as e:
        print(f"Camera initialization error: {e}")
        return None

# Initialize audio
def init_audio():
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=AUDIO_FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        return audio, stream
    except Exception as e:
        print(f"Audio initialization error: {e}")
        return None, None

# Generate camera frames
def generate_frames(camera):
    while True:
        try:
            success, frame = camera.read()
            if not success:
                print("Failed to get frame")
                time.sleep(0.1)
                continue
                
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
            frame_bytes = buffer.tobytes()
            
            # Send frame to server for processing
            try:
                requests.post(f"http://{SERVER_IP}:{SERVER_PORT}/process_frame",
                             files={"frame": frame_bytes},
                             data={"pi_id": PI_ID})
            except requests.exceptions.RequestException:
                pass  # Continue even if the server is temporarily unavailable
                
            # Stream to dashboard
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            time.sleep(0.1)  # Reduce framerate to save bandwidth
        except Exception as e:
            print(f"Frame generation error: {e}")
            time.sleep(0.5)

# Flask route for video streaming
@app.route('/video_feed')
def video_feed():
    try:
        camera = init_camera()
        if camera:
            return Response(generate_frames(camera),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        else:
            return "Camera not available", 500
    except Exception as e:
        print(f"Video feed error: {e}")
        return str(e), 500

# Flask route for audio streaming
@app.route('/audio_feed', methods=['GET'])
def audio_feed():
    def generate_audio():
        audio, stream = init_audio()
        if not audio or not stream:
            return
            
        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                yield data
        except Exception as e:
            print(f"Audio streaming error: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            if audio:
                audio.terminate()
                
    return Response(generate_audio(), mimetype="audio/x-wav")

# Receive audio responses from server
@app.route('/play_audio', methods=['POST'])
def play_audio():
    try:
        # This endpoint receives audio data from the server to play through speakers
        # Implementation depends on how you want to handle audio output
        # For simplicity, you might save to a file and play with a system command
        audio_data = request.data
        with open('response.wav', 'wb') as f:
            f.write(audio_data)
        os.system('aplay response.wav')  # Simple playback
        return "OK", 200
    except Exception as e:
        print(f"Play audio error: {e}")
        return str(e), 500

# Health check endpoint
@app.route('/status')
def status():
    return json.dumps({"status": "online", "pi_id": PI_ID})

# Main function
def main():
    try:
        # Start Flask server
        app.run(host='0.0.0.0', port=8000, threaded=True)
    except Exception as e:
        print(f"Main error: {e}")

if __name__ == "__main__":
    main()