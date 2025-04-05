# Example usage: ./deploy-to-ec2.sh ~/.ssh/voice-timelogger-key.pem ec2-user@13.60.40.88

SSH_KEY=$1
EC2_ADDRESS=$2

if [ -z "$SSH_KEY" ] || [ -z "$EC2_ADDRESS" ]; then
  echo "Usage: $0 <ssh-key-path> <ec2-address>"
  exit 1
fi

# Create a deployment package excluding unnecessary files
echo "Creating deployment package..."
tar --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' --exclude='credentials/*.json' \
    -czf deployment.tar.gz src config requirements.txt docker-compose.yml \
    Dockerfile setup.sh .dockerignore .env.example

# Transfer the deployment package
echo "Transferring files to EC2..."
scp -i "$SSH_KEY" deployment.tar.gz "$EC2_ADDRESS:~/"

# Transfer sensitive files separately
scp -i "$SSH_KEY" .env "$EC2_ADDRESS:~/"
ssh -i "$SSH_KEY" "$EC2_ADDRESS" "mkdir -p ~/credentials"
scp -i "$SSH_KEY" credentials/google-service-account.json "$EC2_ADDRESS:~/credentials/"

# Deploy on EC2
echo "Deploying application on EC2..."
ssh -i "$SSH_KEY" "$EC2_ADDRESS" << 'EOF'
  mkdir -p voice-timelogger
  tar -xzf deployment.tar.gz -C voice-timelogger
  mv .env voice-timelogger/
  mv credentials voice-timelogger/
  cd voice-timelogger
  chmod +x setup.sh
  ./setup.sh
  docker-compose build --no-cache
  docker-compose up -d
EOF

# Clean up
rm deployment.tar.gz

echo "Deployment complete! Application is running on EC2."