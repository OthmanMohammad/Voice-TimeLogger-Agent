from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MeetingData(BaseModel):
    """Pydantic model for meeting data"""
    
    customer_name: Optional[str] = Field(None, description="Name of the customer/client")
    meeting_date: Optional[str] = Field(None, description="Date of the meeting (YYYY-MM-DD)")
    start_time: Optional[str] = Field(None, description="Start time of the meeting")
    end_time: Optional[str] = Field(None, description="End time of the meeting")
    total_hours: Optional[str] = Field(None, description="Total duration in 'Xh Ym' format")
    notes: Optional[str] = Field(None, description="Meeting notes or additional information")
    timestamp: Optional[str] = Field(None, description="Timestamp when the record was created")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_name": "Acme Corp",
                "meeting_date": "2025-03-31",
                "start_time": "10:00 AM",
                "end_time": "11:30 AM",
                "total_hours": "1h 30m",
                "notes": "Discussed project requirements and timeline",
                "timestamp": "2025-03-31 12:00:00"
            }
        }


class ProcessingResponse(BaseModel):
    """Response model for audio processing endpoints"""
    
    success: bool = Field(..., description="Whether the processing was successful")
    message: str = Field(..., description="Description of the result")
    data: Optional[MeetingData] = Field(None, description="Extracted meeting data")