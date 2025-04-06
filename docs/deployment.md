# Docker Deployment Guide

This document explains how to deploy the Voice-TimeLogger-Agent application both locally and on an EC2 instance.

## Prerequisites

- Docker and Docker Compose installed
- An OpenAI API key
- A Google service account JSON key file with Google Sheets access
- For EC2 deployment: An EC2 instance with SSH access

## Local Deployment

There are two ways to deploy and test the Voice-TimeLogger-Agent:
1. **Direct API approach**: Deploy only the API service and interact with it directly
2. **n8n workflow approach**: Deploy both the API and n8n services, and use the n8n workflow as an intermediary

### 1. Configure Environment

- Copy `.env.example` to `.env` and edit with your actual API keys and settings
- Place your Google service account JSON file in the `credentials/` directory as `google-service-account.json`

### 2. Run the Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Start the Service

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000
The n8n workflow automation tool will be available at http://localhost:5678

#### Testing with Direct API Approach
```bash
# Test the API directly
curl -X POST "http://localhost:8000/api/v1/speech/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@examples/audio/example_meeting_1.mp3" \
  -F "notify=true"
```

#### Testing with n8n Workflow
```bash
# Test via the n8n webhook (after configuring the workflow)
curl -X POST "http://localhost:5678/webhook/YOUR_WEBHOOK_PATH" \
  -F "file=@examples/audio/example_meeting_1.mp3" \
  -F "notify=true"
```

Each approach has its advantages:
- The direct API approach is simpler for development and debugging
- The n8n workflow approach provides visual workflow management and additional automation options

> **Note:**  
> The setup script (`setup.sh`) only needs to be run **once** to create the necessary directories and check for required files. For subsequent deployments, you can run:  
> ```bash
> docker-compose up -d
> ```
> directly.

### 4. Check Logs

```bash
docker-compose logs -f
```

## n8n Configuration

After deploying the application, you'll need to configure n8n:

- Access n8n at http://localhost:5678
- Create an n8n account or log in
- Import the workflow from n8n_workflow/voice-timelogger-workflow.json
- Configure the required credentials:
  - Google Sheets (for storing meeting data)
  - SMTP (for email notifications)
- Activate the workflow

Refer to n8n Workflow Documentation for detailed setup instructions.

## EC2 Deployment

### 1. Prerequisites

- An EC2 instance running Amazon Linux 2 or Ubuntu
- Docker and Docker Compose installed on the instance
- An SSH key pair for connecting to the EC2 instance

### 2. Prepare Your Local Environment

- Copy `.env.example` to `.env` and edit with your actual API keys and settings
- Place your Google service account JSON file in the `credentials/` directory as `google-service-account.json`
- Place your EC2 SSH private key in the `credentials/` directory (e.g., `voice-timelogger-key.pem`)
- Make the deployment script executable:

```bash
chmod +x deploy-to-ec2.sh
```

### 3. Deploy to EC2

```bash
./deploy-to-ec2.sh ./credentials/your-key.pem ec2-user@your-ec2-ip
```

Replace:
- `your-key.pem` with your actual SSH key filename
- `your-ec2-ip` with your EC2 instance's public IP address
- If using a different user than `ec2-user` (e.g., for Ubuntu, use `ubuntu`), update accordingly

### 4. Verify Deployment

Once deployment completes, the API will be available at http://your-ec2-ip:8000
The n8n workflow automation tool will be available at http://your-ec2-ip:5678

You can SSH into your EC2 instance to check logs:

```bash
ssh -i ./credentials/your-key.pem ec2-user@your-ec2-ip
cd voice-timelogger
docker-compose logs -f
```

## How It Works

### Local Deployment

1. The setup script creates necessary directories and checks for required files
2. Docker Compose builds the application image using the multi-stage Dockerfile
3. The container runs with the local directories mounted as volumes
4. n8n provides a visual workflow editor and execution engine

### EC2 Deployment

1. The `deploy-to-ec2.sh` script:
   - Creates a deployment package excluding sensitive files
   - Transfers this package to the EC2 instance
   - Transfers sensitive files (.env and credentials) separately
   - Extracts the files and starts the application on EC2

2. Docker Compose on EC2:
   - Builds the application image
   - Starts the container with the correct configuration
   - Exposes the API on port 8000 and n8n on port 5678

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check logs: `docker-compose logs`
   - Verify API keys in `.env` file
   - Ensure Google service account JSON is correctly placed

2. **Permission issues**
   - Run `chmod -R 777 ./tmp` to ensure the tmp directory is writable

3. **Network issues**
   - If deploying to EC2, check security group settings to ensure ports 8000 and 5678 are open

4. **Deployment script fails**
   - Verify SSH key has the correct permissions: `chmod 400 ./credentials/your-key.pem`
   - Check EC2 instance status and connectivity

5. **n8n workflow issues**
   - See the n8n Workflow Documentation for troubleshooting