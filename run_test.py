
import shutil
import os
from bot.vector_store import VectorStore

def clean_and_test():
    # Clean up
    for folder in ["test_qdrant", "qdrant_data"]:
        if os.path.exists(folder):
            print(f"Deleting {folder}...")
            shutil.rmtree(folder, ignore_errors=True)
    
    # Set env vars
    os.environ["QDRANT_HOST"] = "./test_qdrant"
    os.environ["QDRANT_PORT"] = "6333"
    
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
    clean_and_test()
