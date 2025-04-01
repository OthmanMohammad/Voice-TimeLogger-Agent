import re
import logging
from typing import Dict, Any, Optional
import datetime
from dateutil import parser
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Template Method Pattern for extraction strategies
class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies."""
    
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Template method to extract meeting data from text.
        
        Args:
            text: The text to extract data from
            
        Returns:
            Dict containing extracted meeting data
        """
        # Initialize with default structure
        result = {
            "customer_name": None,
            "start_time": None,
            "end_time": None,
            "meeting_date": None,
            "total_hours": None,
            "notes": None
        }
        
        # Call specific extraction methods
        result = await self._extract_implementation(text, result)
        
        # Post-processing
        if not result.get("total_hours") and result.get("start_time") and result.get("end_time"):
            result["total_hours"] = self._calculate_total_hours(
                result["start_time"], result["end_time"]
            )
        
        return result
    
    @abstractmethod
    async def _extract_implementation(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of the extraction strategy."""
        pass
    
    def _calculate_total_hours(self, start_time: str, end_time: str) -> float:
        """
        Calculate total hours from start and end times.
        
        Args:
            start_time: Start time string (e.g. "9:00 AM")
            end_time: End time string (e.g. "11:30 AM")
            
        Returns:
            Total hours as float
        """
        try:
            # Parse the time strings
            start = parser.parse(start_time)
            end = parser.parse(end_time)
            
            # If end time is earlier than start time, assume it's the next day
            if end < start:
                end = end + datetime.timedelta(days=1)
            
            # Calculate the difference in hours
            diff = end - start
            hours = diff.total_seconds() / 3600.0
            
            # Round to 2 decimal places
            return round(hours, 2)
        except Exception as e:
            logger.error(f"Error calculating hours: {str(e)}")
            return None


class LLMExtractionStrategy(ExtractionStrategy):
    """Strategy to extract data using LLM (GPT)."""
    
    def __init__(self, api_key: str):
        """
        Initialize the LLM extraction strategy.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        import openai
        openai.api_key = api_key
        self.openai = openai
    
    async def _extract_implementation(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to extract structured data."""
        try:
            prompt = f"""
            Extract the following information from this meeting note. If any information is missing, leave the field empty:
            
            1. Customer Name
            2. Start Time
            3. End Time
            4. Meeting Date
            5. Total Hours (calculate from start and end time if not explicitly mentioned)
            6. Notes (any other relevant information)
            
            Format the response as a JSON object with these keys: 
            customer_name, start_time, end_time, meeting_date, total_hours, notes
            
            Meeting note:
            {text}
            """
            
            response = await self.openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # Parse the JSON response
            import json
            try:
                extracted_data = json.loads(result_text)
                # Update the result with extracted data
                for key, value in extracted_data.items():
                    if key in result and value:
                        result[key] = value
                
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {result_text}")
                # Fall back to regex extraction if JSON parsing fails
                regex_strategy = RegexExtractionStrategy()
                return await regex_strategy._extract_implementation(text, result)
                
        except Exception as e:
            logger.error(f"LLM extraction error: {str(e)}")
            # Fall back to regex extraction on error
            regex_strategy = RegexExtractionStrategy()
            return await regex_strategy._extract_implementation(text, result)


class RegexExtractionStrategy(ExtractionStrategy):
    """Strategy to extract data using regex patterns."""
    
    async def _extract_implementation(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Use regex patterns to extract structured data."""
        # Extract customer name
        customer_patterns = [
            r"customer(?:\s+name)?(?:\s*:|\s+is|\s+was)?\s+([A-Za-z0-9\s]+)(?:\.|\,|\n|$)",
            r"client(?:\s+name)?(?:\s*:|\s+is|\s+was)?\s+([A-Za-z0-9\s]+)(?:\.|\,|\n|$)",
            r"meeting with\s+([A-Za-z0-9\s]+)(?:\.|\,|\n|$)",
        ]
        
        for pattern in customer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["customer_name"] = match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r"(?:on|date)(?:\s*:|\s+is|\s+was)?\s+([A-Za-z0-9\s,]+\d{4})",
            r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s*,?\s*\d{4})?)",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                try:
                    parsed_date = parser.parse(date_str)
                    result["meeting_date"] = parsed_date.strftime("%Y-%m-%d")
                except:
                    pass
                break
        
        # If no date found, try to infer current date
        if not result["meeting_date"]:
            today_patterns = [
                r"today",
                r"this morning",
                r"this afternoon",
                r"this evening"
            ]
            
            for pattern in today_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result["meeting_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                    break
        
        # Extract times
        time_pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))"
        times = re.findall(time_pattern, text, re.IGNORECASE)
        
        if len(times) >= 2:
            result["start_time"] = times[0].strip()
            result["end_time"] = times[1].strip()
        elif len(times) == 1:
            # If only one time is mentioned, assume it's the start time
            result["start_time"] = times[0].strip()
        
        # Extract total hours directly if mentioned
        hours_patterns = [
            r"(?:total|spent|duration|for)(?:\s+time|\s+hours)?(?:\s*:|\s+of|\s+is|\s+was)?\s+(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr)",
            r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr)(?:\s+total|\s+spent|\s+duration)?",
        ]
        
        for pattern in hours_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    result["total_hours"] = float(match.group(1))
                except:
                    pass
                break
        
        # Extract notes - everything else becomes notes
        # Remove identified elements from text to get notes
        notes_text = text
        if result["customer_name"]:
            notes_text = re.sub(r"customer(?:\s+name)?(?:\s*:|\s+is|\s+was)?\s+" + re.escape(result["customer_name"]), "", notes_text, flags=re.IGNORECASE)
        
        # Clean up notes
        notes_text = notes_text.strip()
        if notes_text:
            result["notes"] = notes_text
        
        return result


# Main Service Class that uses the strategies
class DataExtractionService:
    """Service to extract structured data from meeting transcriptions."""
    
    def __init__(self, use_llm: bool = True, openai_api_key: Optional[str] = None):
        """
        Initialize the data extraction service.
        
        Args:
            use_llm: Whether to use GPT for extraction (more accurate but slower)
            openai_api_key: API key for OpenAI
        """
        self.use_llm = use_llm
        
        if use_llm:
            openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenAI API key is required when use_llm is True")
            self.strategy = LLMExtractionStrategy(openai_api_key)
        else:
            self.strategy = RegexExtractionStrategy()
    
    async def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured meeting data from transcribed text.
        
        Args:
            text: The transcribed meeting notes
            
        Returns:
            Dict containing extracted meeting data
        """
        return await self.strategy.extract(text)