"""
Speech-to-text module for Voice-TimeLogger-Agent.
Provides modular speech recognition capabilities with different providers.
"""

from src.services.speech.speech_manager import SpeechManager
from src.services.speech.config import DEFAULT_TRANSCRIPTION_CONFIG

# Export the main classes
__all__ = [
    "SpeechManager",
    "DEFAULT_TRANSCRIPTION_CONFIG"
]