import tkinter as tk
from tkinter import ttk
import threading
import time

class DisplayManager:
    def __init__(self, root):
        self.root = root
        self.notification_queue = []
        self.notification_lock = threading.Lock()
        
        # Create a notification area at the top
        self.notification_var = tk.StringVar()
        self.notification_label = ttk.Label(
            root,
            textvariable=self.notification_var,
            font=("Helvetica", 12),
            background="#2C3E50",
            foreground="white",
            anchor=tk.CENTER
        )
        self.notification_label.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Start the notification display thread
        self.notification_thread = threading.Thread(target=self._process_notifications)
        self.notification_thread.daemon = True
        self.notification_thread.start()
    
    def show_notification(self, message, duration=3):
        """Show a notification message for a specified duration"""
        with self.notification_lock:
            self.notification_queue.append((message, duration))
    
    def _process_notifications(self):
        """Process notification queue in background"""
        while True:
            # Check if there are notifications to display
            if self.notification_queue:
                with self.notification_lock:
                    message, duration = self.notification_queue.pop(0)
                
                # Update the notification text
                self.root.after(0, lambda: self.notification_var.set(message))
                
                # Wait for the specified duration
                time.sleep(duration)
                
                # Clear the notification
                self.root.after(0, lambda: self.notification_var.set(""))
                
                # Small delay between notifications
                time.sleep(0.5)
            else:
                # No notifications, sleep briefly
                time.sleep(0.1)
    
    def update_status(self, status_text):
        """Update a status display"""
        # This could update a status bar or other UI element
        self.show_notification(status_text, 2)