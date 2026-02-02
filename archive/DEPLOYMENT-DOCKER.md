# Deployment & VPS Installation Guide

This guide provides step-by-step instructions for deploying the **Voice Journal Bot** to a Linux VPS (e.g., Hetzner). It is designed to be easily readable by both humans and LLMs.

## 1. Prerequisites
- A Linux VPS (Ubuntu 22.04+ recommended)
- Docker and Docker Compose installed on the VPS
- A GitHub repository (public or private) to host your code
- SSH access to your VPS

## 2. GitHub Workflow (Recommended)
Developing on your local machine and pushing to GitHub is the best way to manage updates.

### Local Setup
1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   ```
2. Create a repository on GitHub and push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

### VPS Setup
1. Connect to your VPS: `ssh root@your_vps_ip`
2. Install Docker (if not present): [Official Docker Install Guide](https://docs.docker.com/engine/install/ubuntu/)
3. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   ```

## 3. Environment Configuration
Create a `.env` file on the VPS in the project root:
```bash
nano .env
```
Copy your credentials into it (refer to your local `.env`):
```env
TELEGRAM_TOKEN=your_token
OPENAI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
LLM_PROVIDER=deepseek
# DO NOT CHANGE THESE FOR DOCKER DEPLOYMENT
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

## 4. Launching the Application
Run the application using Docker Compose:
```bash
docker compose up -d --build
```
This will:
- Start the Qdrant vector database.
- Build and start the Telegram bot.
- Auto-restart if the server reboots.

## 5. Persistence & Knowledge Retention
**CRITICAL:** To ensure your data is never lost during upgrades:
- The `docker-compose.yml` maps `./qdrant_data` on your VPS to the database storage.
- **Never delete the `qdrant_data` folder.**
- When you update the code via `git pull`, the database remains untouched.
- To update the app:
  ```bash
  git pull
  docker compose up -d --build
  ```

## 6. Troubleshooting
- **Check logs:** `docker compose logs -f voice-journal-bot`
- **Check database status:** `docker compose logs -f qdrant`
- **Restart services:** `docker compose restart`

## 7. LLM Implementation Context
If you are an LLM helping with this installation:
- The bot runs as a Python module: `python -m bot.main`.
- It uses `qdrant-client` for vector storage.
- Persistence is handled by mounting `./qdrant_data` to `/qdrant/storage` in the `qdrant` container.
- Environment variables are passed through Docker Compose.
- The bot depends on `qdrant` being healthy before starting.
