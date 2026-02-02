# PM2 Deployment Guide (Persistent Memory)

This setup assumes you want to run the bot on a VPS using PM2 (for the bot) and a System Service (for Qdrant database).

## 💾 Data Persistence Strategy

**Your data is safe.**

- **Code:** Lives in `~/orchids-voice-journal-app` (updated via git).
- **Database:** Lives in `~/qdrant_data` (NOT touched by git).

When you run `deploy-pm2.sh`, it configures Qdrant to use `~/qdrant_data`. This means you can delete the code folder, update it, or change branches, and your bot's memory remains intact.

## 🚀 Initial Deployment

1.  **Connect to VPS:**
    ```bash
    ssh user@your-vps-ip
    ```

2.  **Download Code:**
    ```bash
    git clone git@github.com:mkierin/lifeos-voice-journal-agent.git orchids-voice-journal-app
    cd orchids-voice-journal-app
    ```

3.  **Setup Environment:**
    ```bash
    cp .env.example .env
    nano .env
    # Paste your keys. Ensure QDRANT_HOST=localhost
    ```

4.  **Run Installer:**
    ```bash
    chmod +x deploy-pm2.sh
    ./deploy-pm2.sh
    ```

## 🔄 Updating the Bot (New Versions)

When you make changes locally and push to GitHub, run this on your VPS:

```bash
cd ~/orchids-voice-journal-app
git pull
./deploy-pm2.sh  # This re-installs dependencies and restarts the bot
```

**Your memory will explicitly remain because `./deploy-pm2.sh` does NOT touch `~/qdrant_data`.**

## 🛠 Troubleshooting

**Check Logs:**
```bash
pm2 logs voice-journal-bot
```

**Check Database Status:**
```bash
sudo systemctl status qdrant
```
