#!/bin/bash

# Voice Journal Bot - PM2 Deployment Script
# This script sets up and deploys the bot using PM2 and Native Qdrant

set -e

echo "🚀 Starting PM2 deployment..."

# 1. Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Python, pip, and system dependencies
echo "🐍 Installing Python 3..."
sudo apt install -y python3 python3-pip python3-venv unzip

# 3. Install Node.js and PM2
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing Node.js and PM2..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    sudo npm install -g pm2
fi

# 4. Install and setup Qdrant (Native System Service)
echo "🗄️ Setting up Qdrant..."
QDRANT_DATA_DIR="$HOME/qdrant_data"

if ! command -v qdrant &> /dev/null; then
    echo "   Downloading Qdrant..."
    # Download latest linux binary
    wget https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-x86_64-unknown-linux-gnu.tar.gz
    tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
    sudo mv qdrant /usr/local/bin/
    rm qdrant-x86_64-unknown-linux-gnu.tar.gz
    
    # Create persistent data directory OUTSIDE project folder
    echo "   Creating persistent data directory at $QDRANT_DATA_DIR"
    mkdir -p "$QDRANT_DATA_DIR"
    
    # Create systemd service
    echo "   Creating Qdrant system service..."
    sudo tee /etc/systemd/system/qdrant.service > /dev/null <<EOF
[Unit]
Description=Qdrant Vector Database
After=network.target

[Service]
Type=simple
User=$USER
# CRITICAL: This line ensures data persists in $HOME/qdrant_data
ExecStart=/usr/local/bin/qdrant --storage-path $QDRANT_DATA_DIR
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Start Qdrant
    sudo systemctl daemon-reload
    sudo systemctl enable qdrant
    sudo systemctl start qdrant
    echo "   ✅ Qdrant service started"
else
    echo "   ✅ Qdrant is already installed"
fi

# 5. Setup Bot Application
echo "🤖 Setting up Bot Application..."
# Navigate to script directory (assuming this script is inside the repo)
cd "$(dirname "$0")"

# Create/Update virtual environment
echo "   🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "   📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. PM2 Process Management
echo "   🚀 Starting bot using PM2..."

# Check if app is already running
if pm2 list | grep -q "voice-journal-bot"; then
    echo "   Restarting existing bot..."
    pm2 restart voice-journal-bot
else
    echo "   Starting new bot instance..."
    pm2 start ecosystem.config.js
fi

# Save PM2 list so it restarts on reboot
pm2 save
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

echo ""
echo "✅ Deployment complete!"
echo "---------------------------------------------------"
echo "📂 Data persistence: $QDRANT_DATA_DIR (Safe from git updates)"
echo "📜 View logs:        pm2 logs voice-journal-bot"
echo "🔁 Update code:      git pull && pm2 restart voice-journal-bot"
echo "---------------------------------------------------"
