"""
Status code enums for the Voice-TimeLogger-Agent.
Used for internal state tracking and API responses.
"""

from enum import Enum, auto


class ProcessingStatus(Enum):
    """Status codes for audio processing pipeline."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ExtractionStatus(Enum):
    """Status codes for data extraction processes."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class StorageStatus(Enum):
    """Status codes for storage operations."""
    
    PENDING = "pending"
    STORED = "stored"
    FAILED = "failed"