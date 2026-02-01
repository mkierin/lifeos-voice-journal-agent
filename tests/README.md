# Tests for Voice Journal App

This directory contains tests for the Voice Journal application.

## Test Files

### 1. `test_docker_simple.sh` (Recommended)
Simple shell-based integration tests that verify the Docker setup is working correctly.

**Run it:**
```bash
bash tests/test_docker_simple.sh
```

**What it tests:**
- Qdrant service is running and accessible
- Collections API is working
- Docker containers are up and running
- Bot started successfully
- Data persistence volumes exist

### 2. `test_docker_integration.py`
Python-based integration tests (requires dependencies).

**Run it inside Docker:**
```bash
docker-compose exec voice-journal-bot python /app/tests/test_docker_integration.py
```

**What it tests:**
- Full VectorStore functionality with Docker Qdrant
- Search and retrieval operations
- Task management
- Container health

### 3. `test_components.py`
Unit tests for individual components (requires dependencies).

**Run it inside Docker:**
```bash
docker-compose exec voice-journal-bot python /app/tests/test_components.py
```

**What it tests:**
- Config loading
- VectorStore with in-memory backend
- Settings persistence
- Task management

## Quick Test

Before deploying or pushing to GitHub, run:

```bash
# Make sure containers are running
docker-compose up -d

# Run the simple test suite
bash tests/test_docker_simple.sh
```

If all tests pass, your Docker setup is ready for deployment!

## Expected Output

```
✅ Qdrant is running and healthy
✅ Qdrant collections endpoint is working
✅ Qdrant container is running
✅ Voice Journal Bot container is running
✅ Bot started successfully
✅ All Docker integration tests passed!
```
