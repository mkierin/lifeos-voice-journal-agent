"""
Integration tests for Docker setup
Tests that all services are running and can communicate
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse


def test_qdrant_is_running():
    """Test that Qdrant service is running and accessible"""
    client = QdrantClient(host="localhost", port=6333)

    # Try to get collections - this will fail if Qdrant is not running
    try:
        collections = client.get_collections()
        assert collections is not None
        print("✅ Qdrant is running and accessible")
    except Exception as e:
        raise AssertionError(f"Qdrant is not accessible: {e}")


def test_qdrant_can_create_collection():
    """Test that we can create and use collections in Qdrant"""
    client = QdrantClient(host="localhost", port=6333)

    test_collection = "test_collection"

    # Clean up if exists
    try:
        client.delete_collection(test_collection)
    except:
        pass

    # Create a simple collection
    client.add(
        collection_name=test_collection,
        documents=["This is a test document"],
        ids=[1]
    )

    # Verify collection was created
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    assert test_collection in collection_names

    # Clean up
    client.delete_collection(test_collection)
    print("✅ Can create and delete collections in Qdrant")


def test_vector_store_with_docker_qdrant():
    """Test VectorStore class with Docker Qdrant instance"""
    # Set environment to use Docker Qdrant
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"

    from bot.vector_store import VectorStore

    vs = VectorStore()

    # Test user ID
    test_user_id = 999999

    # Add a test entry
    entry_id = vs.add_entry(
        text="Testing Docker integration with a voice journal entry about fitness and goals",
        categories=["fitness", "goals"],
        user_id=test_user_id
    )

    assert entry_id is not None
    print(f"✅ Added entry with ID: {entry_id}")

    # Search for the entry
    results = vs.search("fitness goals", test_user_id, limit=5)
    assert len(results) > 0
    assert results[0].payload["user_id"] == test_user_id
    print(f"✅ Found {len(results)} results for search query")

    # Get recent entries
    recent = vs.get_recent_entries(test_user_id, limit=5)
    assert len(recent) > 0
    print(f"✅ Retrieved {len(recent)} recent entries")

    # Test task management
    task_id = vs.upsert_task(
        user_id=test_user_id,
        task_id="test-task-1",
        description="Test task for Docker integration",
        status="open"
    )

    assert task_id == "test-task-1"
    print(f"✅ Created task with ID: {task_id}")

    # Get tasks
    tasks = vs.get_tasks(test_user_id, status="open")
    assert len(tasks) > 0
    assert tasks[0].payload["description"] == "Test task for Docker integration"
    print(f"✅ Retrieved {len(tasks)} open tasks")


def test_bot_container_is_running():
    """Test that the bot container is running"""
    import subprocess

    result = subprocess.run(
        ["docker", "ps", "--filter", "name=voice-journal-bot", "--format", "{{.Status}}"],
        capture_output=True,
        text=True
    )

    assert "Up" in result.stdout, "Bot container is not running"
    print("✅ Bot container is running")


def test_bot_logs_show_startup():
    """Test that bot logs show successful startup"""
    import subprocess

    result = subprocess.run(
        ["docker", "logs", "voice-journal-bot", "--tail", "50"],
        capture_output=True,
        text=True
    )

    logs = result.stdout + result.stderr
    assert "Voice Journal Bot started" in logs or "Application started" in logs
    print("✅ Bot started successfully (found startup message in logs)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Docker Integration Tests")
    print("="*60 + "\n")

    # Run tests
    test_qdrant_is_running()
    test_qdrant_can_create_collection()
    test_vector_store_with_docker_qdrant()
    test_bot_container_is_running()
    test_bot_logs_show_startup()

    print("\n" + "="*60)
    print("✅ All Docker integration tests passed!")
    print("="*60 + "\n")
