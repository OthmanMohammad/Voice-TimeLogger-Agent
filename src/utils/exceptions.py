"""
Custom exceptions for the Voice-TimeLogger-Agent.
Provides standardized error handling across the application.
"""

from enum import Enum
from typing import Optional, Dict, Any


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


class BaseAppException(Exception):
    """
    Base exception class for the application.
    All custom exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a base application exception.
        
        Args:
            message: Human-readable error message
            code: Error code from ErrorCode enum
            details: Additional error details
            original_exception: Original exception if this is wrapping another exception
        """
        self.message = message
        self.code = code
        self.code_value = code.value
        self.details = details or {}
        self.original_exception = original_exception
        
        # Combine all information into the error message
        full_message = f"[{code.name}] {message}"
        if details:
            full_message += f" - Details: {details}"
        if original_exception:
            full_message += f" - Original exception: {str(original_exception)}"
        
        super().__init__(full_message)


class ConfigurationError(BaseAppException):
    """Exception raised for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            original_exception=original_exception
        )


class ValidationError(BaseAppException):
    """Exception raised for data validation errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            original_exception=original_exception
        )


class ExtractionError(BaseAppException):
    """Exception raised for data extraction errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EXTRACTION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=code,
            details=details,
            original_exception=original_exception
        )


class LLMExtractionError(ExtractionError):
    """Exception raised for LLM-based extraction errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.LLM_EXTRACTION_ERROR,
            details=details,
            original_exception=original_exception
        )


class InsufficientDataError(ExtractionError):
    """Exception raised when the extracted data is incomplete or insufficient."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.INSUFFICIENT_DATA,
            details=details,
            original_exception=original_exception
        )


class TranscriptionError(BaseAppException):
    """Exception raised for speech-to-text transcription errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.TRANSCRIPTION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=code,
            details=details,
            original_exception=original_exception
        )


class StorageError(BaseAppException):
    """Exception raised for storage-related errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.STORAGE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=code,
            details=details,
            original_exception=original_exception
        )