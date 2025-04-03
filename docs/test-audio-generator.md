# Test Audio Generator Utility

## Overview

The `generate_test_audio.py` script is a utility for creating realistic test audio files for the Voice-TimeLogger-Agent application. It uses OpenAI's Text-to-Speech (TTS) API to generate spoken meeting summaries that can be used to test the speech-to-text and data extraction functionality.

## Location

This script should be stored in two locations:

1. `scripts/generate_test_audio.py` - For developer use during development
2. `tests/utils/generate_test_audio.py` - For automated testing in CI/CD pipelines

## Features

- Generates realistic meeting summary audio files
- Uses OpenAI's TTS API for high-quality voice synthesis
- Supports multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
- Creates files with a variety of client names, meeting durations, and contexts
- Automatically names files with timestamps for easy identification

## Usage

### Basic Usage

```bash
python -m scripts.generate_test_audio --output-dir tests/audio --num-samples 3
```

### Options

- `--output-dir`: Directory to save the audio files (default: tests/audio)
- `--num-samples`: Number of samples to generate (default: 5)
- `--api-key`: OpenAI API key (default: uses environment variable)
- `--voice`: Voice to use (default: alloy)

### Voices

OpenAI offers several voices with different characteristics:

- `alloy`: Neutral, versatile voice (default)
- `echo`: Deeper, mature voice
- `fable`: Soft, warm voice
- `onyx`: Authoritative voice
- `nova`: Professional, clear voice
- `shimmer`: Bright, energetic voice

## Requirements

- OpenAI API key with access to TTS functionality
- Python 3.7+
- `openai` Python package

## Integration with Testing

The generated audio files are used in:

1. Unit tests that verify the speech-to-text functionality
2. Integration tests that verify the end-to-end workflow
3. Manual testing of the API endpoints

## Maintenance

The test samples should be refreshed periodically to ensure they cover a wide range of scenarios. Consider updating the sample texts when:

- New features are added that require specific content in the meeting summaries
- There are changes to the extraction logic
- New edge cases are identified that should be tested

## Security Note

The generated audio files are stored in the repository for testing purposes but do not contain any sensitive information. All client names, meeting details, and other information are fictional.