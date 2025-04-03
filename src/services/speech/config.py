"""
Configuration for speech-to-text services.
Separates configuration from implementation for better maintainability.
"""
import os
from typing import Dict, Any

# Default audio storage configurations
DEFAULT_AUDIO_DIR = os.path.join(os.getcwd(), "tmp", "meeting_recordings")
DEFAULT_AUDIO_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 16000
MAX_AUDIO_SIZE_MB = 25  # OpenAI Whisper API limits

# Default transcription configuration
DEFAULT_TRANSCRIPTION_CONFIG = {
    "model": "whisper-1",  # OpenAI's Whisper model
    "language": "en",      # Default language
    "temperature": 0,      # Deterministic transcription for consistency
    "response_format": "json",  # Get JSON response with timestamps
}

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = [
    "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"
]

# Error messages
ERROR_MESSAGES = {
    "file_too_large": f"Audio file size exceeds the maximum of {MAX_AUDIO_SIZE_MB}MB.",
    "unsupported_format": f"Audio format not supported. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}",
    "invalid_api_key": "Invalid or missing OpenAI API key.",
    "transcription_error": "Error transcribing audio file."
}