import os
import logging
from typing import Dict, Any, List, Optional
import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Storage Interface (Adapter Pattern)
class StorageAdapter(ABC):
    """Abstract interface for storage adapters."""
    
    @abstractmethod
    async def store_data(self, data: Dict[str, Any]) -> bool:
        """
        Store data in the storage system.
        
        Args:
            data: Dictionary containing data to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def setup(self) -> None:
        """Set up the storage system if needed."""
        pass


class GoogleSheetsAdapter(StorageAdapter):
    """Adapter for Google Sheets storage."""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Initialize the Google Sheets adapter.
        
        Args:
            credentials_file: Path to the Google service account credentials file
            spreadsheet_id: ID of the Google Sheet to use
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        
        if not os.path.exists(self.credentials_file):
            raise ValueError(f"Google credentials file not found: {self.credentials_file}")
            
        self._setup_service()
        
    def _setup_service(self):
        """Set up the Google Sheets API service."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            
            self.service = build("sheets", "v4", credentials=credentials)
            self.sheet = self.service.spreadsheets()
        except Exception as e:
            logger.error(f"Error setting up Google Sheets service: {str(e)}")
            raise
    
    async def store_data(self, data: Dict[str, Any]) -> bool:
        """
        Store data in Google Sheets.
        
        Args:
            data: Dictionary containing data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format data for insertion
            row_data = self._format_data_for_sheet(data)
            
            # Insert data into sheet
            result = self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!A1",  # Assumes first sheet with headers in row 1
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row_data]}
            ).execute()
            
            logger.info(f"Data added to sheet: {result.get('updates').get('updatedRange')}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing data in Google Sheets: {str(e)}")
            return False
    
    def _format_data_for_sheet(self, data: Dict[str, Any]) -> List[Any]:
        """
        Format data for Google Sheets insertion.
        
        Args:
            data: Dictionary containing data
            
        Returns:
            List of values to insert as a row
        """
        # Define the order of columns in the sheet
        columns = [
            "timestamp",
            "customer_name",
            "meeting_date",
            "start_time",
            "end_time",
            "total_hours",
            "notes"
        ]
        
        # Add current timestamp
        data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create row data in the correct order
        row_data = []
        for column in columns:
            row_data.append(data.get(column, ""))
            
        return row_data
    
    async def setup(self) -> None:
        """
        Set up the Google Sheet with proper headers if it doesn't exist.
        """
        try:
            # Check if sheet has headers
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!1:1"
            ).execute()
            
            values = result.get("values", [])
            
            # If sheet is empty or has no headers, add them
            if not values:
                headers = [
                    "Timestamp",
                    "Customer Name",
                    "Meeting Date",
                    "Start Time",
                    "End Time",
                    "Total Hours",
                    "Notes"
                ]
                
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": [headers]}
                ).execute()
                
                logger.info("Added headers to Google Sheet")
        
        except Exception as e:
            logger.error(f"Error setting up Google Sheet: {str(e)}")
            raise


# Factory function to create storage adapter
def create_storage_adapter(adapter_type: str = "google_sheets", **kwargs) -> StorageAdapter:
    """
    Factory function to create a storage adapter.
    
    Args:
        adapter_type: Type of adapter to create
        **kwargs: Additional arguments for the adapter
        
    Returns:
        StorageAdapter instance
    """
    if adapter_type == "google_sheets":
        credentials_file = kwargs.get("credentials_file") or os.environ.get("GOOGLE_CREDENTIALS_FILE")
        spreadsheet_id = kwargs.get("spreadsheet_id") or os.environ.get("GOOGLE_SPREADSHEET_ID")
        
        return GoogleSheetsAdapter(credentials_file, spreadsheet_id)
    else:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")


# Main Storage Service
class StorageService:
    """Service to store meeting data in configured storage system."""
    
    def __init__(self, adapter: Optional[StorageAdapter] = None, adapter_type: str = "google_sheets", **kwargs):
        """
        Initialize the storage service with the specified adapter.
        
        Args:
            adapter: Storage adapter to use (if None, one will be created)
            adapter_type: Type of adapter to create if none provided
            **kwargs: Additional arguments for the adapter
        """
        self.adapter = adapter or create_storage_adapter(adapter_type, **kwargs)
    
    async def store_meeting_data(self, meeting_data: Dict[str, Any]) -> bool:
        """
        Store meeting data using the configured adapter.
        
        Args:
            meeting_data: Dictionary containing meeting data
            
        Returns:
            True if successful, False otherwise
        """
        return await self.adapter.store_data(meeting_data)
    
    async def setup(self) -> None:
        """Set up the storage system if needed."""
        await self.adapter.setup()