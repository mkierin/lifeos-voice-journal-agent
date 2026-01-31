import os
import sys
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add current directory to path so we can import bot
sys.path.append(os.path.abspath("."))

from bot.llm_client import LLMClient, JournalDeps

# Mock VectorStore result
class MockResult:
    def __init__(self, text, timestamp):
        self.payload = {"text": text, "timestamp": timestamp}

def test_pydantic_ai_agents():
    print("Starting Pydantic AI Agent Test...")
    
    # 1. Setup Mock VectorStore
    mock_vs = MagicMock()
    mock_vs.search.return_value = [
        MockResult("I went to the gym today and did some heavy squats.", "2026-01-29T10:00:00Z"),
        MockResult("Started reading a new book about Stoicism.", "2026-01-28T22:00:00Z")
    ]
    mock_vs.get_recent_entries.return_value = [
        MockResult("I went to the gym today and did some heavy squats.", "2026-01-29T10:00:00Z")
    ]
    
    client = LLMClient()
    deps = JournalDeps(vector_store=mock_vs, user_id=12345)
    
    # 2. Test Classification (Structured Output)
    print("\n--- Testing Classification ---")
    entry = "I crushed my leg day today, feeling great but tired."
    categories = client.classify_categories(entry)
    print(f"Entry: {entry}")
    print(f"Detected Categories: {categories}")
    
    # 3. Test Agent with Tools (RAG simulation)
    print("\n--- Testing Agent with Tools ---")
    prompt = "What did I do for exercise recently according to my journal?"
    print(f"Prompt: {prompt}")
    
    # Run agent directly with deps to test tool usage
    result = client.agent.run_sync(prompt, deps=deps)
    print(f"Response: {result.output}")
    
    # Verify tool was called
    mock_vs.search.assert_called()
    print("Success: Tool 'search_journal' was correctly called by the agent.")

if __name__ == "__main__":
    print("Main block started")
    try:
        test_pydantic_ai_agents()
        print("\nAll agent tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
