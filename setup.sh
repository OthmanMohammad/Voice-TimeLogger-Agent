set -e

echo "Setting up Voice-TimeLogger-Agent..."

# Create required directories
echo "Creating project directories..."
mkdir -p ./tmp/meeting_recordings ./credentials

# Set permissions
echo "Setting directory permissions..."
chmod -R 755 .
chmod -R 777 ./tmp

# Check if credentials file exists
if [ ! -f ./credentials/google-service-account.json ]; then
  echo "WARNING: Google service account JSON not found in ./credentials/"
  echo "You will need to add this file before the application can connect to Google Sheets"
fi

# Check if .env file exists
if [ ! -f .env ]; then
  echo "No .env file found. Creating from example..."
  cp .env.example .env 2>/dev/null || { echo "No .env.example found. Please create .env manually."; }
fi

echo "Setup complete!"
echo "Next steps:"
echo "1. Make sure your .env file has your API keys"
echo "2. Add Google service account JSON to ./credentials/google-service-account.json"
echo "3. Run 'docker-compose up -d' to start the service"