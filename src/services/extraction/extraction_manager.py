"""
Extraction manager that handles meeting data extraction.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from src.services.extraction.config import DEFAULT_MEETING_DATA, REQUIRED_MEETING_FIELDS

logger = logging.getLogger(__name__)

class ExtractionManager:
    """
    Manager class for extracting structured meeting data from text.
    Primary implementation uses LLM-based extraction.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the extraction manager.
        
        Args:
            openai_api_key: API key for OpenAI (if None, read from environment)
            model: OpenAI model to use (defaults to configuration value)
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        
        # Lazy load the LLM extractor when needed
        self._llm_extractor = None
    
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract meeting data from text.
        
        Args:
            text: Transcribed meeting text
            
        Returns:
            Dictionary containing extracted meeting data
        """
        # Initialize with default values
        result = DEFAULT_MEETING_DATA.copy()
        result["notes"] = text
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Try LLM extraction
        try:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not provided and not found in environment")
            
            # Lazy initialize the LLM extractor
            if not self._llm_extractor:
                from src.services.extraction.llm_extractor import LLMExtractor
                self._llm_extractor = LLMExtractor(
                    api_key=self.openai_api_key, 
                    model=self.model
                )
            
            logger.info(f"Using LLM extraction with model: {self._llm_extractor.model}")
            llm_result = await self._llm_extractor.extract(text)
            
            # Update our result with the extracted data
            for key in DEFAULT_MEETING_DATA.keys():
                if key in llm_result and llm_result[key] is not None:
                    result[key] = llm_result[key]
            
            # Check if extraction was successful
            if self._is_complete_extraction(result):
                logger.info("LLM extraction successful")
            else:
                logger.warning("LLM extraction incomplete")
                
        except Exception as e:
            logger.error(f"LLM extraction error: {str(e)}")
            result["extraction_error"] = str(e)
        
        return result
    
    def _is_complete_extraction(self, result: Dict[str, Any]) -> bool:
        """
        Check if the extraction result has all required fields.
        
        Args:
            result: Extraction result to check
            
        Returns:
            True if all required fields are present, False otherwise
        """
        return all(result.get(field) is not None for field in REQUIRED_MEETING_FIELDS)