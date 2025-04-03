"""
Audio processing utilities for the speech-to-text service.
Handles validation, preprocessing, and storage of audio files.
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from src.services.speech.config import (
    DEFAULT_AUDIO_DIR,
    SUPPORTED_AUDIO_FORMATS,
    MAX_AUDIO_SIZE_MB,
    ERROR_MESSAGES
)
from src.utils import (
    get_logger,
    format_structured_log,
    TranscriptionError
)
from src.enums import ProcessingStatus, ErrorCode

logger = get_logger(__name__)

class AudioProcessor:
    """
    Handles audio file processing, validation, and storage.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the audio processor.
        
        Args:
            storage_dir: Directory for storing audio files (defaults to tmp/meeting_recordings)
        """
        self.storage_dir = storage_dir or DEFAULT_AUDIO_DIR
        self._ensure_storage_dir()
        
        logger.info(f"AudioProcessor initialized with storage directory: {self.storage_dir}")
    
    def _ensure_storage_dir(self) -> None:
        """
        Ensure the storage directory exists.
        """
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.debug(f"Ensured storage directory exists: {self.storage_dir}")
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an audio file for transcription.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return False, f"File not found: {file_path}"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            logger.warning(
                format_structured_log(
                    f"Audio file too large", 
                    {"file": file_path, "size_mb": file_size_mb, "max_mb": MAX_AUDIO_SIZE_MB}
                )
            )
            return False, ERROR_MESSAGES["file_too_large"]
        
        # Check file format
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if file_ext not in SUPPORTED_AUDIO_FORMATS:
            logger.warning(
                format_structured_log(
                    f"Unsupported audio format", 
                    {"file": file_path, "format": file_ext}
                )
            )
            return False, ERROR_MESSAGES["unsupported_format"]
        
        logger.debug(f"Audio file validated successfully: {file_path}")
        return True, None
    
    def save_audio_file(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """
        Save audio data to a file in the storage directory.
        
        Args:
            audio_data: Raw audio data in bytes
            filename: Optional filename (if None, generates a unique name)
            
        Returns:
            Path to the saved audio file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"meeting_{timestamp}_{unique_id}.mp3"
        
        file_path = os.path.join(self.storage_dir, filename)
        
        # Save the file
        try:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            
            logger.info(
                format_structured_log(
                    f"Audio file saved", 
                    {"file_path": file_path, "size_bytes": len(audio_data)}
                )
            )
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"Failed to save audio file: {str(e)}",
                code=ErrorCode.AUDIO_PROCESSING_ERROR,
                original_exception=e
            )
    
    def copy_audio_file(self, source_path: str, preserve_filename: bool = False) -> str:
        """
        Copy an audio file to the storage directory.
        
        Args:
            source_path: Path to the source audio file
            preserve_filename: Whether to keep the original filename
            
        Returns:
            Path to the copied audio file in the storage directory
        """
        # Validate the source file
        is_valid, error = self.validate_audio_file(source_path)
        if not is_valid:
            raise TranscriptionError(
                f"Invalid audio file: {error}",
                code=ErrorCode.UNSUPPORTED_AUDIO_FORMAT
            )
        
        # Generate destination path
        if preserve_filename:
            dest_filename = os.path.basename(source_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_ext = os.path.splitext(source_path)[1]
            dest_filename = f"meeting_{timestamp}_{unique_id}{file_ext}"
        
        dest_path = os.path.join(self.storage_dir, dest_filename)
        
        # Copy the file
        try:
            shutil.copy2(source_path, dest_path)
            
            logger.info(
                format_structured_log(
                    f"Audio file copied to storage", 
                    {"source": source_path, "destination": dest_path}
                )
            )
            return dest_path
            
        except Exception as e:
            logger.error(f"Error copying audio file: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"Failed to copy audio file: {str(e)}",
                code=ErrorCode.AUDIO_PROCESSING_ERROR,
                original_exception=e
            )
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Remove audio files older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files deleted
        """
        if not os.path.exists(self.storage_dir):
            return 0
        
        count = 0
        now = datetime.now()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(self.storage_dir):
            if filename == '.gitkeep':
                continue
                
            file_path = os.path.join(self.storage_dir, filename)
            if not os.path.isfile(file_path):
                continue
                
            # Get file modification time
            file_mtime = os.path.getmtime(file_path)
            file_time = datetime.fromtimestamp(file_mtime)
            age_seconds = (now - file_time).total_seconds()
            
            if age_seconds > max_age_seconds:
                try:
                    os.remove(file_path)
                    count += 1
                    logger.debug(f"Removed old audio file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove old file {file_path}: {str(e)}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} old audio files from {self.storage_dir}")
        
        return count