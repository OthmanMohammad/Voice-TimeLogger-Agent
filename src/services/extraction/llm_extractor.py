"""
Modern LLM-based extraction using the OpenAI API.
This implementation is compatible with OpenAI SDK 1.x.
"""

import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser

from openai import OpenAI

from src.services.extraction.config import (
    DEFAULT_LLM_MODEL, 
    EXTRACTION_PROMPTS,
    DEFAULT_MEETING_DATA
)

logger = logging.getLogger(__name__)

class LLMExtractor:
    """Extracts meeting data from text using LLM models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM extractor.
        
        Args:
            api_key: OpenAI API key (falls back to environment variable if not provided)
            model: Which model to use for extraction (defaults to config.DEFAULT_LLM_MODEL)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required - set in .env file or pass directly")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or DEFAULT_LLM_MODEL
        logger.info(f"LLM Extractor initialized with model: {self.model}")
    
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract structured meeting data from text using OpenAI's API.
        
        Args:
            text: The transcribed meeting text
            
        Returns:
            Dictionary containing extracted meeting data
        """
        # Get a copy of the default result structure
        result = DEFAULT_MEETING_DATA.copy()
        result["notes"] = text  # Always include the original text as notes
        
        try:
            # Get the system prompt for meeting data extraction
            system_prompt = EXTRACTION_PROMPTS["meeting_data"]
            
            # Make the API call
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,  # Low temperature for more consistent extraction
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Extract the result
            result_text = response.choices[0].message.content
            logger.debug(f"LLM response: {result_text}")
            
            # Parse the JSON response
            try:
                extracted_data = json.loads(result_text)
                
                # Update our result with the extracted data
                for key in DEFAULT_MEETING_DATA.keys():
                    if key in extracted_data and extracted_data[key] is not None:
                        result[key] = extracted_data[key]
                
                # Process dates - convert to YYYY-MM-DD format
                if result.get("meeting_date"):
                    try:
                        date_str = result["meeting_date"]
                        parsed_date = parser.parse(date_str)
                        result["meeting_date"] = parsed_date.strftime("%Y-%m-%d")
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {e}")
                
                # Convert total_hours to float
                if result.get("total_hours"):
                    try:
                        result["total_hours"] = float(result["total_hours"])
                    except:
                        result["total_hours"] = None
                
                # Add timestamp
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                return result
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {result_text}")
                # Add error info to result
                result["extraction_error"] = "Failed to parse LLM response as JSON"
                return result
                
        except Exception as e:
            logger.error(f"Error in LLM extraction: {str(e)}")
            # Add error info to result
            result["extraction_error"] = str(e)
            return result


async def test_llm_extraction(text, model=None):
    """Test function for LLM extraction."""
    try:
        # Try to get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OpenAI API key not found in environment.")
            print("Make sure you set OPENAI_API_KEY in your .env file.")
            return None
        
        print(f"Testing LLM extraction with model: {model or DEFAULT_LLM_MODEL}")
        
        # Create extractor and test
        extractor = LLMExtractor(api_key=api_key, model=model)
        result = await extractor.extract(text)
        return result
        
    except Exception as e:
        print(f"Error during LLM extraction test: {e}")
        return None


if __name__ == "__main__":
    # Sample text
    sample = "I had a meeting with Acme Corp yesterday from 2 PM to 3:30 PM. We discussed project requirements."
    
    # Run extraction
    asyncio.run(test_llm_extraction(sample))