"""
Storage module for the Voice-TimeLogger-Agent.
Handles storing meeting data in various backends.
"""

from src.services.storage.storage_manager import StorageManager
from src.services.storage.config import DEFAULT_SHEET_NAME, DEFAULT_SHEET_HEADERS

__all__ = [
    "StorageManager",
    "DEFAULT_SHEET_NAME",
    "DEFAULT_SHEET_HEADERS"
]