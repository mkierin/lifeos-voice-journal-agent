
from bot.vector_store import VectorStore
import os

# Set dummy env vars for local test if not present
os.environ["QDRANT_HOST"] = "./test_qdrant"
os.environ["QDRANT_PORT"] = "6333"

def test_vector_store():
    print("Initializing VectorStore...")
    vs = VectorStore()
    
    print("Adding an entry...")
    vs.add_entry("Today I worked on my voice journal bot. It's going well.", ["work", "ideas"], 12345)
    
    print("Searching for entry...")
    results = vs.search("What did I work on today?", 12345)
    
    print(f"Results: {results}")
    if len(results) > 0:
        print("✅ VectorStore test passed!")
    else:
        print("❌ VectorStore test failed: No results found.")

if __name__ == "__main__":
    test_vector_store()
