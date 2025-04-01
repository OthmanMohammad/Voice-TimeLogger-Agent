# Voice-TimeLogger-Agent

An AI-powered system that automates consultant work hours tracking using voice messages. The consultant can record a voice message after each meeting, and the system extracts key details (customer name, start/end time, total hours, and notes) and stores them in Google Sheets.

## Features

- **Voice Processing**: Convert voice recordings to text using OpenAI Whisper or Google Speech-to-Text
- **AI Data Extraction**: Extract structured meeting data from transcribed text
- **Google Sheets Integration**: Automatically store meeting details in Google Sheets
- **Notifications**: Optional Slack or email notifications when new meetings are recorded
- **API Endpoint**: Simple API for uploading voice recordings
- **Dockerized Deployment**: Easy deployment using Docker
