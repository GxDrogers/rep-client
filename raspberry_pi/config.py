"""
Configuration settings for the AI Academic Assistant
"""

# Server connection settings
SERVER_URL = "http://192.168.83.133:5000"  # Replace with your server IP

# Attendance settings
CAPTURE_INTERVAL = 1800  # Capture attendance every 30 minutes (in seconds)

# Voice assistant settings
WAKE_WORD = "assistant"  # Word to activate the voice assistant

# System settings
DEBUG_MODE = True  # Enable debug logging
SYSTEM_NAME = "AI Academic Assistant"

# Class schedule (24-hour format)
CLASS_SCHEDULE = {
    "Monday": [
        {"start": "09:00", "end": "10:30", "subject": "Mathematics"},
        {"start": "11:00", "end": "12:30", "subject": "Physics"},
        {"start": "14:00", "end": "15:30", "subject": "Computer Science"}
    ],
    "Tuesday": [
        {"start": "09:00", "end": "10:30", "subject": "Chemistry"},
        {"start": "11:00", "end": "12:30", "subject": "Biology"},
        {"start": "14:00", "end": "15:30", "subject": "English"}
    ],
    "Wednesday": [
        {"start": "09:00", "end": "10:30", "subject": "Mathematics"},
        {"start": "11:00", "end": "12:30", "subject": "Physics"},
        {"start": "14:00", "end": "15:30", "subject": "Computer Science"}
    ],
    "Thursday": [
        {"start": "09:00", "end": "10:30", "subject": "Chemistry"},
        {"start": "11:00", "end": "12:30", "subject": "Biology"},
        {"start": "14:00", "end": "15:30", "subject": "English"}
    ],
    "Friday": [
        {"start": "09:00", "end": "10:30", "subject": "Mathematics"},
        {"start": "11:00", "end": "12:30", "subject": "Physics"},
        {"start": "14:00", "end": "15:30", "subject": "Computer Science"}
    ]
}

# Additional configuration for expansion
FEATURES_ENABLED = {
    "facial_recognition": True,
    "voice_assistant": True,
    "attendance_tracking": True,
    "performance_analytics": True
}