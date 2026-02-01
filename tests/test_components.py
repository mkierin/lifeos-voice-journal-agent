"""
Unit tests for individual components
Tests VectorStore, Config, and LLM client functionality
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config_loads_environment():
    """Test that config properly loads environment variables"""
    # Set test environment
    os.environ["TELEGRAM_TOKEN"] = "test_token_123"
    os.environ["DEEPSEEK_API_KEY"] = "test_deepseek_key"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    os.environ["LLM_PROVIDER"] = "deepseek"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"

    from bot import config

    # Force reload
    import importlib
    importlib.reload(config)

    assert config.TELEGRAM_TOKEN == "test_token_123"
    assert config.DEEPSEEK_API_KEY == "test_deepseek_key"
    assert config.OPENAI_API_KEY == "test_openai_key"
    assert config.QDRANT_HOST == "localhost"
    assert config.QDRANT_PORT == 6333

    print("✅ Config loads environment variables correctly")


def test_config_has_categories():
    """Test that config has predefined categories"""
    from bot.config import CATEGORIES

    assert "fitness" in CATEGORIES
    assert "goals" in CATEGORIES
    assert "ideas" in CATEGORIES
    assert "journal" in CATEGORIES

    assert isinstance(CATEGORIES["fitness"], list)
    assert len(CATEGORIES["fitness"]) > 0

    print(f"✅ Config has {len(CATEGORIES)} categories defined")


def test_vector_store_initialization():
    """Test that VectorStore can be initialized with different backends"""
    os.environ["QDRANT_HOST"] = ":memory:"
    os.environ["QDRANT_PORT"] = "6333"

    from bot.vector_store import VectorStore

    vs = VectorStore()
    assert vs.client is not None
    assert vs.collection_name == "journal"
    assert vs.tasks_collection == "tasks"

    print("✅ VectorStore initializes correctly")


def test_vector_store_add_and_search():
    """Test basic add and search functionality"""
    os.environ["QDRANT_HOST"] = ":memory:"

    from bot.vector_store import VectorStore

    vs = VectorStore()
    test_user = 123456

    # Add entries
    entry1 = vs.add_entry(
        text="I went for a 5km run today. Feeling great!",
        categories=["fitness", "journal"],
        user_id=test_user
    )

    entry2 = vs.add_entry(
        text="Planning to learn Python this month",
        categories=["goals", "learning"],
        user_id=test_user
    )

    entry3 = vs.add_entry(
        text="Had a great meeting with the client about the new project",
        categories=["work"],
        user_id=test_user
    )

    assert entry1 is not None
    assert entry2 is not None
    assert entry3 is not None

    # Search for fitness-related entries
    results = vs.search("running exercise", test_user, limit=3)
    assert len(results) > 0
    assert "run" in results[0].payload["text"].lower()

    # Search for learning/goals
    results = vs.search("learning programming", test_user, limit=3)
    assert len(results) > 0

    print("✅ VectorStore add and search works correctly")


def test_vector_store_recent_entries():
    """Test getting recent entries"""
    os.environ["QDRANT_HOST"] = ":memory:"

    from bot.vector_store import VectorStore

    vs = VectorStore()
    test_user = 789012

    # Add multiple entries
    for i in range(5):
        vs.add_entry(
            text=f"Journal entry number {i+1}",
            categories=["journal"],
            user_id=test_user
        )

    # Get recent entries
    recent = vs.get_recent_entries(test_user, limit=3)
    assert len(recent) == 3

    # Check they're sorted by timestamp (most recent first)
    timestamps = [entry.payload["timestamp"] for entry in recent]
    assert timestamps == sorted(timestamps, reverse=True)

    print(f"✅ Retrieved {len(recent)} recent entries in correct order")


def test_vector_store_task_management():
    """Test task management functionality"""
    os.environ["QDRANT_HOST"] = ":memory:"

    from bot.vector_store import VectorStore

    vs = VectorStore()
    test_user = 345678

    # Create tasks
    task1 = vs.upsert_task(
        user_id=test_user,
        task_id="task-1",
        description="Complete the project proposal",
        status="open",
        due_date="2026-02-15"
    )

    task2 = vs.upsert_task(
        user_id=test_user,
        task_id="task-2",
        description="Review pull requests",
        status="open"
    )

    task3 = vs.upsert_task(
        user_id=test_user,
        task_id="task-3",
        description="Deploy to production",
        status="completed"
    )

    # Get all open tasks
    open_tasks = vs.get_tasks(test_user, status="open")
    assert len(open_tasks) == 2

    # Get all tasks
    all_tasks = vs.get_tasks(test_user)
    assert len(all_tasks) == 3

    # Get completed tasks
    completed_tasks = vs.get_tasks(test_user, status="completed")
    assert len(completed_tasks) == 1

    # Update a task
    vs.upsert_task(
        user_id=test_user,
        task_id="task-1",
        description="Complete the project proposal",
        status="completed"
    )

    open_tasks = vs.get_tasks(test_user, status="open")
    assert len(open_tasks) == 1

    print("✅ Task management works correctly")


def test_settings_persistence():
    """Test that settings can be saved and loaded"""
    from bot.config import save_settings, load_settings, DEFAULT_SETTINGS

    test_settings = {
        "llm_provider": "openai",
        "temperature": 0.8,
        "max_tokens": 1000,
        "system_prompt": "Test prompt"
    }

    save_settings(test_settings)
    loaded = load_settings()

    assert loaded["llm_provider"] == "openai"
    assert loaded["temperature"] == 0.8
    assert loaded["max_tokens"] == 1000

    print("✅ Settings persistence works correctly")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Component Unit Tests")
    print("="*60 + "\n")

    # Run tests
    test_config_loads_environment()
    test_config_has_categories()
    test_vector_store_initialization()
    test_vector_store_add_and_search()
    test_vector_store_recent_entries()
    test_vector_store_task_management()
    test_settings_persistence()

    print("\n" + "="*60)
    print("✅ All component tests passed!")
    print("="*60 + "\n")
