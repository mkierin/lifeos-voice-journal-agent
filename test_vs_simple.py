import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath("."))

print("1. Importing VectorStore...")
from bot.vector_store import VectorStore
print("2. Initializing VectorStore (In-Memory)...")
try:
    vs = VectorStore()
    print("3. VectorStore initialized successfully!")
except Exception as e:
    print(f"FAILED: {e}")
