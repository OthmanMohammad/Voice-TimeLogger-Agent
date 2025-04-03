"""
Routes for extracting meeting data from text.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import Dict, Any, Optional
import uuid

from src.models.api import MeetingDataResponse, ErrorResponse
from src.models.meeting import MeetingData, ProcessingResponse
from src.services.extraction import ExtractionManager
from src.utils import get_logger
from src.utils.exceptions import BaseAppException
from config.config import get_settings

# Setup router
router = APIRouter(
    prefix="/meetings",
    tags=["meetings"],
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)

logger = get_logger(__name__)

async def get_extraction_manager():
    """Dependency to get extraction manager instance."""
    settings = get_settings()
    try:
        manager = ExtractionManager(
            openai_api_key=settings.OPENAI_API_KEY
        )
        yield manager
    except Exception as e:
        logger.error(f"Error creating ExtractionManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize extraction service: {str(e)}"
        )


@router.post(
    "/extract",
    response_model=MeetingDataResponse,
    summary="Extract meeting data from text",
    description="Analyze text and extract structured meeting data"
)
async def extract_meeting_data(
    request: Request,
    text: str = Body(..., embed=True),
    customer_hint: Optional[str] = Body(None, embed=True),
    meeting_date_hint: Optional[str] = Body(None, embed=True),
    extraction_manager: ExtractionManager = Depends(get_extraction_manager)
):
    """
    Extract meeting data from text.
    
    Args:
        text: Text to extract meeting data from
        customer_hint: Optional hint about the customer name
        meeting_date_hint: Optional hint about the meeting date
        extraction_manager: ExtractionManager instance
        
    Returns:
        Extracted meeting data
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{request_id}] Extracting meeting data from text ({len(text)} chars)")
    
    try:
        # Add hints to the text if provided
        extraction_text = text
        
        if customer_hint or meeting_date_hint:
            hint_text = "Additional information: "
            if customer_hint:
                hint_text += f"Customer is {customer_hint}. "
            if meeting_date_hint:
                hint_text += f"Meeting date is {meeting_date_hint}."
            
            extraction_text = f"{text}\n\n{hint_text}"
        
        # Extract meeting data
        meeting_data = await extraction_manager.extract(extraction_text)
        
        # Return the results
        return MeetingDataResponse(
            meeting_data=meeting_data,
            extraction_status=meeting_data.get("extraction_status", "unknown"),
            timestamp=meeting_data.get("timestamp", "")
        )
        
    except BaseAppException as e:
        logger.error(f"[{request_id}] Application error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_code": e.code_value,
                "error_details": e.details,
                "request_id": request_id
            }
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )