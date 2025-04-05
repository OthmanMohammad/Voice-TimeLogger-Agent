"""
Enums package for the Voice-TimeLogger-Agent.
"""

from src.enums.error_codes import ErrorCode
from src.enums.log_levels import LogLevel
from src.enums.notification import NotificationStatus, NotificationChannel
from src.enums.status_codes import ProcessingStatus, ExtractionStatus, StorageStatus

__all__ = [
    # Error codes
    "ErrorCode",
    
    # Log levels
    "LogLevel",
    
    # Status codes
    "ProcessingStatus",
    "ExtractionStatus",
    "StorageStatus",

    # notification enums
    "NotificationStatus",
    "NotificationChannel",
]