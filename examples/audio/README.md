# Example Audio Files

This directory contains example audio files for testing the Voice-TimeLogger-Agent system.

## Files

- `example_meeting_1.mp3` - Meeting with Acme Corp
- `example_meeting_2.mp3` - Meeting with TechStart Inc
- `example_meeting_3.mp3` - Meeting with Global Industries
- `example_meeting_4.mp3` - Meeting with Johnson & Johnson
- `example_meeting_5.mp3` - Meeting with Microsoft

## Usage

You can use these files to test the system:

1. **API Testing:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/speech/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@examples/audio/example_meeting_1.mp3" \
     -F "notify=true"
   ```

2. **n8n Testing:**
   ```bash
   curl -X POST "http://localhost:5678/webhook/YOUR_WEBHOOK_PATH" \
     -F "file=@examples/audio/example_meeting_1.mp3" \
     -F "notify=true"
   ```

## Source

These example audio files were generated using the script at `scripts/generate_test_audio.py` using OpenAI's text-to-speech API.