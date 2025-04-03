"""
Storage manager for handling meeting data storage.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from config.config import get_settings
from src.utils import (
    get_logger,
    log_async_function_call,
    format_structured_log,
    StorageError
)
from src.enums import StorageStatus

logger = get_logger(__name__)

class StorageManager:
    """
    Manager for storing meeting data.
    Currently supports Google Sheets storage.
    """
    
    def __init__(
        self,
        google_credentials_file: Optional[str] = None,
        google_spreadsheet_id: Optional[str] = None
    ):
        """
        Initialize the storage manager.
        
        Args:
            google_credentials_file: Path to Google service account credentials
            google_spreadsheet_id: ID of Google Spreadsheet
            
        Raises:
            StorageError: If initialization fails
        """
        # Generate unique ID for this storage manager instance
        self.instance_id = str(uuid.uuid4())[:8]
        logger.info(f"Initializing StorageManager instance {self.instance_id}")
        
        try:
            settings = get_settings()
            
            # Lazy-load Google Sheets storage when needed
            self._google_sheets_storage = None
            self.google_credentials_file = google_credentials_file or settings.GOOGLE_CREDENTIALS_FILE
            self.google_spreadsheet_id = google_spreadsheet_id or settings.GOOGLE_SPREADSHEET_ID
            
            logger.debug(
                format_structured_log(
                    f"StorageManager initialized",
                    {
                        "instance_id": self.instance_id,
                        "google_spreadsheet_id": self.google_spreadsheet_id
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Error initializing StorageManager: {str(e)}", exc_info=True)
            raise StorageError(
                f"Failed to initialize storage manager: {str(e)}",
                original_exception=e
            )
    
    @log_async_function_call(logger)
    async def store_meeting_data(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store meeting data using the appropriate storage backend.
        Currently only supports Google Sheets.
        
        Args:
            meeting_data: Meeting data to store
            
        Returns:
            Storage result with status
            
        Raises:
            StorageError: If storage fails
        """
        storage_id = f"store_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "storage_id": storage_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "storage_status": StorageStatus.PENDING.value
        }
        
        logger.info(
            format_structured_log(
                f"Starting storage process [{storage_id}]",
                {
                    "instance_id": self.instance_id,
                    "customer": meeting_data.get("customer_name")
                }
            )
        )
        
        try:
            # Lazy initialize Google Sheets storage
            if not self._google_sheets_storage:
                from src.services.storage.google_sheets_storage import GoogleSheetsStorage
                
                self._google_sheets_storage = GoogleSheetsStorage(
                    credentials_file=self.google_credentials_file,
                    spreadsheet_id=self.google_spreadsheet_id
                )
            
            # Store data using Google Sheets
            storage_result = await self._google_sheets_storage.store_meeting_data(meeting_data)
            
            # Update result with storage result
            result.update(storage_result)
            
            logger.info(
                format_structured_log(
                    f"Storage completed [{storage_id}]",
                    {
                        "storage_status": result.get("storage_status"),
                        "instance_id": self.instance_id
                    }
                )
            )
            
            return result
            
        except Exception as e:
            result["storage_status"] = StorageStatus.FAILED.value
            
            error_msg = f"Storage error: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{storage_id}]",
                    {
                        "instance_id": self.instance_id,
                        "status": result["storage_status"]
                    }
                ),
                exc_info=True
            )
            
            result["error"] = str(e)
            
            if not isinstance(e, StorageError):
                e = StorageError(
                    error_msg,
                    original_exception=e
                )
            
            raise e