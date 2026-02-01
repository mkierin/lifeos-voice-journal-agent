from qdrant_client import QdrantClient, models
import uuid
from datetime import datetime
from .config import QDRANT_HOST, QDRANT_PORT

class VectorStore:
    def __init__(self):
        if QDRANT_HOST == ":memory:":
            self.client = QdrantClient(":memory:")
        else:
            # Check if QDRANT_HOST is a path (starts with . or / or \ or contains :)
            if QDRANT_HOST.startswith((".", "/", "\\")) or ":" in QDRANT_HOST[1:]:
                self.client = QdrantClient(path=QDRANT_HOST)
            else:
                self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        self.collection_name = "journal"
        self.tasks_collection = "tasks"
        
        # FastEmbed model
        self.model_name = "BAAI/bge-small-en-v1.5" # 384 dim, fast and light
        self.client.set_model(self.model_name)
        
    def add_entry(self, text: str, categories: list, user_id: int, metadata: dict = None):
        """Add journal entry to vector store using auto-embedding"""
        payload = {
            "text": text,
            "categories": categories,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        if metadata:
            payload.update(metadata)
        
        point_id = str(uuid.uuid4())
        
        self.client.add(
            collection_name=self.collection_name,
            documents=[text],
            metadata=[payload],
            ids=[point_id]
        )
        return point_id

    def upsert_task(self, user_id: int, task_id: str, description: str, status: str = "open", goal_id: str = None, due_date: str = None, metadata: dict = None):
        """Add or update a task using auto-embedding"""
        payload = {
            "description": description,
            "status": status,
            "user_id": user_id,
            "goal_id": goal_id,
            "due_date": due_date,
            "updated_at": datetime.now().isoformat()
        }
        if metadata:
            payload.update(metadata)
            
        self.client.add(
            collection_name=self.tasks_collection,
            documents=[description],
            metadata=[payload],
            ids=[task_id]
        )
        return task_id

    def get_tasks(self, user_id: int, status: str = None, goal_id: str = None):
        """Get tasks for a user with optional filters"""
        must_filters = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        if status:
            must_filters.append(models.FieldCondition(key="status", match=models.MatchValue(value=status)))
        if goal_id:
            must_filters.append(models.FieldCondition(key="goal_id", match=models.MatchValue(value=goal_id)))
            
        results = self.client.scroll(
            collection_name=self.tasks_collection,
            scroll_filter=models.Filter(must=must_filters),
            with_payload=True,
            with_vectors=False
        )
        return results[0]
    
    def search(self, query: str, user_id: int, categories: list = None, limit: int = 5):
        """Search for relevant entries using auto-embedding"""
        must_filters = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
        ]
        if categories:
            must_filters.append(models.FieldCondition(key="categories", match=models.MatchAny(any=categories)))
        
        results = self.client.query(
            collection_name=self.collection_name,
            query_text=query,
            query_filter=models.Filter(must=must_filters),
            limit=limit
        )
        
        return results
    
    def get_recent_entries(self, user_id: int, limit: int = 10):
        """Get recent entries for a user"""
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        return sorted(results[0], key=lambda x: x.payload["timestamp"], reverse=True)
