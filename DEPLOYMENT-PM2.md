# PM2 Deployment Guide

This guide explains how to deploy the Voice Journal Bot using PM2 instead of Docker.

## Prerequisites

- Ubuntu/Debian VPS with SSH access
- Python 3.8+
- Node.js 18+ (for PM2)

## Quick Start

1. **Clone the repository on your VPS:**
   ```bash
   cd ~
   git clone git@github.com:mkierin/lifeos-voice-journal-agent.git orchids-voice-journal-app
   cd orchids-voice-journal-app
   ```

2. **Create your .env file:**
   ```bash
   cp .env.example .env
   nano .env  # Add your actual API keys
   ```

3. **Run the deployment script:**
   ```bash
   chmod +x deploy-pm2.sh
   ./deploy-pm2.sh
   ```

That's it! The bot will be running and managed by PM2.

## PM2 Commands

### Check Status
```bash
pm2 status
```

### View Logs
```bash
pm2 logs voice-journal-bot
pm2 logs voice-journal-bot --lines 100  # Last 100 lines
```

### Restart Bot
```bash
pm2 restart voice-journal-bot
```

### Stop Bot
```bash
pm2 stop voice-journal-bot
```

### Monitor Resources
```bash
pm2 monit
```

### View Detailed Info
```bash
pm2 show voice-journal-bot
```

## Update Deployment

When you push changes to GitHub:

```bash
cd ~/orchids-voice-journal-app
git pull
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed
pm2 restart voice-journal-bot
```

## Qdrant Management

Qdrant runs as a systemd service:

```bash
# Check status
sudo systemctl status qdrant

# Restart
sudo systemctl restart qdrant

# View logs
sudo journalctl -u qdrant -f
```

## Troubleshooting

### Bot not starting?
```bash
# Check logs
pm2 logs voice-journal-bot --err

# Check if Qdrant is running
curl http://localhost:6333/health
```

### Environment variables not loading?
Make sure your `.env` file is in the project root and contains all required variables.

### Python dependencies issues?
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
pm2 restart voice-journal-bot
```

## Advantages over Docker

- ✅ **Simpler setup** - No Docker installation needed
- ✅ **Easier debugging** - Direct access to Python process
- ✅ **Better logs** - PM2 provides excellent log management
- ✅ **Lower overhead** - No container layer
- ✅ **Faster restarts** - No image building
- ✅ **Auto-restart** - PM2 handles crashes automatically

## Migration from Docker

If you're currently using Docker:

1. Stop Docker containers: `docker-compose down`
2. Follow the Quick Start guide above
3. Your data in `qdrant_data/` will be preserved
4. Optionally remove Docker files: `rm Dockerfile docker-compose.yml`
