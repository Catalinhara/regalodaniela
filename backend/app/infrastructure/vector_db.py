import logging
import os
from typing import List, Optional, Dict, Any
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        # self.api_key = os.getenv("QDRANT_API_KEY", None) # For cloud
        
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None

    def ensure_collection(self, collection_name: str, vector_size: int = 1536):
        """Creates collection if it doesn't exist."""
        if not self.client:
            return

        try:
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
            else:
                logger.debug(f"Collection {collection_name} already exists.")
        except Exception as e:
            logger.error(f"Error ensuring collection {collection_name}: {e}")

    def upsert_vectors(self, collection_name: str, points: List[models.PointStruct]):
        if not self.client:
            return
        
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.debug(f"Upserted {len(points)} vectors to {collection_name}")
        except Exception as e:
            logger.error(f"Error upserting to {collection_name}: {e}")

    def search(self, collection_name: str, vector: List[float], limit: int = 5, score_threshold: float = 0.7, filter_conditions: Optional[Dict] = None) -> List[models.ScoredPoint]:
        if not self.client:
            return []
            
        try:
            search_filter = None
            if filter_conditions:
                # Convert simple dict to Filter
                # Note: This is a simplified filter builder. For complex queries adapt as needed.
                must_conditions = []
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                search_filter = models.Filter(must=must_conditions)

            # Use query_points instead of search (API change)
            results = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            ).points
            return results
        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}")
            return []
            
    def delete_vector(self, collection_name: str, point_id: str):
        if not self.client:
            return
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[point_id]),
            )
        except Exception as e:
            logger.error(f"Error deleting vector {point_id} from {collection_name}: {e}")

# Global instance
vector_db = VectorDB()
