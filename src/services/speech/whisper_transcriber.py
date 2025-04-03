"""
OpenAI Whisper transcriber implementation.
Provides speech-to-text conversion using OpenAI's Whisper API.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime

from openai import OpenAI
from openai import OpenAIError

from config.config import get_settings
from src.services.speech.config import (
    DEFAULT_TRANSCRIPTION_CONFIG,
    ERROR_MESSAGES
)
from src.utils import (
    get_logger,
    log_async_function_call,
    format_structured_log,
    TranscriptionError
)
from src.enums import ProcessingStatus, ErrorCode

logger = get_logger(__name__)

class WhisperTranscriber:
    """
    Provides speech-to-text functionality using OpenAI's Whisper API.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            api_key: OpenAI API key (falls back to environment variable)
            config: Configuration for the transcription service
            
        Raises:
            TranscriptionError: If API key is missing or invalid
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            error_msg = "OpenAI API key not provided or found in environment"
            logger.error(error_msg)
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.VALIDATION_ERROR
            )
        
        # Set up configuration with defaults
        self.config = DEFAULT_TRANSCRIPTION_CONFIG.copy()
        if config:
            self.config.update(config)
        
        try:
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.api_key)
            logger.info(
                format_structured_log(
                    "WhisperTranscriber initialized", 
                    {"model": self.config.get("model")}
                )
            )
        except Exception as e:
            error_msg = f"Failed to initialize WhisperTranscriber: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.VALIDATION_ERROR,
                original_exception=e
            )
    
    def transcribe_audio_file(self, audio_file, params):
        """
        Helper method to make the actual API call to OpenAI.
        This separates the blocking API call from the async interface.
        
        Args:
            audio_file: Open file handle to the audio file
            params: Parameters for the transcription API
            
        Returns:
            OpenAI API response
        """
        # Create a clean copy of params to avoid issues with unsupported parameters
        api_params = {
            "model": params.get("model", "whisper-1")
        }
        
        # Add supported parameters
        if "language" in params:
            api_params["language"] = params["language"]
        if "temperature" in params:
            api_params["temperature"] = params["temperature"]
        if "response_format" in params:
            api_params["response_format"] = params["response_format"]
            
        # Make the API call with only supported parameters
        return self.client.audio.transcriptions.create(
            file=audio_file,
            **api_params
        )
    
    @log_async_function_call(logger)
    async def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file using OpenAI's Whisper API.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with transcription results
            
        Raises:
            TranscriptionError: If transcription fails
        """
        if not os.path.exists(file_path):
            error_msg = f"Audio file not found: {file_path}"
            logger.error(error_msg)
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.VALIDATION_ERROR
            )
        
        # Generate a unique ID for tracking this transcription
        transcription_id = f"whisper_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(
            format_structured_log(
                f"Starting transcription [{transcription_id}]", 
                {"file": file_path, "model": self.config.get("model")}
            )
        )
        
        try:
            # Prepare the API call parameters
            params = self.config.copy()
            
            # Open the file and transcribe
            with open(file_path, "rb") as audio_file:
                # Use asyncio to run the blocking API call in a thread pool
                response = await asyncio.to_thread(
                    self.transcribe_audio_file,
                    audio_file,
                    params
                )
            
            # Process the response
            result = {
                "text": response.text,
                "provider": "openai_whisper",
                "model": self.config.get("model"),
                "processing_status": ProcessingStatus.COMPLETED.value,
                "transcription_id": transcription_id
            }
            
            # Add timestamps if available
            if hasattr(response, 'segments'):
                result["segments"] = response.segments
            
            # Log success
            logger.info(
                format_structured_log(
                    f"Transcription completed successfully [{transcription_id}]", 
                    {
                        "text_length": len(result["text"]), 
                        "status": result["processing_status"]
                    }
                )
            )
            
            return result
            
        except OpenAIError as e:
            error_msg = f"OpenAI API error during transcription: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{transcription_id}]", 
                    {"file": file_path, "status": ProcessingStatus.FAILED.value}
                ),
                exc_info=True
            )
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.TRANSCRIPTION_ERROR,
                details={"transcription_id": transcription_id},
                original_exception=e
            )
            
        except Exception as e:
            error_msg = f"Error during transcription: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{transcription_id}]", 
                    {"file": file_path, "status": ProcessingStatus.FAILED.value}
                ),
                exc_info=True
            )
            raise TranscriptionError(
                error_msg,
                code=ErrorCode.TRANSCRIPTION_ERROR,
                details={"transcription_id": transcription_id},
                original_exception=e
            )