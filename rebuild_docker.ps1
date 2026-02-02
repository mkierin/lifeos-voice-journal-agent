# Stop and remove all containers
Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker stop $(docker ps -aq) 2>$null
docker rm $(docker ps -aq) 2>$null

# Remove old images
Write-Host "Removing old images..." -ForegroundColor Yellow
docker rmi orchids-voice-journal-app-voice-journal-bot 2>$null

# Clean up networks
Write-Host "Cleaning up networks..." -ForegroundColor Yellow
docker network prune -f 2>$null

# Rebuild and start
Write-Host "Building and starting containers..." -ForegroundColor Green
docker-compose up -d --build

# Wait a bit for startup
Start-Sleep -Seconds 10

# Check status
Write-Host "`nContainer Status:" -ForegroundColor Cyan
docker ps

Write-Host "`nBot Logs:" -ForegroundColor Cyan
docker logs voice-journal-bot --tail 20
