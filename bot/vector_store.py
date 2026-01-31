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
        
        self._create_collection()
    
    def _create_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
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
