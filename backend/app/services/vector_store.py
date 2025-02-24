from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from ..config.db_config import qdrant_settings
import numpy as np

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=qdrant_settings.url,
            api_key=qdrant_settings.api_key
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists with proper configuration"""
        try:
            self.client.get_collection(qdrant_settings.collection_name)
        except:
            # Create collection if it doesn't exist
            self.client.create_collection(
                collection_name=qdrant_settings.collection_name,
                vectors_config=models.VectorParams(
                    size=qdrant_settings.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    async def store_recommendation(
        self,
        recommendation_id: str,
        embedding: List[float],
        metadata: Dict
    ) -> bool:
        """Store a recommendation with its embedding"""
        try:
            self.client.upsert(
                collection_name=qdrant_settings.collection_name,
                points=[
                    models.PointStruct(
                        id=recommendation_id,
                        vector=embedding,
                        payload=metadata
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error storing recommendation: {e}")
            return False

    async def search_recommendations(
        self,
        query_vector: List[float],
        filter_params: Optional[Dict] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Search for similar recommendations"""
        try:
            search_params = models.SearchParams(hnsw_ef=128)
            if filter_params:
                filter_query = models.Filter(**filter_params)
            else:
                filter_query = None

            results = self.client.search(
                collection_name=qdrant_settings.collection_name,
                query_vector=query_vector,
                query_filter=filter_query,
                limit=limit,
                search_params=search_params
            )

            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "metadata": hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            print(f"Error searching recommendations: {e}")
            return []

    async def batch_store_recommendations(
        self,
        recommendations: List[Dict]
    ) -> bool:
        """Store multiple recommendations in batch"""
        try:
            points = [
                models.PointStruct(
                    id=rec["id"],
                    vector=rec["embedding"],
                    payload=rec["metadata"]
                )
                for rec in recommendations
            ]
            
            self.client.upsert(
                collection_name=qdrant_settings.collection_name,
                points=points
            )
            return True
        except Exception as e:
            print(f"Error batch storing recommendations: {e}")
            return False

    async def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation"""
        try:
            self.client.delete(
                collection_name=qdrant_settings.collection_name,
                points_selector=models.PointIdsList(
                    points=[recommendation_id]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting recommendation: {e}")
            return False

    async def update_metadata(
        self,
        recommendation_id: str,
        metadata: Dict
    ) -> bool:
        """Update recommendation metadata"""
        try:
            self.client.set_payload(
                collection_name=qdrant_settings.collection_name,
                payload=metadata,
                points=[recommendation_id]
            )
            return True
        except Exception as e:
            print(f"Error updating metadata: {e}")
            return False 