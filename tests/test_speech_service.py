"""
Test script for the speech-to-text service.
Demonstrates how to use the SpeechManager to transcribe audio files.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from pathlib import Path


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import configure_logging, get_logger
from src.services.speech import SpeechManager


load_dotenv()

configure_logging(level="INFO")
logger = get_logger(__name__)

async def test_transcription(file_path: str):
    """
    Test transcribing an audio file using the SpeechManager.
    
    Args:
        file_path: Path to the audio file to transcribe
    """
    logger.info(f"Testing transcription of file: {file_path}")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("ERROR: OpenAI API key not found. Set OPENAI_API_KEY in your .env file.")
        return None
    
    try:
        speech_manager = SpeechManager(openai_api_key=api_key)
        
        logger.info("SpeechManager initialized. Starting transcription...")
        
        # Transcribe the audio file
        result = await speech_manager.transcribe_audio_file(file_path, copy_to_storage=True)
        
        logger.info("Transcription completed!")
        print("\nTranscription Results:")
        print(f"Processing ID: {result.get('processing_id')}")
        print(f"Status: {result.get('processing_status')}")
        print(f"File: {result.get('file_path')}")
        print(f"Model: {result.get('model')}")
        print("\nTranscribed Text:")
        print(f"\"{result.get('text')}\"")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        print(f"\nError: {e}")
        return None

async def test_transcribe_with_extraction(file_path: str):
    """
    Test end-to-end workflow: transcribe an audio file and extract meeting data.
    
    Args:
        file_path: Path to the audio file to transcribe
    """
    # First transcribe the audio
    transcription_result = await test_transcription(file_path)
    
    if not transcription_result:
        return
    
    # Only import ExtractionManager here to avoid circular imports
    from src.services.extraction import ExtractionManager
    
    try:
        logger.info("Initializing ExtractionManager for data extraction...")
        
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("ERROR: OpenAI API key not found for extraction.")
            return
        
        # Initialize the ExtractionManager
        extraction_manager = ExtractionManager(openai_api_key=api_key)
        
        # Extract meeting data from the transcription
        transcribed_text = transcription_result.get("text", "")
        logger.info(f"Extracting meeting data from transcribed text ({len(transcribed_text)} chars)...")
        
        extraction_result = await extraction_manager.extract(transcribed_text)
        
        # Print extraction results
        print("\nExtracted Meeting Data:")
        print(f"Customer: {extraction_result.get('customer_name')}")
        print(f"Date: {extraction_result.get('meeting_date')}")
        print(f"Start Time: {extraction_result.get('start_time')}")
        print(f"End Time: {extraction_result.get('end_time')}")
        print(f"Total Hours: {extraction_result.get('total_hours')}")
        
        # Print extraction status
        print(f"\nExtraction Status: {extraction_result.get('extraction_status')}")
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}", exc_info=True)
        print(f"\nError: {e}")
        return None

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Test the speech-to-text service")
    parser.add_argument("--file", "-f", help="Path to the audio file to transcribe")
    parser.add_argument("--directory", "-d", help="Directory with audio files to test")
    parser.add_argument("--extract", "-e", action="store_true", help="Also extract meeting data from transcription")
    
    args = parser.parse_args()
    
    if not args.file and not args.directory:
        print("Error: You must specify either --file or --directory")
        parser.print_help()
        sys.exit(1)
    
    if args.file:
        # Test a single file
        asyncio.run(
            test_transcribe_with_extraction(args.file) if args.extract 
            else test_transcription(args.file)
        )
    
    elif args.directory:
        # Test all audio files in the directory
        dir_path = Path(args.directory)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Error: Directory not found: {args.directory}")
            sys.exit(1)
        
        audio_files = [
            str(f) for f in dir_path.glob("*.mp3")
        ]
        
        if not audio_files:
            print(f"No audio files found in {args.directory}")
            sys.exit(1)
        
        print(f"Found {len(audio_files)} audio files to test")
        
        # Process each file
        for file_path in audio_files:
            print(f"\n--- Testing file: {file_path} ---")
            asyncio.run(
                test_transcribe_with_extraction(file_path) if args.extract 
                else test_transcription(file_path)
            )

if __name__ == "__main__":
    main()