import os
import sys
import asyncio

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.extraction_service import DataExtractionService


async def test_extraction(text):
    """
    Test the extraction service with the provided text.
    
    Args:
        text: The text to extract meeting data from
    """
    # Create extraction service with regex strategy (no API key needed)
    service = DataExtractionService(use_llm=False)
    
    # Extract data
    result = await service.extract_meeting_data(text)
    
    # Print results
    print("\nExtraction Results:")
    print(f"Customer: {result.get('customer_name')}")
    print(f"Date: {result.get('meeting_date')}")
    print(f"Start Time: {result.get('start_time')}")
    print(f"End Time: {result.get('end_time')}")
    print(f"Total Hours: {result.get('total_hours')}")
    print(f"Notes: {result.get('notes')}")
    
    return result


if __name__ == "__main__":
    # Sample text examples
    examples = [
        "I had a meeting with Acme Corp on January 15, 2025 from 10:00 am to 11:30 am. We discussed the new project requirements.",
        "Meeting with Johnson & Johnson today from 2 PM to 3:30 PM to discuss the marketing campaign.",
        "Client name: Microsoft. We met on March 20th from 9am to 10:30am and discussed the software integration timeline."
    ]
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Run extraction for each example
    for i, example in enumerate(examples):
        print(f"\n--- Example {i+1} ---\n{example}")
        asyncio.run(test_extraction(example))
    
    print("\nExtraction tests completed!")