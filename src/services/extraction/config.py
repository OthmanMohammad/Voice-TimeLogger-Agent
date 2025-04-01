"""
Configuration for extraction services.
Separates configuration from implementation for better maintainability.
"""

# Default LLM model to use
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"

# System prompts for different extraction strategies
EXTRACTION_PROMPTS = {
    "meeting_data": """
    You are an AI assistant specialized in extracting structured meeting data from text.
    Given a transcription of someone describing a meeting, extract the following information:
    
    1. Customer/Client Name: The company or organization name (avoid including dates or other info here)
    2. Meeting Date: In YYYY-MM-DD format
    3. Start Time: The time the meeting started
    4. End Time: The time the meeting ended
    5. Total Hours: Numeric duration in hours, calculated from start and end time if not explicitly mentioned
    6. Notes: Any other relevant information about the meeting
    
    Format your response as a JSON object with these exact keys:
    {"customer_name": string, "meeting_date": string, "start_time": string, "end_time": string, "total_hours": number, "notes": string}
    
    If any field is missing in the text, use null for that field. For total_hours, calculate from start and end times if both are provided.
    For dates, convert relative dates like "today" or "yesterday" to actual dates.
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