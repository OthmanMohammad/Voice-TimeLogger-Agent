"""
API-specific Pydantic models for request and response objects.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from src.enums import ProcessingStatus, ExtractionStatus, ErrorCode


class VoiceUploadRequest(BaseModel):
    """Request model for voice upload endpoints"""
    
    customer_hint: Optional[str] = Field(
        None, 
        description="Optional hint about the customer name to improve extraction"
    )
    meeting_date_hint: Optional[str] = Field(
        None, 
        description="Optional hint about the meeting date to improve extraction"
    )
    notify: bool = Field(
        False, 
        description="Whether to send notification after processing"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "customer_hint": "Acme Corp",
                "meeting_date_hint": "2025-03-31",
                "notify": True
            }
        }


class TranscriptionResponse(BaseModel):
    """Response model for transcription endpoints"""
    
    processing_id: str = Field(..., description="Unique ID for this processing request")
    processing_status: str = Field(..., description="Status of the processing request")
    text: str = Field(..., description="Transcribed text from the audio")
    model: Optional[str] = Field(None, description="Model used for transcription")
    file_path: Optional[str] = Field(None, description="Path to the stored audio file")
    timestamp: str = Field(..., description="Timestamp of processing")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed segments with timestamps if available")
    
    class Config:
        schema_extra = {
            "example": {
                "processing_id": "transcribe_20250401123456",
                "processing_status": "completed",
                "text": "I had a meeting with Acme Corp from 2 PM to 3:30 PM.",
                "model": "whisper-1",
                "file_path": "/tmp/meeting_recordings/meeting_20250401123456.mp3",
                "timestamp": "2025-04-01 12:34:56",
                "segments": None
            }
        }


class MeetingDataResponse(BaseModel):
    """Response model for meeting data extraction endpoints"""
    
    meeting_data: Dict[str, Any] = Field(..., description="Extracted meeting data")
    extraction_status: str = Field(..., description="Status of the extraction process")
    timestamp: str = Field(..., description="Timestamp of extraction")
    
    class Config:
        schema_extra = {
            "example": {
                "meeting_data": {
                    "customer_name": "Acme Corp",
                    "meeting_date": "2025-03-31",
                    "start_time": "14:00",
                    "end_time": "15:30",
                    "total_hours": 1.5,
                    "notes": "Discussed project requirements"
                },
                "extraction_status": "complete",
                "timestamp": "2025-04-01 12:34:56"
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    error_code: int = Field(..., description="Error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid audio format",
                "error_code": 4002,
                "error_details": {
                    "format": "aac",
                    "supported_formats": ["mp3", "wav", "m4a"]
                },
                "request_id": "req_a1b2c3d4e5f6"
            }
        }