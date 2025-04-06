# Voice-TimeLogger-Agent

<p align="center">
  <img src="docs\assets\logo.png" alt="Voice-TimeLogger-Agent Logo" width="200"/>
</p>

<h3 align="center">AI-powered automation system for consultant time tracking</h3>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

---

**Voice-TimeLogger-Agent** is an AI-powered system that automates consultant work hours tracking using voice messages. Consultants can record a quick voice message after each meeting, and the system automatically extracts key details (customer name, start/end times, total hours, and notes) and stores them in Google Sheets.

## Key Features

- **Voice Processing** - Convert voice recordings to text using OpenAI Whisper API
- **AI Data Extraction** - Extract structured meeting data from transcribed text using LLM
- **Google Sheets Integration** - Automatically store meeting details in Google Sheets
- **API Endpoint** - Simple REST API for uploading voice recordings
- **Notifications** - Optional email or Slack notifications for new meeting entries
- **n8n Workflow** - Visual automation workflow for processing audio files
- **Dockerized Deployment** - Easy deployment using Docker and Docker Compose

## Architecture

<p align="center">
  <img src="docs\assets\architecture_diagram.png" alt="Architecture Diagram" width="800"/>
</p>

### Technology Stack

- **FastAPI** - Modern, fast API framework for Python
- **OpenAI Whisper** - State-of-the-art speech recognition model
- **GPT Models** - Advanced language model for data extraction
- **Google Sheets API** - For structured data storage
- **n8n** - Workflow automation platform
- **Docker** - Container platform for deployment

<p align="center">
  <img src="https://n8n.io/favicon.ico" alt="n8n Icon" width="40" style="margin: 10px;"/>
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg" alt="OpenAI Icon" width="40" style="margin: 10px;"/>
  <img src="https://www.gstatic.com/images/branding/product/2x/sheets_2020q4_48dp.png" alt="Google Sheets Icon" width="40" style="margin: 10px;"/>
  <img src="https://fastapi.tiangolo.com/img/favicon.png" alt="FastAPI Icon" width="40" style="margin: 10px;"/>
</p>

### Component Overview

1. **API Service** - Handles audio file uploads and processing
2. **Speech Service** - Transcribes audio using OpenAI Whisper API
3. **Extraction Service** - Extracts structured data using GPT models
4. **Storage Service** - Stores meeting data in Google Sheets
5. **Notification Service** - Sends notifications via email or Slack
6. **n8n Workflow** - Provides visual workflow management and automation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Google Cloud Platform account with Google Sheets API enabled
- Google service account JSON key file with Google Sheets access

### Installation

1. Clone the repository:

```bash
git clone https://github.com/username/voice-timelogger-agent.git
cd voice-timelogger-agent
```

2. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Add Google service account credentials:

```bash
mkdir -p credentials
# Copy your Google service account JSON file to credentials/google-service-account.json
```

4. Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

5. Start the services:

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000 and n8n at http://localhost:5678.

## Deployment

### Local Deployment

For local development and testing, follow the [Installation](#installation) steps above.

### EC2 Deployment

To deploy on AWS EC2:

1. Prepare your local environment (steps 1-3 from Installation)
2. Make the deployment script executable:

```bash
chmod +x deploy-to-ec2.sh
```

3. Run the deployment script:

```bash
./deploy-to-ec2.sh ./path/to/your-key.pem ec2-user@your-ec2-ip
```

For more detailed deployment instructions, see [Deployment Documentation](docs/deployment.md).

## Usage

### Direct API Usage

Upload an audio recording directly to the API:

```bash
curl -X POST "http://localhost:8000/api/v1/speech/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/recording.mp3" \
  -F "notify=true"
```

### n8n Workflow

1. Access n8n at http://localhost:5678
2. Import the workflow from `n8n_workflow/voice-timelogger-workflow.json`
3. Configure the webhook URL with credentials
4. Upload audio through the webhook URL:

```bash
curl -X POST "http://localhost:5678/webhook/YOUR_WEBHOOK_PATH" \
  -F "file=@/path/to/recording.mp3" \
  -F "notify=true"
```

### API Endpoints

The application provides the following REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/speech/upload` | POST | Upload and process an audio recording |
| `/api/v1/speech/transcribe` | POST | Transcribe an audio file without extraction |
| `/api/v1/speech/process` | POST | Process an audio file without storage |
| `/api/v1/meetings/extract` | POST | Extract meeting data from text |
| `/health` | GET | Health check endpoint |

For a complete API reference, see the [Postman Collection](postman/voice-timelogger-agent-api.postman_collection.json).

## How It Works

### Audio Processing Workflow

1. The consultant records a voice message after a meeting, saying something like:
   ```
   "I had a meeting with Acme Corporation today from 2:00 PM to 3:30 PM. We discussed their new product launch strategy."
   ```

2. The voice message is uploaded to the API or n8n webhook.

3. The system transcribes the audio using OpenAI Whisper API.

4. An AI model extracts structured data from the transcription:
   ```json
   {
     "customer_name": "Acme Corporation",
     "meeting_date": "2025-04-06",
     "start_time": "2:00 PM",
     "end_time": "3:30 PM",
     "total_hours": "1h 30m",
     "notes": "We discussed their new product launch strategy."
   }
   ```

5. The extracted data is stored in Google Sheets.

6. Optional notification is sent via email or Slack.

### Data Extraction Capabilities

The AI-powered extraction system can handle various formats and expressions:

- Different time formats: "2pm", "14:00", "2 o'clock"
- Relative dates: "yesterday", "today", "last Tuesday"
- Calculation of total hours when not explicitly stated
- Extracting client names from contextual mentions
- Separating meeting notes from factual information

## Configuration

The application is configured using environment variables. See [.env.example](.env.example) for a complete list of available options:

```properties
# API settings
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# OpenAI API settings
OPENAI_API_KEY=your-openai-api-key-here
DEFAULT_LLM_MODEL=gpt-4o-mini

# Google Sheets settings
GOOGLE_CREDENTIALS_FILE=./credentials/google-service-account.json
GOOGLE_SPREADSHEET_ID=your-google-spreadsheet-id-here

# Notification settings
ENABLE_EMAIL_NOTIFICATIONS=false
ENABLE_SLACK_NOTIFICATIONS=false
NOTIFICATIONS_DEFAULT=false

# Additional notification settings for email and Slack
...
```

## n8n Workflow

<p align="center">
  <img src="n8n_workflow\images\n8n-workflow-diagram.png" alt="n8n Workflow" width="800"/>
</p>

The n8n workflow provided in this repository automates the process of:

1. Receiving audio files through a webhook
2. Processing them through the API
3. Storing the extracted meeting data in Google Sheets
4. Sending email notifications for new meetings

See [n8n Workflow Documentation](docs/n8n-workflow.md) for detailed instructions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [OpenAI](https://openai.com/) for Whisper API and GPT models
- [n8n.io](https://n8n.io/) for the workflow automation platform
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Google Sheets API](https://developers.google.com/sheets/api) for data storage