import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.notification import NotificationManager
from src.utils import configure_logging, get_logger

load_dotenv()
configure_logging(level="INFO")
logger = get_logger(__name__)

async def test_email():
    """Test sending an email notification"""
    manager = NotificationManager()
    
    # Sample meeting data for testing
    meeting_data = {
        "customer_name": "Test Client",
        "meeting_date": "2025-04-05",
        "start_time": "10:00 AM",
        "end_time": "11:30 AM",
        "total_hours": 1.5,
        "notes": "This is a test notification from Voice-TimeLogger-Agent.",
        "timestamp": "2025-04-05 12:00:00"
    }
    
    result = await manager.send_notification(meeting_data)
    print(f"Notification result: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_email())