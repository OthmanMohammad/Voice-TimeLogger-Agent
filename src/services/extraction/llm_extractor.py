"""
Modern LLM-based extraction using the OpenAI API.
This implementation is compatible with OpenAI SDK 1.x.
"""

import json
import asyncio
import re
from typing import Dict, Any, Optional, Union
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
    format_structured_log
)
from src.utils.exceptions import (
    LLMExtractionError,
    ValidationError
)
from src.enums import ExtractionStatus


logger = get_logger(__name__)

class LLMExtractor:
    """Extracts meeting data from text using LLM models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM extractor.
        
        Args:
            api_key: OpenAI API key (falls back to settings if not provided)
            model: Which model to use for extraction (defaults to settings.DEFAULT_LLM_MODEL)
            
        Raises:
            ValidationError: If API key is missing or invalid
        """
        try:
            # Get settings
            settings = get_settings()
            
            # If api_key is provided directly, use it
            if api_key:
                self.api_key = api_key
            else:
                # Otherwise get from settings
                self.api_key = settings.OPENAI_API_KEY
            
            if not self.api_key:
                raise ValidationError("Valid OpenAI API key is required")
            
            self.client = OpenAI(api_key=self.api_key)
            # Use model from parameters, or from settings, or fall back to gpt-4o-mini
            self.model = model or settings.DEFAULT_LLM_MODEL
            logger.info(f"LLM Extractor initialized with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM extractor: {str(e)}", exc_info=True)
            raise ValidationError(
                f"Failed to initialize LLM extractor: {str(e)}",
                original_exception=e
            )
    
    def _format_duration(self, hours_value: Union[float, str]) -> str:
        """
        Format a duration value to the standard "Xh Ym" format.
        
        Args:
            hours_value: Duration in hours (float or string)
            
        Returns:
            Formatted duration string like "1h 30m"
        """
        # If it's already in the correct format, return it
        if isinstance(hours_value, str) and re.match(r'^\d+h\s+\d+m$', hours_value.strip()):
            return hours_value
            
        try:
            # Convert to float if it's a string representing a number
            if isinstance(hours_value, str):
                # Try to extract numeric part if it has units
                match = re.match(r'(\d+\.?\d*)', hours_value)
                if match:
                    hours_value = float(match.group(1))
                else:
                    hours_value = float(hours_value)
            
            # Calculate hours and minutes
            hours = int(hours_value)
            minutes = int((hours_value - hours) * 60)
            
            # Format as "Xh Ym"
            return f"{hours}h {minutes}m"
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to format duration '{hours_value}': {str(e)}")
            # Return the original value if we can't format it
            return str(hours_value) if hours_value is not None else None

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
        result["extraction_status"] = ExtractionStatus.PENDING.value
        
        extraction_id = f"extract_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(
            format_structured_log(
                f"Starting LLM extraction [{extraction_id}]",
                {"text_length": len(text), "model": self.model}
            )
        )
        
        try:
            result["extraction_status"] = ExtractionStatus.PROCESSING.value
            
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
                
                # Format total_hours to ensure consistent "Xh Ym" format
                if result.get("total_hours") is not None:
                    result["total_hours"] = self._format_duration(result["total_hours"])
                
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                result["extraction_status"] = ExtractionStatus.COMPLETE.value
                
                # Log success
                logger.info(
                    format_structured_log(
                        f"LLM extraction successful [{extraction_id}]",
                        {
                            "customer": result.get("customer_name"),
                            "date": result.get("meeting_date"),
                            "total_hours": result.get("total_hours"),
                            "status": result["extraction_status"]
                        }
                    )
                )
                
                return result
                
            except json.JSONDecodeError as e:
                result["extraction_status"] = ExtractionStatus.FAILED.value
                
                logger.error(
                    f"Failed to parse LLM response as JSON [{extraction_id}]: {result_text[:200]}...",
                    exc_info=True
                )
                raise LLMExtractionError(
                    "Failed to parse LLM response as JSON",
                    details={
                        "response_text": result_text[:500], 
                        "extraction_id": extraction_id,
                        "status": result["extraction_status"]
                    },
                    original_exception=e
                )
                
        except OpenAIError as e:
            result["extraction_status"] = ExtractionStatus.FAILED.value
            
            logger.error(
                f"OpenAI API error during extraction [{extraction_id}]: {str(e)}",
                exc_info=True
            )
            raise LLMExtractionError(
                f"OpenAI API error: {str(e)}",
                details={
                    "extraction_id": extraction_id,
                    "status": result["extraction_status"]
                },
                original_exception=e
            )
                
        except Exception as e:
            result["extraction_status"] = ExtractionStatus.FAILED.value
            
            logger.error(
                f"Unexpected error in LLM extraction [{extraction_id}]: {str(e)}",
                exc_info=True
            )
            raise LLMExtractionError(
                f"Unexpected error in LLM extraction: {str(e)}",
                details={
                    "extraction_id": extraction_id,
                    "status": result["extraction_status"]
                },
                original_exception=e
            )