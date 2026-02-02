#!/bin/bash

# Voice Journal Bot - PM2 Deployment Script
# This script sets up and deploys the bot using PM2 instead of Docker

set -e

echo "🚀 Starting PM2 deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not already installed
echo "🐍 Installing Python 3..."
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js and PM2 (if not already installed)
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing Node.js and PM2..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    sudo npm install -g pm2
fi

# Install and setup Qdrant
echo "🗄️ Setting up Qdrant..."
if ! command -v qdrant &> /dev/null; then
    # Download and install Qdrant
    wget https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-x86_64-unknown-linux-gnu.tar.gz
    tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
    sudo mv qdrant /usr/local/bin/
    rm qdrant-x86_64-unknown-linux-gnu.tar.gz
    
    # Create Qdrant data directory
    mkdir -p ~/qdrant_data
    
    # Create systemd service for Qdrant
    sudo tee /etc/systemd/system/qdrant.service > /dev/null <<EOF
[Unit]
Description=Qdrant Vector Database
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
ExecStart=/usr/local/bin/qdrant --storage-path $HOME/qdrant_data
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start Qdrant
    sudo systemctl daemon-reload
    sudo systemctl enable qdrant
    sudo systemctl start qdrant
fi

# Navigate to project directory
cd ~/orchids-voice-journal-app

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Load environment variables
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Please create it from .env.example"
    exit 1
fi

# Start the bot with PM2
echo "🤖 Starting bot with PM2..."
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on system boot
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

echo "✅ Deployment complete!"
echo ""
echo "Useful PM2 commands:"
echo "  pm2 status              - Check bot status"
echo "  pm2 logs                - View logs"
echo "  pm2 restart voice-journal-bot - Restart bot"
echo "  pm2 stop voice-journal-bot    - Stop bot"
echo "  pm2 monit               - Monitor resources"
