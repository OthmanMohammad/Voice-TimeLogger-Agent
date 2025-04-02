"""
Modern LLM-based extraction using the OpenAI API.
This implementation is compatible with OpenAI SDK 1.x.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser
from openai import OpenAI
from openai import OpenAIError

from config.config import get_settings
from src.services.extraction.config import (
    EXTRACTION_PROMPTS,
    DEFAULT_MEETING_DATA
)
from src.utils import (
    get_logger, 
    log_async_function_call,
    format_structured_log,
    LLMExtractionError,
    ValidationError
)

# Setup logger for this module
logger = get_logger(__name__)

# Define the default model
DEFAULT_LLM_MODEL = "gpt-4o-mini"


class LLMExtractor:
    """Extracts meeting data from text using LLM models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM extractor.
        
        Args:
            api_key: OpenAI API key (falls back to settings if not provided)
            model: Which model to use for extraction (defaults to DEFAULT_LLM_MODEL)
            
        Raises:
            ValidationError: If API key is missing or invalid
        """
        try:
            # If api_key is provided directly, use it
            if api_key:
                self.api_key = api_key
            else:
                # Otherwise get from settings
                settings = get_settings()
                self.api_key = settings.OPENAI_API_KEY
            
            if not self.api_key:
                raise ValidationError("Valid OpenAI API key is required")
            
            self.client = OpenAI(api_key=self.api_key)
            self.model = model or DEFAULT_LLM_MODEL
            logger.info(f"LLM Extractor initialized with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM extractor: {str(e)}", exc_info=True)
            raise ValidationError(
                f"Failed to initialize LLM extractor: {str(e)}",
                original_exception=e
            )
    
    @log_async_function_call(logger)
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract structured meeting data from text using OpenAI's API.
        
        Args:
            text: The transcribed meeting text
            
        Returns:
            Dictionary containing extracted meeting data
            
        Raises:
            LLMExtractionError: If extraction fails
        """
        # Get a copy of the default result structure
        result = DEFAULT_MEETING_DATA.copy()
        result["notes"] = text  # Always include the original text as notes
        
        extraction_id = f"extract_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(
            format_structured_log(
                f"Starting LLM extraction [{extraction_id}]",
                {"text_length": len(text), "model": self.model}
            )
        )
        
        try:
            # Get the system prompt for meeting data extraction
            system_prompt = EXTRACTION_PROMPTS["meeting_data"]
            
            # Make the API call
            logger.debug(f"Sending request to OpenAI API with model {self.model}")
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
            logger.debug(f"Received LLM response: {result_text[:200]}...")
            
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
                        logger.warning(
                            f"Failed to parse date '{result['meeting_date']}': {str(e)}"
                        )
                
                # Convert total_hours to float
                if result.get("total_hours"):
                    try:
                        result["total_hours"] = float(result["total_hours"])
                    except Exception as e:
                        logger.warning(
                            f"Failed to convert total_hours '{result['total_hours']}' to float: {str(e)}"
                        )
                        result["total_hours"] = None
                
                # Add timestamp
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Log success
                logger.info(
                    format_structured_log(
                        f"LLM extraction successful [{extraction_id}]",
                        {
                            "customer": result.get("customer_name"),
                            "date": result.get("meeting_date"),
                            "total_hours": result.get("total_hours")
                        }
                    )
                )
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse LLM response as JSON [{extraction_id}]: {result_text[:200]}...",
                    exc_info=True
                )
                raise LLMExtractionError(
                    "Failed to parse LLM response as JSON",
                    details={"response_text": result_text[:500], "extraction_id": extraction_id},
                    original_exception=e
                )
                
        except OpenAIError as e:
            logger.error(
                f"OpenAI API error during extraction [{extraction_id}]: {str(e)}",
                exc_info=True
            )
            raise LLMExtractionError(
                f"OpenAI API error: {str(e)}",
                details={"extraction_id": extraction_id},
                original_exception=e
            )
                
        except Exception as e:
            logger.error(
                f"Unexpected error in LLM extraction [{extraction_id}]: {str(e)}",
                exc_info=True
            )
            raise LLMExtractionError(
                f"Unexpected error in LLM extraction: {str(e)}",
                details={"extraction_id": extraction_id},
                original_exception=e
            )