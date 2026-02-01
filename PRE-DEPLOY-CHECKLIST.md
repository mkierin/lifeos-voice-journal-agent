# Pre-Deployment Checklist

Before pushing to GitHub and deploying to your VPS, complete this checklist:

## ✅ Local Testing

- [x] Docker image builds successfully
- [x] Docker containers start without errors
- [x] Bot connects to Telegram
- [x] Qdrant is accessible
- [x] Integration tests pass

**Run the tests:**
```bash
bash tests/test_docker_simple.sh
```

## 🔒 Security

- [ ] Verify `.env` file is **NOT** tracked by git
  ```bash
  git status
  # .env should NOT appear in the list
  ```

- [ ] `.env.example` has no real API keys
  ```bash
  cat .env.example
  # Should only have placeholder values
  ```

- [ ] No API keys in git history
  ```bash
  git log --all --full-history -- .env
  # Should be empty or show only deletions
  ```

## 📦 Files to Commit

These files should be committed:
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `.dockerignore`
- `bot/` directory
- `tests/` directory
- `README.md`, `DEPLOYMENT.md`

These should **NOT** be committed:
- `.env` (contains real API keys!)
- `data/` (local data)
- `logs/` (local logs)
- `qdrant_data/` (local database)
- `__pycache__/`
- `.next/`
- `node_modules/`

## 🚀 Deployment Steps

### 1. Final Local Test
```bash
docker-compose down
docker-compose up -d
bash tests/test_docker_simple.sh
```

### 2. Commit and Push to GitHub
```bash
git add .
git status  # Verify .env is NOT in the list!
git commit -m "Ready for deployment: Docker setup and tests"
git push origin main
```

### 3. Deploy to VPS
```bash
# On your local machine
scp -r orchids-voice-journal-app root@your-vps-ip:/opt/

# SSH into VPS
ssh root@your-vps-ip

# On VPS
cd /opt/orchids-voice-journal-app

# Create .env file with your API keys
cp .env.example .env
nano .env  # Add your real API keys

# Install Docker if not already installed
curl -fsSL https://get.docker.com | sh

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f voice-journal-bot
```

### 4. Verify Deployment
On your VPS, run:
```bash
docker-compose ps  # Should show both containers running
curl http://localhost:6333/  # Should return Qdrant info
docker logs voice-journal-bot --tail 20  # Should show "Bot started"
```

## 🧪 Quick Test Command

Run this before pushing:
```bash
docker-compose down && docker-compose up -d && sleep 5 && bash tests/test_docker_simple.sh
```

All tests should pass before deploying!

## 📝 Environment Variables Needed on VPS

Make sure your `.env` file on the VPS has:
- `TELEGRAM_TOKEN` - From @BotFather
- `DEEPSEEK_API_KEY` - From platform.deepseek.com
- `OPENAI_API_KEY` - From platform.openai.com (optional)
- `LLM_PROVIDER` - "deepseek" or "openai"
- `QDRANT_HOST` - "qdrant" (for Docker)
- `QDRANT_PORT` - "6333"

## 🎯 Post-Deployment

After deploying to VPS:
1. Test the bot by sending a message on Telegram
2. Check logs: `docker-compose logs -f`
3. Verify data persistence: `ls -la qdrant_data/`
4. Monitor for a few hours
5. Set up monitoring/alerts (optional)

---

**Status:** ✅ Ready for deployment!
