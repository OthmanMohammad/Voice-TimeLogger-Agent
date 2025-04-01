import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.extraction_service import DataExtractionService

# Load environment variables
load_dotenv()

async def test_llm_extraction(text):
    """
    Test the LLM extraction strategy with the provided text.
    
    Args:
        text: The text to extract meeting data from
    """
    # Get OpenAI API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OpenAI API key not found. Set OPENAI_API_KEY in your .env file.")
        return None
        
    print(f"Testing LLM extraction with text: {text}")
    
    # Create extraction service with LLM strategy (requires API key)
    service = DataExtractionService(use_llm=True, openai_api_key=api_key)
    
    # Extract data
    result = await service.extract_meeting_data(text)
    
    # Print results
    print("\nLLM Extraction Results:")
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
        "Meeting with Global Technologies today. Discussed roadmap.",
        "Client name: Johnson & Johnson on March 10th from 9am to 10:30am to discuss the marketing campaign.",
        "I met with Microsoft yesterday at 2 PM until 3:30 PM to review the integration plan."
    ]
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Run LLM extraction for each example
    for i, example in enumerate(examples):
        print(f"\n--- Example {i+1} ---")
        try:
            asyncio.run(test_llm_extraction(example))
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nLLM extraction tests completed!")