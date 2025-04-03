"""
Generate test audio files for testing the speech-to-text functionality.
Uses OpenAI's text-to-speech API to create sample audio files.
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging


# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import configure_logging, get_logger
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

configure_logging(level="INFO")
logger = get_logger(__name__)

# Sample meeting descriptions for testing
SAMPLE_MEETING_TEXTS = [
    "I had a meeting with Acme Corporation on March 15th from 10:00 AM to 11:30 AM. We discussed their new product line and marketing strategy for Q2.",
    
    "Meeting with TechStart Inc today from 2 PM to 3:30 PM. We reviewed the project timeline and addressed some concerns about the delivery date.",
    
    "I just finished a call with Global Industries. Started at 9 AM and ended at 10:15 AM. They want to schedule a follow-up next week to discuss the contract details.",
    
    "Had a client meeting with Johnson & Johnson yesterday from 1:00 PM until 2:30 PM. We went over the regulatory requirements for their new healthcare product.",
    
    "Just completed a session with Microsoft about their cloud migration project. The meeting ran from 11 AM until 12:30 PM today. They needed help planning the infrastructure requirements.",
]

def create_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    logger.info(f"Ensured directory exists: {path}")

def generate_audio_with_openai(
    text: str, 
    output_file: str,
    voice: str = "alloy",
    model: str = "tts-1",
    api_key: Optional[str] = None
) -> str:
    """
    Generate audio file using OpenAI's text-to-speech API.
    
    Args:
        text: Text to convert to speech
        output_file: Path to save the audio file
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        model: TTS model to use
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        Path to the generated audio file
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OpenAI API key not provided or found in environment")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    logger.info(f"Generating audio with OpenAI TTS API: model={model}, voice={voice}")
    
    try:
        # Create the audio file
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Save the audio file
        response.stream_to_file(output_file)
        
        logger.info(f"Audio file generated successfully: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}", exc_info=True)
        raise

def generate_test_files(
    output_dir: str, 
    num_samples: int = 5,
    api_key: Optional[str] = None,
    voice: str = "alloy"
) -> List[str]:
    """
    Generate test audio files with meeting descriptions.
    
    Args:
        output_dir: Directory to save the audio files
        num_samples: Number of samples to generate
        api_key: OpenAI API key
        voice: Voice to use for TTS
        
    Returns:
        List of paths to the generated audio files
    """
    create_directory(output_dir)
    
    generated_files = []
    
    for i in range(min(num_samples, len(SAMPLE_MEETING_TEXTS))):
        text = SAMPLE_MEETING_TEXTS[i]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"test_meeting_{timestamp}_{i+1}.mp3"
        output_file = os.path.join(output_dir, filename)
        
        try:
            generate_audio_with_openai(
                text=text,
                output_file=output_file,
                voice=voice,
                api_key=api_key
            )
            generated_files.append(output_file)
            
            # Slight delay to avoid hitting rate limits
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to generate audio for sample {i+1}: {str(e)}")
    
    return generated_files

def main():
    """Main function to parse arguments and generate test audio files."""
    parser = argparse.ArgumentParser(description="Generate test audio files for speech-to-text testing")
    parser.add_argument("--output-dir", default="tests/audio", help="Directory to save the audio files")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to generate")
    parser.add_argument("--api-key", help="OpenAI API key (default: use environment variable)")
    parser.add_argument("--voice", default="alloy", help="Voice to use (alloy, echo, fable, onyx, nova, shimmer)")
    
    args = parser.parse_args()
    
    logger.info(f"Generating {args.num_samples} test audio files in {args.output_dir}")
    
    try:
        files = generate_test_files(
            output_dir=args.output_dir,
            num_samples=args.num_samples,
            api_key=args.api_key,
            voice=args.voice
        )
        
        logger.info(f"Successfully generated {len(files)} test audio files:")
        for file in files:
            logger.info(f"  - {file}")
            
    except Exception as e:
        logger.error(f"Error generating test audio files: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()