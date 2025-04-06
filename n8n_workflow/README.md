# n8n Workflow for Voice-TimeLogger-Agent

This directory contains the n8n workflow configuration for the Voice-TimeLogger-Agent project.

## Contents

- `voice-timelogger-workflow.json` - The main workflow for processing audio and updating Google Sheets

## Setup

For detailed instructions on setting up and using the n8n workflow, please refer to:
- [n8n Workflow Documentation](../docs/n8n-workflow.md)

## How it Works

This n8n workflow:
1. Receives audio files via a webhook
2. Sends the audio to the Voice-TimeLogger API for processing
3. Stores the extracted meeting data in Google Sheets
4. Sends email notifications

## Quick Start

1. Start the Docker containers: `docker-compose up -d`
2. Access n8n at http://localhost:5678
3. Import the workflow from this directory
4. Configure credentials for Google Sheets and SMTP
5. Activate the workflow