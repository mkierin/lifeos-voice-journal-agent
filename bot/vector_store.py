from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
from .config import QDRANT_HOST, QDRANT_PORT

class VectorStore:
    def __init__(self):
        if QDRANT_HOST == ":memory:":
            self.client = QdrantClient(":memory:")
            # Use a mock embedder for in-memory testing to avoid heavy downloads
            self.embedder = type('MockEmbedder', (), {
                'encode': lambda self, x: [0.1] * 384
            })()
        else:
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "journal"
        self.tasks_collection = "tasks"
        
        self._create_collection(self.collection_name)
        self._create_collection(self.tasks_collection)
    
    def _create_collection(self, name: str):
        """Create collection if it doesn't exist"""
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except:
            pass
    
    def add_entry(self, text: str, categories: list, user_id: int, metadata: dict = None):
        """Add journal entry to vector store"""
        res = self.embedder.encode(text)
        embedding = res.tolist() if hasattr(res, 'tolist') else res
        
        payload = {
            "text": text,
            "categories": categories,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        if metadata:
            payload.update(metadata)
        
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )
        
        return point_id

    def upsert_task(self, user_id: int, task_id: str, description: str, status: str = "open", goal_id: str = None, due_date: str = None, metadata: dict = None):
        """Add or update a task"""
        res = self.embedder.encode(description)
        embedding = res.tolist() if hasattr(res, 'tolist') else res
        
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
            
        self.client.upsert(
            collection_name=self.tasks_collection,
            points=[PointStruct(
                id=task_id,
                vector=embedding,
                payload=payload
            )]
        )
        return task_id

    def get_tasks(self, user_id: int, status: str = None, goal_id: str = None):
        """Get tasks for a user with optional filters"""
        must_filters = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        if status:
            must_filters.append(FieldCondition(key="status", match=MatchValue(value=status)))
        if goal_id:
            must_filters.append(FieldCondition(key="goal_id", match=MatchValue(value=goal_id)))
            
        results = self.client.scroll(
            collection_name=self.tasks_collection,
            scroll_filter=Filter(must=must_filters),
            with_payload=True,
            with_vectors=False
        )
        return results[0]
    
    def search(self, query: str, user_id: int, categories: list = None, limit: int = 5):
        """Search for relevant entries"""
        res = self.embedder.encode(query)
        query_embedding = res.tolist() if hasattr(res, 'tolist') else res
        
        # Build filter conditions for Qdrant using models
        must_filters = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        
        if categories:
            # Match any of the categories
            must_filters.append(FieldCondition(key="categories", match=MatchAny(any=categories)))
        
        # Use query_points if search is not available (common in newer qdrant-client versions for :memory:)
        if hasattr(self.client, "query_points"):
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                query_filter=Filter(must=must_filters)
            ).points
        else:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=Filter(must=must_filters)
            )
        
        return results
    
    def get_recent_entries(self, user_id: int, limit: int = 10):
        """Get recent entries for a user"""
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        return sorted(results[0], key=lambda x: x.payload["timestamp"], reverse=True)
