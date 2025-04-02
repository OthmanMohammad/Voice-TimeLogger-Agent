"""
Configuration for extraction services.
Separates configuration from implementation for better maintainability.
"""

from datetime import datetime

# Get current date for relative date calculations
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")

# System prompts for different extraction strategies
EXTRACTION_PROMPTS = {
    "meeting_data": f"""
    You are an AI assistant specialized in extracting structured meeting data from text.
    Today's date is {CURRENT_DATE}.
    
    Given a transcription of someone describing a meeting, extract the following information:
    
    1. Customer/Client Name: The company or organization name (avoid including dates or other info here)
    2. Meeting Date: In YYYY-MM-DD format. Handle relative dates like "today" or "yesterday" based on today's date of {CURRENT_DATE}.
    3. Start Time: The time the meeting started (in format like "10:00 AM" or "14:30")
    4. End Time: The time the meeting ended (in format like "11:00 AM" or "15:45")
    5. Total Hours: Numeric duration in hours, calculated from start and end time if not explicitly mentioned
    6. Notes: Any other relevant information about the meeting
    
    Format your response as a JSON object with these exact keys:
    {{"customer_name": string, "meeting_date": string, "start_time": string, "end_time": string, "total_hours": number, "notes": string}}
    
    If any field is missing in the text, use null for that field. For total_hours, calculate from start and end times if both are provided.
    For dates, when you see "yesterday", that means {(datetime.now().replace(day=datetime.now().day-1)).strftime("%Y-%m-%d")}.
    When you see "today", that means {CURRENT_DATE}.
    """
}

# Default result structure
DEFAULT_MEETING_DATA = {
    "customer_name": None,
    "meeting_date": None,
    "start_time": None,
    "end_time": None,
    "total_hours": None,
    "notes": None,
    "timestamp": None
}

# Required fields for a complete extraction
REQUIRED_MEETING_FIELDS = ["customer_name", "total_hours"]