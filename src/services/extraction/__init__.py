"""
Extraction module for Voice-TimeLogger-Agent.
Provides strategies for extracting structured meeting data from text.
"""

from src.services.extraction.extraction_manager import ExtractionManager
from src.services.extraction.config import DEFAULT_MEETING_DATA

# Export the main classes
__all__ = ["ExtractionManager", "DEFAULT_MEETING_DATA"]