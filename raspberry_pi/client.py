import socket
import json
import threading

class CommandClient:
    def __init__(self, server_ip, command_port):
        self.server_ip = server_ip
        self.command_port = command_port
        self.command_socket = None
        self.connected = False
        
    def initialize(self):
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket.connect((self.server_ip, self.command_port))
        self.connected = True
        print(f"Command client connected to server at {self.server_ip}:{self.command_port}")
        
        # Start listener for commands
        self.listener_thread = threading.Thread(target=self.listen_for_commands)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
    def send_command(self, command, data=None):
        if not self.connected:
            return False
            
        message = {
            "command": command,
            "data": data or {}
        }
        
        try:
            self.command_socket.sendall(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
            
    def listen_for_commands(self):
        buffer_size = 4096
        data = ""
        
        while self.connected:
            try:
                chunk = self.command_socket.recv(buffer_size).decode('utf-8')
                if not chunk:
                    continue
                    
                data += chunk
                
                # Process complete messages
                if data.endswith('\n'):
                    messages = data.strip().split('\n')
                    for message in messages:
                        try:
                            cmd = json.loads(message)
                            self.process_command(cmd)
                        except json.JSONDecodeError:
                            pass
                    data = ""
                    
            except Exception as e:
                print(f"Error receiving command: {e}")
                self.connected = False
                break
                
    def process_command(self, cmd):
        # Handle commands from server
        command = cmd.get("command", "")
        data = cmd.get("data", {})
        
        print(f"Received command: {command}")
        # Process specific commands here
        
    def release(self):
        self.connected = False
        if self.command_socket:
            self.command_socket.close()