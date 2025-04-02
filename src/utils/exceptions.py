"""
Custom exceptions for the Voice-TimeLogger-Agent.
Provides standardized error handling across the application.
"""

from typing import Optional, Dict, Any

from src.enums import ErrorCode


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