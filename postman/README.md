# Postman Collection for Voice-TimeLogger-Agent API

This directory contains Postman collections and environments for testing the Voice-TimeLogger-Agent API.

## Files

- `voice-timelogger-agent-api.postman_collection.json`: The main Postman collection with all API endpoints
- `local-environment.postman_environment.json`: Environment variables for local development

## Importing the Collection

1. Open Postman
2. Click "Import" in the top left
3. Drag and drop the collection file or browse to select it
4. Also import the environment file for your desired environment
5. Select the imported environment from the dropdown in the top right

## Available Endpoints

The collection includes the following endpoints:

### Status Endpoints
- `GET /` - Root endpoint that returns API status
- `GET /health` - Health check endpoint

### Speech Endpoints
- `POST /api/v1/speech/transcribe` - Transcribe an audio file
- `POST /api/v1/speech/upload` - Upload and process an audio file, store in Google Sheets
- `POST /api/v1/speech/process` - Process an audio file (without storage)

### Meetings Endpoints
- `POST /api/v1/meetings/extract` - Extract meeting data from text

## Environment Variables

The collection uses the following environment variables:

- `base_url`: Base URL of the API (e.g., `http://localhost:8000`)
