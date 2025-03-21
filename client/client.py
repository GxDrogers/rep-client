import cv2
import asyncio
import websockets
import json
import pygame
import base64
from time import sleep
import os

class AcademicClient:
    def __init__(self):
        # Initialize camera with retries
        self.init_camera()
        self.server_url = "ws://192.168.83.133:8765"
        self.audio_dir = "temp_audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Initialize audio with error handling
        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Audio initialization failed: {e}")
            
    def init_camera(self, max_retries=3):
        for attempt in range(max_retries):
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                return
            print(f"Camera init attempt {attempt + 1} failed, retrying...")
            sleep(2)
        raise RuntimeError("Failed to initialize camera")

    def capture_frame(self):
        if not self.camera.isOpened():
            self.init_camera()
        
        for _ in range(3):  # Multiple attempts to capture
            ret, frame = self.camera.read()
            if ret and frame is not None:
                try:
                    _, buffer = cv2.imencode('.jpg', frame)
                    return base64.b64encode(buffer).decode('utf-8')
                except Exception as e:
                    print(f"Frame encoding error: {e}")
            sleep(0.1)
        return None

    async def connect_to_server(self):
        while True:
            try:
                async with websockets.connect(self.server_url, ping_interval=None) as ws:
                    print("Connected to server")
                    while True:
                        frame_data = self.capture_frame()
                        if not frame_data:
                            print("Frame capture failed")
                            await asyncio.sleep(1)
                            continue
                            
                        try:
                            await ws.send(json.dumps({
                                "type": "frame",
                                "data": frame_data
                            }))
                            
                            response = await ws.recv()
                            response_data = json.loads(response)
                            
                            if response_data.get("type") == "audio":
                                self.play_audio(response_data["data"])
                                
                        except Exception as e:
                            print(f"Communication error: {e}")
                            break
                            
                        await asyncio.sleep(0.1)
                        
            except Exception as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(5)  # Wait before retry
                
    def play_audio(self, audio_data):
        try:
            audio_path = os.path.join(self.audio_dir, "temp.wav")
            with open(audio_path, "wb") as f:
                f.write(base64.b64decode(audio_data))
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Audio playback error: {e}")

    def cleanup(self):
        if self.camera.isOpened():
            self.camera.release()
        pygame.mixer.quit()

if __name__ == "__main__":
    client = AcademicClient()
    try:
        asyncio.get_event_loop().run_until_complete(client.connect_to_server())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        client.cleanup()