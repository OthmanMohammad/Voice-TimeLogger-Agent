"""
Google Sheets implementation for storing meeting data.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.config import get_settings
from src.services.storage.config import (
    DEFAULT_SHEET_NAME,
    DEFAULT_SHEET_HEADERS,
    MEETING_DATA_TO_SHEET_MAPPING
)
from src.utils import (
    get_logger,
    format_structured_log,
    StorageError,
    ErrorCode
)
from src.enums import StorageStatus

logger = get_logger(__name__)

class GoogleSheetsStorage:
    """
    Storage implementation using Google Sheets.
    """
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None
    ):
        """
        Initialize Google Sheets storage.
        
        Args:
            credentials_file: Path to service account JSON key file
            spreadsheet_id: ID of the Google Spreadsheet to use
            sheet_name: Name of the sheet to store data in
            
        Raises:
            StorageError: If initialization fails
        """
        try:
            settings = get_settings()
            
            self.credentials_file = credentials_file or settings.GOOGLE_CREDENTIALS_FILE
            self.spreadsheet_id = spreadsheet_id or settings.GOOGLE_SPREADSHEET_ID
            self.sheet_name = sheet_name or DEFAULT_SHEET_NAME
            
            if not self.credentials_file or not os.path.exists(self.credentials_file):
                raise StorageError(
                    "Google credentials file not found",
                    code=ErrorCode.STORAGE_ERROR
                )
                
            if not self.spreadsheet_id:
                raise StorageError(
                    "Google Spreadsheet ID not provided",
                    code=ErrorCode.STORAGE_ERROR
                )
            
            self.service = self._create_sheets_service()
            
            logger.info(
                format_structured_log(
                    "GoogleSheetsStorage initialized",
                    {
                        "spreadsheet_id": self.spreadsheet_id,
                        "sheet_name": self.sheet_name
                    }
                )
            )
            
        except StorageError:
            # Re-raise storage errors
            raise
            
        except Exception as e:
            logger.error(f"Error initializing GoogleSheetsStorage: {str(e)}", exc_info=True)
            raise StorageError(
                f"Failed to initialize Google Sheets storage: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )
    
    def _create_sheets_service(self):
        """
        Create a Google Sheets API service.
        
        Returns:
            Google Sheets API service
            
        Raises:
            StorageError: If service creation fails
        """
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Error creating Google Sheets service: {str(e)}", exc_info=True)
            raise StorageError(
                f"Failed to create Google Sheets service: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )
    
    async def initialize_sheet(self) -> bool:
        """
        Initialize the sheet with headers if it doesn't exist.
        
        Returns:
            True if initialization was successful
            
        Raises:
            StorageError: If initialization fails
        """
        # asyncio to run blocking IO in a thread
        try:
            return await asyncio.to_thread(self._initialize_sheet_sync)
        except Exception as e:
            logger.error(f"Error initializing sheet: {str(e)}", exc_info=True)
            raise StorageError(
                f"Failed to initialize sheet: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )
    
    def _initialize_sheet_sync(self) -> bool:
        """
        Synchronous implementation of sheet initialization.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Check if the sheet exists
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = sheet_metadata.get('sheets', [])
            sheet_exists = False
            
            for sheet in sheets:
                if sheet.get('properties', {}).get('title') == self.sheet_name:
                    sheet_exists = True
                    break
            
            # Create the sheet if it doesn't exist
            if not sheet_exists:
                logger.info(f"Creating new sheet: {self.sheet_name}")
                
                # Add the sheet
                request = {
                    'addSheet': {
                        'properties': {
                            'title': self.sheet_name
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
                # Add headers
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1:G1",
                    valueInputOption="RAW",
                    body={
                        'values': [DEFAULT_SHEET_HEADERS]
                    }
                ).execute()
                
                # Format headers (make bold)
                format_request = {
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(),
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [format_request]}
                ).execute()
                
                logger.info(f"Sheet {self.sheet_name} created with headers")
            
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                raise StorageError(
                    f"Spreadsheet not found: {self.spreadsheet_id}",
                    code=ErrorCode.SHEET_NOT_FOUND,
                    original_exception=e
                )
            else:
                raise StorageError(
                    f"Google Sheets API error: {str(e)}",
                    code=ErrorCode.GOOGLE_SHEETS_ERROR,
                    original_exception=e
                )
        except Exception as e:
            raise StorageError(
                f"Error initializing sheet: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )
    
    def _get_sheet_id(self) -> int:
        """
        Get the sheet ID for the current sheet name.
        
        Returns:
            The sheet ID
            
        Raises:
            StorageError: If the sheet is not found
        """
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = sheet_metadata.get('sheets', [])
            
            for sheet in sheets:
                if sheet.get('properties', {}).get('title') == self.sheet_name:
                    return sheet.get('properties', {}).get('sheetId', 0)
            
            raise StorageError(
                f"Sheet not found: {self.sheet_name}",
                code=ErrorCode.SHEET_NOT_FOUND
            )
            
        except HttpError as e:
            raise StorageError(
                f"Google Sheets API error: {str(e)}",
                code=ErrorCode.GOOGLE_SHEETS_ERROR,
                original_exception=e
            )
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(
                f"Error getting sheet ID: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )
    
    async def store_meeting_data(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store meeting data in Google Sheets.
        
        Args:
            meeting_data: Meeting data to store
            
        Returns:
            Storage result with status
            
        Raises:
            StorageError: If storage fails
        """
        storage_id = f"storage_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "storage_id": storage_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "storage_status": StorageStatus.PENDING.value
        }
        
        logger.info(
            format_structured_log(
                f"Storing meeting data [{storage_id}]",
                {
                    "customer": meeting_data.get("customer_name"),
                    "meeting_date": meeting_data.get("meeting_date")
                }
            )
        )
        
        try:
            await self.initialize_sheet()
            
            # Prepare row data
            row_data = [""] * len(DEFAULT_SHEET_HEADERS)  # Initialize with empty strings
            
            if "timestamp" not in meeting_data or not meeting_data["timestamp"]:
                meeting_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Map meeting data to columns
            for field, column_index in MEETING_DATA_TO_SHEET_MAPPING.items():
                if field in meeting_data and meeting_data[field] is not None:
                    row_data[column_index] = meeting_data[field]
            
            # Store data in sheet
            result["storage_status"] = StorageStatus.PENDING.value
            
            # asyncio to run blocking IO in a thread
            await asyncio.to_thread(
                self._append_row,
                row_data
            )
            
            result["storage_status"] = StorageStatus.STORED.value
            result["row_data"] = row_data
            
            logger.info(
                format_structured_log(
                    f"Meeting data stored successfully [{storage_id}]",
                    {"status": result["storage_status"]}
                )
            )
            
            return result
            
        except Exception as e:
            result["storage_status"] = StorageStatus.FAILED.value
            
            error_msg = f"Failed to store meeting data: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{storage_id}]",
                    {"status": result["storage_status"]}
                ),
                exc_info=True
            )
            
            result["error"] = str(e)
            
            if not isinstance(e, StorageError):
                e = StorageError(
                    error_msg,
                    code=ErrorCode.STORAGE_ERROR,
                    original_exception=e
                )
            
            raise e
    
    def _append_row(self, row_data: List[Any]) -> Dict[str, Any]:
        """
        Append a row to the sheet.
        
        Args:
            row_data: List of values to append
            
        Returns:
            API response
            
        Raises:
            StorageError: If append fails
        """
        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:G",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={
                    'values': [row_data]
                }
            ).execute()
            
            return result
            
        except HttpError as e:
            raise StorageError(
                f"Google Sheets API error: {str(e)}",
                code=ErrorCode.GOOGLE_SHEETS_ERROR,
                original_exception=e
            )
        except Exception as e:
            raise StorageError(
                f"Error appending row: {str(e)}",
                code=ErrorCode.STORAGE_ERROR,
                original_exception=e
            )