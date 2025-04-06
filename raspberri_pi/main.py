import asyncio
import websockets
import json
import threading
from camera_stream import CameraStream
from audio_stream import AudioStream
from output_manager import OutputManager

class RaspberryPiClient:
    def __init__(self, server_uri="ws://192.168.83.133:8765"):  # Replace with your PC's IP
        self.server_uri = server_uri
        self.camera = CameraStream()
        self.audio = AudioStream()
        self.output = OutputManager()
        self.running = False
        
    async def connect(self):
        async with websockets.connect(self.server_uri) as websocket:
            self.running = True
            
            # Start camera and audio streams
            camera_task = asyncio.create_task(self.stream_camera(websocket))
            audio_task = asyncio.create_task(self.stream_audio(websocket))
            receive_task = asyncio.create_task(self.receive_commands(websocket))
            
            await asyncio.gather(camera_task, audio_task, receive_task)
    
    async def stream_camera(self, websocket):
        while self.running:
            frame = self.camera.get_frame()
            await websocket.send(json.dumps({
                'type': 'camera',
                'data': frame.tolist()  # Convert numpy array to list
            }))
            await asyncio.sleep(0.1)  # 10 FPS
    
    async def stream_audio(self, websocket):
        while self.running:
            audio_data = self.audio.get_audio()
            await websocket.send(json.dumps({
                'type': 'audio',
                'data': audio_data.tolist()
            }))
            await asyncio.sleep(0.05)  # 20Hz update rate
    
    async def receive_commands(self, websocket):
        while self.running:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'speech':
                self.output.play_speech(data['text'])
            elif data['type'] == 'control':
                if data['command'] == 'stop':
                    self.running = False
                # Add more control commands as needed
    
    def start(self):
        asyncio.run(self.connect())

if __name__ == "__main__":
    client = RaspberryPiClient()
    client.start()