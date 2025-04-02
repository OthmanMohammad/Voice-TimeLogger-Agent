"""
Test script for the ExtractionManager class.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv, find_dotenv

# Import the ExtractionManager
from src.services.extraction.extraction_manager import ExtractionManager

# Load environment variables
load_dotenv(find_dotenv(), override=True)

async def test_extraction_manager():
    """Test the ExtractionManager class."""
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment.")
        return
    
    try:
        # Create extraction manager with the API key
        manager = ExtractionManager(openai_api_key=api_key)
        
        print(f"Testing extraction with ExtractionManager")
        
        # Sample text
        text = "I had a meeting with Acme Corp yesterday from 2 PM to 3:30 PM. We discussed project requirements."
        
        # Extract data
        result = await manager.extract(text)
        
        # Print results
        print("\nExtraction Results:")
        print(f"Customer: {result.get('customer_name')}")
        print(f"Date: {result.get('meeting_date')}")
        print(f"Start Time: {result.get('start_time')}")
        print(f"End Time: {result.get('end_time')}")
        print(f"Total Hours: {result.get('total_hours')}")
        print(f"Notes: {result.get('notes')}")
        
        # Check if extraction was complete
        if manager._is_complete_extraction(result):
            print("\nExtraction was complete!")
        else:
            print("\nExtraction was incomplete.")
        
        print("\nTest completed successfully!")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_extraction_manager())