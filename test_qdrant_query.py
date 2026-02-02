
from qdrant_client import QdrantClient
import os

client = QdrantClient(":memory:")
client.set_model("BAAI/bge-small-en-v1.5")

client.add(
    collection_name="test",
    documents=["hello world"],
    metadata=[{"text": "hello world", "val": 1}],
    ids=[1]
)

results = client.query(
    collection_name="test",
    query_text="hello",
    limit=1
)

print(f"Result type: {type(results[0])}")
print(f"Result attributes: {dir(results[0])}")
if hasattr(results[0], 'payload'):
    print(f"Payload: {results[0].payload}")
if hasattr(results[0], 'metadata'):
    print(f"Metadata: {results[0].metadata}")

print("\n--- Testing Scroll ---")
scroll_results = client.scroll(collection_name="test", with_payload=True)
print(f"Scroll results type: {type(scroll_results[0][0])}")
print(f"Scroll attributes: {dir(scroll_results[0][0])}")
if hasattr(scroll_results[0][0], 'payload'):
    print(f"Scroll Payload: {scroll_results[0][0].payload}")
