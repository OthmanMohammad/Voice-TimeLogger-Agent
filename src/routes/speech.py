"""
Speech processing related routes for handling audio uploads and transcription.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import os
import uuid
from datetime import datetime

from config.config import get_settings
from src.models.api import VoiceUploadRequest, TranscriptionResponse, ErrorResponse
from src.models.meeting import ProcessingResponse
from src.services.speech import SpeechManager
from src.services.extraction import ExtractionManager
from src.services.storage import StorageManager
from src.services.notification import NotificationManager
from src.utils import get_logger, ErrorCode, TranscriptionError, ExtractionError
from src.utils.exceptions import BaseAppException, StorageError
from src.enums import ProcessingStatus, StorageStatus
from src.enums.notification import NotificationStatus

# Setup router
router = APIRouter(
    prefix="/speech",
    tags=["speech"],
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)

logger = get_logger(__name__)

async def get_speech_manager():
    """Dependency to get speech manager instance."""
    settings = get_settings()
    try:
        manager = SpeechManager(
            openai_api_key=settings.OPENAI_API_KEY,
            storage_dir=settings.TEMP_DIR
        )
        yield manager
    except Exception as e:
        logger.error(f"Error creating SpeechManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize speech service: {str(e)}"
        )

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

async def get_storage_manager():
    """Dependency to get storage manager instance."""
    settings = get_settings()
    try:
        manager = StorageManager(
            google_credentials_file=settings.GOOGLE_CREDENTIALS_FILE,
            google_spreadsheet_id=settings.GOOGLE_SPREADSHEET_ID
        )
        yield manager
    except Exception as e:
        logger.error(f"Error creating StorageManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize storage service: {str(e)}"
        )
    
async def get_notification_manager():
    """Dependency to get notification manager instance."""
    try:
        manager = NotificationManager()
        yield manager
    except Exception as e:
        logger.error(f"Error creating NotificationManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize notification service: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=ProcessingResponse,
    summary="Upload and process an audio recording",
    description="Upload an audio recording of a meeting summary, transcribe it, and extract meeting details"
)
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    customer_hint: Optional[str] = Form(None),
    meeting_date_hint: Optional[str] = Form(None),
    notify: Optional[bool] = Form(None),
    speech_manager: SpeechManager = Depends(get_speech_manager),
    extraction_manager: ExtractionManager = Depends(get_extraction_manager),
    storage_manager: StorageManager = Depends(get_storage_manager),
    notification_manager: NotificationManager = Depends(get_notification_manager)
):
    """
    Upload an audio file, transcribe it, extract meeting data, and store it.
    
    Args:
        file: Audio file upload
        customer_hint: Optional hint about the customer name
        meeting_date_hint: Optional hint about the meeting date
        notify: Whether to send notification after processing (overrides default setting if provided)
        speech_manager: SpeechManager instance
        extraction_manager: ExtractionManager instance
        storage_manager: StorageManager instance
        notification_manager: NotificationManager instance
        
    Returns:
        Processed meeting data
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{request_id}] Processing audio upload: {file.filename}")
    
    # Get settings
    settings = get_settings()
    
    # Determine if notifications should be sent
    # If notify param is explicitly provided, use it; otherwise use the default from settings
    should_notify = notify if notify is not None else settings.NOTIFICATIONS_DEFAULT
    
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        if not file_ext or file_ext.lstrip(".") not in ["mp3", "wav", "m4a", "mpeg", "mpga", "webm"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Supported formats: mp3, wav, m4a, mpeg, mpga, webm"
            )
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Process audio in the background if it's large
        if len(file_content) > 5 * 1024 * 1024:  # If file > 5MB
            # Schedule background processing
            processing_id = f"upload_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request_id}"
            
            # Return immediate response
            return ProcessingResponse(
                success=True,
                message=f"Audio upload received ({len(file_content)} bytes). Processing in background. Check status with processing ID: {processing_id}",
                data=None
            )
        
        # For smaller files, process immediately
        transcription_result = await speech_manager.transcribe_audio_data(file_content)
        
        if transcription_result.get("processing_status") != "completed":
            return ProcessingResponse(
                success=False,
                message=f"Transcription failed: {transcription_result.get('error', 'Unknown error')}",
                data=None
            )
        
        # Extract meeting data from transcription
        transcribed_text = transcription_result.get("text", "")
        
        # Add hints to the text if provided
        if customer_hint or meeting_date_hint:
            hint_text = "Additional information: "
            if customer_hint:
                hint_text += f"Customer is {customer_hint}. "
            if meeting_date_hint:
                hint_text += f"Meeting date is {meeting_date_hint}."
            
            transcribed_text = f"{transcribed_text}\n\n{hint_text}"
        
        # Extract meeting data
        meeting_data = await extraction_manager.extract(transcribed_text)
        
        # Store meeting data
        try:
            storage_result = await storage_manager.store_meeting_data(meeting_data)
            meeting_data["storage_status"] = storage_result.get("storage_status")
        except StorageError as e:
            logger.warning(f"[{request_id}] Storage error (continuing): {str(e)}")
            meeting_data["storage_status"] = StorageStatus.FAILED.value
            meeting_data["storage_error"] = str(e)

        # notification logic
        if meeting_data.get("storage_status") == StorageStatus.STORED.value:
            if should_notify and (settings.ENABLE_EMAIL_NOTIFICATIONS or settings.ENABLE_SLACK_NOTIFICATIONS):
                try:
                    notification_result = await notification_manager.send_notification(meeting_data)
                    meeting_data["notification_status"] = notification_result.get("overall_status")
                    meeting_data["notification_channels"] = notification_result.get("channels", [])
                except Exception as e:
                    logger.warning(f"[{request_id}] Notification error (continuing): {str(e)}")
                    meeting_data["notification_status"] = NotificationStatus.FAILED.value
                    meeting_data["notification_error"] = str(e)
            else:
                meeting_data["notification_status"] = NotificationStatus.SKIPPED.value
                if not should_notify:
                    meeting_data["notification_message"] = "Notifications not requested"
                elif not (settings.ENABLE_EMAIL_NOTIFICATIONS or settings.ENABLE_SLACK_NOTIFICATIONS):
                    meeting_data["notification_message"] = "No notification channels enabled"
        
        # Return the results
        return ProcessingResponse(
            success=True,
            message="Audio processed and data stored successfully",
            data=meeting_data
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
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


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio without extraction",
    description="Upload an audio file and get the transcribed text without extracting meeting details"
)
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    speech_manager: SpeechManager = Depends(get_speech_manager)
):
    """
    Transcribe an audio file without extracting meeting data.
    
    Args:
        file: Audio file upload
        speech_manager: SpeechManager instance
        
    Returns:
        Transcription results
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{request_id}] Transcribing audio: {file.filename}")
    
    try:
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Transcribe the audio
        transcription_result = await speech_manager.transcribe_audio_data(file_content)
        
        return transcription_result
        
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
    
@router.post(
    "/process",
    response_model=ProcessingResponse,
    summary="Process an audio recording without storage or notifications",
    description="Upload an audio recording, transcribe it, and extract meeting details without storing or sending notifications"
)
async def process_audio(
    request: Request,
    file: UploadFile = File(...),
    customer_hint: Optional[str] = Form(None),
    meeting_date_hint: Optional[str] = Form(None),
    speech_manager: SpeechManager = Depends(get_speech_manager),
    extraction_manager: ExtractionManager = Depends(get_extraction_manager)
):
    """
    Process an audio file (transcribe and extract) without storage or notifications.
    
    Args:
        file: Audio file upload
        customer_hint: Optional hint about the customer name
        meeting_date_hint: Optional hint about the meeting date
        speech_manager: SpeechManager instance
        extraction_manager: ExtractionManager instance
        
    Returns:
        Processed meeting data (without storage or notification)
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info(f"[{request_id}] Processing audio: {file.filename}")
    
    try:
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        if not file_ext or file_ext.lstrip(".") not in ["mp3", "wav", "m4a", "mpeg", "mpga", "webm"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Supported formats: mp3, wav, m4a, mpeg, mpga, webm"
            )
        
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Transcribe the audio
        transcription_result = await speech_manager.transcribe_audio_data(file_content)
        
        if transcription_result.get("processing_status") != "completed":
            return ProcessingResponse(
                success=False,
                message=f"Transcription failed: {transcription_result.get('error', 'Unknown error')}",
                data=None
            )
        
        # Extract meeting data from transcription
        transcribed_text = transcription_result.get("text", "")
        
        if customer_hint or meeting_date_hint:
            hint_text = "Additional information: "
            if customer_hint:
                hint_text += f"Customer is {customer_hint}. "
            if meeting_date_hint:
                hint_text += f"Meeting date is {meeting_date_hint}."
            
            transcribed_text = f"{transcribed_text}\n\n{hint_text}"
        
        # Extract meeting data
        meeting_data = await extraction_manager.extract(transcribed_text)
        
        return ProcessingResponse(
            success=True,
            message="Audio processed successfully",
            data=meeting_data
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
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