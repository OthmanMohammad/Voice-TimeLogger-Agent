"""
Test script for the ExtractionManager class.
"""
import asyncio
from config.config import get_settings
from src.services.extraction.extraction_manager import ExtractionManager
from src.utils import configure_logging, get_logger


configure_logging(level="INFO")
logger = get_logger(__name__)

async def test_extraction_manager():
    """Test the ExtractionManager class."""
    try:
        settings = get_settings()
        api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment.")
            print("ERROR: OPENAI_API_KEY not found in environment.")
            return
        
        logger.info("Testing extraction with ExtractionManager")
        
        # Create extraction manager with the API key
        manager = ExtractionManager(openai_api_key=api_key)
        
        # Sample text
        text = "I had a meeting with Acme Corp a week ago from 2 PM to 3:30 PM. We discussed project requirements."
        logger.info(f"Sample text: {text}")
        
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
            logger.info("Extraction was complete")
            print("\nExtraction was complete!")
        else:
            logger.warning("Extraction was incomplete")
            print("\nExtraction was incomplete.")
        
        if "extraction_error" in result:
            logger.warning(f"Extraction error: {result['extraction_error']}")
            print(f"Warning - Extraction Error: {result['extraction_error']}")
        
        logger.info("Test completed successfully")
        print("\nTest completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_extraction_manager())