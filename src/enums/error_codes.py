"""
Error code enums for the Voice-TimeLogger-Agent.
"""

from enum import Enum, auto


class ErrorCode(Enum):
    """Enum of error codes for categorizing exceptions."""
    
    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    CONFIGURATION_ERROR = 1001
    VALIDATION_ERROR = 1002
    
    # Service errors (2000-2999)
    SERVICE_UNAVAILABLE = 2000
    
    # Extraction errors (3000-3999)
    EXTRACTION_ERROR = 3000
    LLM_EXTRACTION_ERROR = 3001
    INSUFFICIENT_DATA = 3002
    
    # Speech-to-text errors (4000-4999)
    TRANSCRIPTION_ERROR = 4000
    AUDIO_PROCESSING_ERROR = 4001
    UNSUPPORTED_AUDIO_FORMAT = 4002
    
    # Storage errors (5000-5999)
    STORAGE_ERROR = 5000
    GOOGLE_SHEETS_ERROR = 5001
    SHEET_NOT_FOUND = 5002
    
    # API errors (6000-6999)
    API_ERROR = 6000
    ENDPOINT_NOT_FOUND = 6001
    REQUEST_VALIDATION_ERROR = 6002