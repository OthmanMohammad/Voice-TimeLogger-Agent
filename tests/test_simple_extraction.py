import asyncio
import os
import sys
import pytest

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.extraction_service import DataExtractionService

@pytest.mark.asyncio
async def test_regex_extraction():
    """Test extraction using RegexExtractionStrategy (doesn't require API keys)."""
    # Create service with regex strategy (no LLM, no API key needed)
    service = DataExtractionService(use_llm=False)
    
    # Sample text
    text = "I had a meeting with Acme Corp on January 15, 2025 from 10:00 am to 11:30 am. We discussed the new project requirements."
    
    # Extract data
    result = await service.extract_meeting_data(text)
    
    # Print results for manual verification
    print("\nExtraction Results:")
    print(f"Customer: {result.get('customer_name')}")
    print(f"Date: {result.get('meeting_date')}")
    print(f"Start Time: {result.get('start_time')}")
    print(f"End Time: {result.get('end_time')}")
    print(f"Total Hours: {result.get('total_hours')}")
    print(f"Notes: {result.get('notes')}")
    
    # Assertions
    assert "Acme Corp" in result.get("customer_name", "")
    assert result.get("meeting_date") == "2025-01-15"
    assert result.get("start_time") == "10:00 am"
    assert result.get("end_time") == "11:30 am"
    assert result.get("total_hours") == 1.5  # Calculated from start and end times
    assert "new project requirements" in result.get("notes", "")
    
    return result


@pytest.mark.asyncio
async def test_extraction_with_minimal_data():
    """Test extraction with minimal information."""
    # Create service with regex strategy (no LLM, no API key needed)
    service = DataExtractionService(use_llm=False)
    
    # Sample text with minimal information
    text = "Meeting with Global Technologies today. Discussed roadmap."
    
    # Extract data
    result = await service.extract_meeting_data(text)
    
    # Print results for manual verification
    print("\nMinimal Data Extraction Results:")
    print(f"Customer: {result.get('customer_name')}")
    print(f"Date: {result.get('meeting_date')}")
    print(f"Notes: {result.get('notes')}")
    
    # Assertions
    assert "Global Technologies" in result.get("customer_name", "")
    assert "Discussed roadmap" in result.get("notes", "")
    
    return result


if __name__ == "__main__":
    # Execute using asyncio.run for simple command line testing
    print("Running tests...")
    asyncio.run(test_regex_extraction())
    asyncio.run(test_extraction_with_minimal_data())
    print("\n✅ All tests passed!")