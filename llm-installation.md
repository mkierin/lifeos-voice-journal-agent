# Hetzner VPS Deployment Instructions

This guide provides step-by-step instructions for deploying the Voice Journal Bot to a Hetzner VPS (Linux) while ensuring data persistence.

## 1. Local Setup (Preparation)

### Git Repository
1.  **Initialize Git**: If not already done, run `git init` in your local project folder.
2.  **Verify .gitignore**: Ensure `.env`, `data/`, and `qdrant_data/` are ignored to prevent leaking secrets and to keep the repository clean.
3.  **Push to GitHub**:
    - Create a private repository on GitHub.
    - Add the remote: `git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`
    - Push your code: `git push -u origin main`

## 2. VPS Prerequisites

Ensure the following are installed on your Hetzner VPS:
- **Git**: `sudo apt update && sudo apt install git -y`
- **Docker**: [Official Install Guide](https://docs.docker.com/engine/install/ubuntu/)
- **Docker Compose**: Usually included with Docker Desktop/Engine, verify with `docker compose version`.

## 3. Deployment on VPS

### Initial Setup
1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    cd YOUR_REPO_NAME
    ```
2.  **Configure Environment**:
    - Create a `.env` file on the VPS: `nano .env`
    - Copy the contents from your local `.env` file and paste them.
    - **Crucial**: Ensure `QDRANT_HOST=qdrant` in the VPS `.env` file (this allows the bot to talk to the qdrant container within the docker network).

### Start the Application
Run the following command to build and start the containers in detached mode:
```bash
docker compose up -d --build
```

## 4. Knowledge Persistence & Updates

### How Persistence Works
- The `docker-compose.yml` file is configured to use **Volumes**.
- It maps `./qdrant_data` on the VPS host to the database inside the container.
- **This means all journal entries are stored on the VPS disk, not inside the temporary container memory.**

### Updating the App
When you make changes locally and push to GitHub, follow these steps on the VPS:
1.  **Pull Changes**: `git pull origin main`
2.  **Restart Containers**:
    ```bash
    docker compose up -d --build
    ```
- **Note**: Your database (`qdrant_data/`) will remain untouched during this process. The bot will restart with the new code but keep all previous "knowledge".

## 5. Troubleshooting
- **Logs**: To see what the bot is doing, run: `docker compose logs -f voice-journal-bot`
- **Database Status**: To check Qdrant logs: `docker compose logs -f qdrant`
- **Permissions**: If you encounter permission errors with `qdrant_data`, run: `sudo chown -R 1000:1000 qdrant_data`
