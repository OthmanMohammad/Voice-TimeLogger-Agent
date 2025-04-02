"""
Logging level enums for the Voice-TimeLogger-Agent.
"""

import logging
from enum import Enum


class LogLevel(Enum):
    """Enum mapping log level names to their numeric values."""
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    @classmethod
    def from_string(cls, level_name: str) -> int:
        """
        Convert a string log level name to its numeric value.
        
        Args:
            level_name: String name of the log level (case-insensitive)
            
        Returns:
            Numeric log level
            
        Raises:
            ValueError: If the level name is not valid
        """
        try:
            return cls[level_name.upper()].value
        except KeyError:
            raise ValueError(f"Invalid log level: {level_name}")