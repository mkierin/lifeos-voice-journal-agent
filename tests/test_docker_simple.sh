#!/bin/bash
# Simple Docker integration tests using curl

set -e

echo ""
echo "============================================================"
echo "Docker Integration Tests - Simple Version"
echo "============================================================"
echo ""

# Test 1: Check Qdrant is running
echo "Test 1: Checking if Qdrant is running..."
if curl -s http://localhost:6333/ | grep -q "qdrant"; then
    echo "✅ Qdrant is running and healthy"
else
    echo "❌ Qdrant is not responding"
    exit 1
fi

# Test 2: Check Qdrant collections endpoint
echo ""
echo "Test 2: Checking Qdrant collections endpoint..."
if curl -s http://localhost:6333/collections | grep -q "result"; then
    echo "✅ Qdrant collections endpoint is working"
else
    echo "❌ Qdrant collections endpoint failed"
    exit 1
fi

# Test 3: Check Docker containers are running
echo ""
echo "Test 3: Checking Docker containers..."
if docker ps | grep -q "qdrant"; then
    echo "✅ Qdrant container is running"
else
    echo "❌ Qdrant container is not running"
    exit 1
fi

if docker ps | grep -q "voice-journal-bot"; then
    echo "✅ Voice Journal Bot container is running"
else
    echo "❌ Voice Journal Bot container is not running"
    exit 1
fi

# Test 4: Check bot logs for successful startup
echo ""
echo "Test 4: Checking bot startup logs..."
if docker logs voice-journal-bot 2>&1 | grep -q "Voice Journal Bot started\|Application started"; then
    echo "✅ Bot started successfully"
else
    echo "❌ Bot did not start successfully"
    exit 1
fi

# Test 5: Check that Qdrant has the expected collections
echo ""
echo "Test 5: Checking for journal collections..."
COLLECTIONS=$(curl -s http://localhost:6333/collections)
if echo "$COLLECTIONS" | grep -q "journal"; then
    echo "✅ Journal collection exists"
else
    echo "⚠️  Journal collection not found (will be created on first use)"
fi

if echo "$COLLECTIONS" | grep -q "tasks"; then
    echo "✅ Tasks collection exists"
else
    echo "⚠️  Tasks collection not found (will be created on first use)"
fi

# Test 6: Test data persistence volumes
echo ""
echo "Test 6: Checking data volumes..."
if docker volume ls | grep -q "qdrant"; then
    echo "✅ Qdrant data volume exists"
else
    echo "⚠️  Qdrant data volume not found"
fi

if [ -d "./qdrant_data" ]; then
    echo "✅ Local qdrant_data directory exists"
else
    echo "⚠️  Local qdrant_data directory not found"
fi

if [ -d "./data" ]; then
    echo "✅ Local data directory exists"
else
    echo "⚠️  Local data directory not found"
fi

echo ""
echo "============================================================"
echo "✅ All Docker integration tests passed!"
echo "============================================================"
echo ""

# Display container status
echo "Container Status:"
docker-compose ps

echo ""
echo "Recent bot logs:"
docker logs voice-journal-bot --tail 5
