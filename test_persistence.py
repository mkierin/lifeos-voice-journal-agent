
import os
import time
from bot.vector_store import VectorStore
from dotenv import load_dotenv

load_dotenv()

def test_persistence():
    # Force use of local path for this specific test script to check actual files
    # or just use the current env which should be 'qdrant'
    print(f"Testing persistence with QDRANT_HOST: {os.getenv('QDRANT_HOST')}")
    
    vs = VectorStore()
    test_text = f"Persistence test entry at {time.time()}"
    user_id = 999
    
    print("Step 1: Adding test entry...")
    vs.add_entry(test_text, ["test"], user_id)
    
    print("Step 2: Verifying entry exists...")
    results = vs.search(test_text, user_id)
    if not results:
        print("❌ Failed: Entry not found immediately after adding.")
        return False
    print("✅ Entry found.")
    
    print("\n--- INSTRUCTIONS ---")
    print("To truly verify persistence:")
    print("1. Run 'docker-compose restart qdrant'")
    print("2. Run this script again but comment out the 'add_entry' line.")
    print("3. If the search still finds the entry, volume mapping is working.")
    print("---------------------\n")
    return True

if __name__ == "__main__":
    test_persistence()
