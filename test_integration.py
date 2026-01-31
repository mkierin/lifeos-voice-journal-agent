import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add current directory to path
sys.path.append(os.path.abspath("."))

from bot.vector_store import VectorStore
from bot.llm_client import LLMClient, JournalDeps

def test_integration():
    print("🚀 Starting Integration Test (In-Memory Qdrant + DeepSeek)...")
    
    # 1. Initialize Vector Store (In-Memory)
    vs = VectorStore()
    print("✅ Vector Store initialized (In-Memory)")
    
    # 2. Add a sample entry
    user_id = 999
    entry_text = "Today I worked on my AI voice journal project. It's going well!"
    categories = ["work", "ideas"]
    vs.add_entry(entry_text, categories, user_id)
    print(f"✅ Sample entry added: {entry_text}")
    
    # 3. Initialize LLM Client
    client = LLMClient()
    print(f"✅ LLM Client initialized (Provider: {client.provider})")
    
    # 4. Test Classification
    print("\n--- Testing Classification ---")
    test_text = "I went for a 5km run this morning."
    detected = client.classify_categories(test_text)
    print(f"Input: {test_text}")
    print(f"Detected Categories: {detected}")
    
    # 5. Test Agent with Tools (Search)
    print("\n--- Testing Agent Search ---")
    deps = JournalDeps(vector_store=vs, user_id=user_id)
    query = "What did I do today?"
    print(f"Query: {query}")
    
    # Run the agent
    response = client.agent.run_sync(query, deps=deps)
    print(f"AI Response: {response.data}")

if __name__ == "__main__":
    try:
        test_integration()
        print("\n✨ Integration test completed successfully!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
