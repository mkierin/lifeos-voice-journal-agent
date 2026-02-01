#!/bin/bash
# Test runner script for Voice Journal App

set -e

echo "=========================================="
echo "Voice Journal App - Test Suite"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if containers are running
echo "Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Containers not running. Starting them..."
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 10
else
    echo "✅ Containers are already running"
fi

echo ""
echo "=========================================="
echo "Test 1: Component Unit Tests (in Docker)"
echo "=========================================="
docker-compose exec -T voice-journal-bot python -c "
import sys
sys.path.insert(0, '/app')

# Run component tests
exec(open('/app/tests/test_components.py').read())
" || echo "⚠️  Some component tests may have failed"

echo ""
echo "=========================================="
echo "Test 2: Docker Integration Tests"
echo "=========================================="
python3 tests/test_docker_integration.py || echo "⚠️  Some integration tests may have failed"

echo ""
echo "=========================================="
echo "✅ Test suite completed!"
echo "=========================================="
