#!/bin/bash
set -e

echo "Setting up Voice-TimeLogger-Agent..."

# Create required directories
mkdir -p ./tmp/meeting_recordings ./credentials

# Set permissions
chmod -R 777 ./tmp

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Creating example .env file. Please edit with your actual credentials."
  cp .env.example .env 2>/dev/null || echo "No .env.example found. Please create .env manually."
fi

echo "Setup complete!"
echo "Next steps:"
echo "1. Make sure your .env file has your API keys"
echo "2. Add Google service account JSON to ./credentials/"
echo "3. Run 'docker-compose up -d' to start the service"