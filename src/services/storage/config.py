"""
Configuration for storage services.
"""

# Google Sheets configuration
DEFAULT_SHEET_NAME = "Meeting Logs"
DEFAULT_SHEET_HEADERS = [
    "Timestamp", 
    "Customer Name", 
    "Meeting Date", 
    "Start Time", 
    "End Time", 
    "Total Hours", 
    "Notes"
]

# Mapping from meeting data fields to sheet columns
MEETING_DATA_TO_SHEET_MAPPING = {
    "timestamp": 0,
    "customer_name": 1,
    "meeting_date": 2,
    "start_time": 3,
    "end_time": 4,
    "total_hours": 5,
    "notes": 6
}