"""
Speech manager that handles transcription of audio files.
Main entry point for speech-to-text functionality.
"""

import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from config.config import get_settings
from src.services.speech.audio_processor import AudioProcessor
from src.services.speech.whisper_transcriber import WhisperTranscriber
from src.services.speech.config import DEFAULT_TRANSCRIPTION_CONFIG
from src.utils import (
    get_logger,
    log_async_function_call,
    format_structured_log,
    TranscriptionError
)
from src.enums import ProcessingStatus, ErrorCode

logger = get_logger(__name__)

class SpeechManager:
    """
    Manager for speech-to-text processing.
    Handles audio files and coordinates transcription.
    """
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        storage_dir: Optional[str] = None,
        transcription_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the speech manager.
        
        Args:
            openai_api_key: API key for OpenAI (if None, read from settings)
            storage_dir: Directory for audio storage
            transcription_config: Configuration for transcription
            
        Raises:
            TranscriptionError: If initialization fails
        """
        # Generate unique ID for this manager instance
        self.instance_id = str(uuid.uuid4())[:8]
        logger.info(f"Initializing SpeechManager instance {self.instance_id}")
        
        try:
            if not openai_api_key:
                settings = get_settings()
                self.openai_api_key = settings.OPENAI_API_KEY
            else:
                self.openai_api_key = openai_api_key
            
            if not storage_dir:
                settings = get_settings()
                self.storage_dir = settings.TEMP_DIR
            else:
                self.storage_dir = storage_dir
            
            # Initialize components
            self.audio_processor = AudioProcessor(storage_dir=self.storage_dir)
            self.transcriber = WhisperTranscriber(
                api_key=self.openai_api_key,
                config=transcription_config
            )
            
            logger.debug(
                format_structured_log(
                    f"SpeechManager initialized",
                    {
                        "instance_id": self.instance_id,
                        "storage_dir": self.storage_dir
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Error initializing SpeechManager: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"Failed to initialize speech manager: {str(e)}",
                code=ErrorCode.VALIDATION_ERROR,
                original_exception=e
            )
    
    @log_async_function_call(logger)
    async def transcribe_audio_data(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe audio data (bytes).
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            Dictionary with transcription results
            
        Raises:
            TranscriptionError: If transcription fails
        """
        # Create a processing ID to trace this specific request
        processing_id = f"transcribe_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "processing_id": processing_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processing_status": ProcessingStatus.PENDING.value
        }
        
        logger.info(
            format_structured_log(
                f"Starting audio transcription [{processing_id}]",
                {"size_bytes": len(audio_data), "instance_id": self.instance_id}
            )
        )
        
        try:
            result["processing_status"] = ProcessingStatus.PROCESSING.value
            
            # Save the audio data to a file
            file_path = self.audio_processor.save_audio_file(audio_data)
            result["file_path"] = file_path
            
            # Transcribe the audio file
            transcription_result = await self.transcriber.transcribe_file(file_path)
            
            # Update result with transcription data
            result.update(transcription_result)
            result["processing_status"] = ProcessingStatus.COMPLETED.value
            
            logger.info(
                format_structured_log(
                    f"Audio transcription completed [{processing_id}]",
                    {
                        "text_length": len(result.get("text", "")),
                        "status": result["processing_status"]
                    }
                )
            )
            
        except Exception as e:
            result["processing_status"] = ProcessingStatus.FAILED.value
            
            error_msg = f"Transcription error: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{processing_id}]",
                    {
                        "instance_id": self.instance_id,
                        "status": result["processing_status"]
                    }
                ),
                exc_info=True
            )
            
            result["error"] = str(e)
            
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.TRANSCRIPTION_ERROR,
                details={"processing_id": processing_id},
                original_exception=e
            )
        
        return result
    
    @log_async_function_call(logger)
    async def transcribe_audio_file(self, file_path: str, copy_to_storage: bool = True) -> Dict[str, Any]:
        """
        Transcribe an existing audio file.
        
        Args:
            file_path: Path to the audio file
            copy_to_storage: Whether to copy the file to the storage directory
            
        Returns:
            Dictionary with transcription results
            
        Raises:
            TranscriptionError: If transcription fails
        """
        # Create a processing ID to trace this specific request
        processing_id = f"transcribe_file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "processing_id": processing_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processing_status": ProcessingStatus.PENDING.value,
            "original_file": file_path
        }
        
        logger.info(
            format_structured_log(
                f"Starting file transcription [{processing_id}]",
                {"file": file_path, "instance_id": self.instance_id}
            )
        )
        
        try:
            result["processing_status"] = ProcessingStatus.PROCESSING.value
            
            # Validate the audio file
            is_valid, error = self.audio_processor.validate_audio_file(file_path)
            if not is_valid:
                raise TranscriptionError(
                    f"Invalid audio file: {error}",
                    code=ErrorCode.UNSUPPORTED_AUDIO_FORMAT
                )
            
            # Copy to storage if requested
            if copy_to_storage:
                file_path = self.audio_processor.copy_audio_file(file_path)
                result["file_path"] = file_path
            
            # Transcribe the audio file
            transcription_result = await self.transcriber.transcribe_file(file_path)
            
            # Update result with transcription data
            result.update(transcription_result)
            result["processing_status"] = ProcessingStatus.COMPLETED.value
            
            logger.info(
                format_structured_log(
                    f"File transcription completed [{processing_id}]",
                    {
                        "text_length": len(result.get("text", "")),
                        "status": result["processing_status"]
                    }
                )
            )
            
        except Exception as e:
            result["processing_status"] = ProcessingStatus.FAILED.value
            
            error_msg = f"File transcription error: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{processing_id}]",
                    {
                        "instance_id": self.instance_id,
                        "status": result["processing_status"]
                    }
                ),
                exc_info=True
            )
            
            result["error"] = str(e)
            
            # Propagate the exception
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.TRANSCRIPTION_ERROR,
                details={"processing_id": processing_id},
                original_exception=e
            )
        
        return result
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old audio files.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files deleted
        """
        return self.audio_processor.cleanup_old_files(max_age_hours)