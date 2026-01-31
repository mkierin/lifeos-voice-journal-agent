# Voice Journal Bot
 
Personal voice journaling assistant with Telegram, Whisper transcription, and AI-powered responses.
 
## Features
 
- 🎙️ Voice message transcription (OpenAI Whisper)
- 🤖 AI responses with DeepSeek/OpenAI API
- 🔍 Semantic search across your journal
- 🏷️ Auto-categorization (fitness, goals, ideas, etc.)
- 💰 Ultra low-cost (~€5/month)
 
## Setup
 
### 1. Get API Keys
 
- **Telegram Bot**: Talk to [@BotFather](https://t.me/botfather)
- **DeepSeek API**: [platform.deepseek.com](https://platform.deepseek.com/)
- **OpenAI API** (optional): [platform.openai.com](https://platform.openai.com/)
 
### 2. Configure
 
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Deploy to Hetzner
 
```bash
# On your local machine
scp -r voice-journal root@your-vps-ip:/opt/
 
# SSH into VPS
ssh root@your-vps-ip
 
# Install Docker
curl -fsSL https://get.docker.com | sh
 
# Start services
cd /opt/voice-journal
docker-compose up -d
 
# View logs
docker-compose logs -f voice-journal-bot
```

## Usage
- Send voice messages to journal
- Ask questions: "What were my fitness goals?"
- Category search: "fitness: what should I do today?"
- Switch APIs: /switch deepseek or /switch openai
- View stats: /stats
- Recent entries: /recent
