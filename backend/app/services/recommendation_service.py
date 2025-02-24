from typing import List, Dict, Optional
from datetime import datetime
import uuid

from .vector_store import VectorStore
from .graph_store import GraphStore
from ..models.schemas import Recommendation

class RecommendationService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()

    async def close(self):
        """Close database connections"""
        await self.graph_store.close()

    async def create_recommendation(
        self,
        title: str,
        content: str,
        category: str,
        embedding: List[float],
        tags: List[str],
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Create a new recommendation in both stores"""
        try:
            recommendation_id = str(uuid.uuid4())
            
            # Store in vector database
            vector_metadata = {
                "title": title,
                "category": category,
                "tags": tags,
                **(metadata or {})
            }
            
            vector_success = await self.vector_store.store_recommendation(
                recommendation_id,
                embedding,
                vector_metadata
            )
            
            # Store in graph database
            graph_success = await self.graph_store.create_recommendation_node(
                recommendation_id,
                {
                    "title": title,
                    "category": category
                }
            )
            
            if vector_success and graph_success:
                return recommendation_id
            return None
        except Exception as e:
            print(f"Error creating recommendation: {e}")
            return None

    async def get_recommendations(
        self,
        query_embedding: List[float],
        category: str,
        user_context: Dict,
        limit: int = 5
    ) -> List[Dict]:
        """Get personalized recommendations using both vector and graph data"""
        try:
            # Get vector-based recommendations
            vector_results = await self.vector_store.search_recommendations(
                query_vector=query_embedding,
                filter_params={"category": category},
                limit=limit * 2  # Get more for combining
            )
            
            # Get graph-based recommendations for each vector result
            graph_results = []
            for result in vector_results[:limit]:
                related = await self.graph_store.get_related_recommendations(
                    result["id"],
                    limit=3
                )
                graph_results.extend(related)
            
            # Combine and rank results
            combined_results = self._combine_rankings(
                vector_results,
                graph_results,
                user_context
            )
            
            return combined_results[:limit]
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        weight: float = 1.0
    ) -> bool:
        """Create a relationship between recommendations"""
        try:
            return await self.graph_store.create_relationship(
                source_id,
                target_id,
                relationship_type,
                {"weight": weight}
            )
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False

    async def update_recommendation_feedback(
        self,
        recommendation_id: str,
        user_id: str,
        is_implemented: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """Update recommendation based on user feedback"""
        try:
            # Update metadata in vector store
            metadata_update = {
                "last_feedback": datetime.now().isoformat(),
                "implementation_count": 1,  # This should be incremented
                "user_feedback": feedback
            }
            
            vector_success = await self.vector_store.update_metadata(
                recommendation_id,
                metadata_update
            )
            
            # Update relationships in graph store
            if is_implemented:
                # Strengthen relationships for implemented recommendations
                related_recs = await self.graph_store.get_related_recommendations(
                    recommendation_id
                )
                for rec in related_recs:
                    await self.graph_store.update_relationship_weight(
                        recommendation_id,
                        rec["id"],
                        0.1  # Small positive reinforcement
                    )
            
            return vector_success
        except Exception as e:
            print(f"Error updating recommendation feedback: {e}")
            return False

    async def get_recommendation_cluster(
        self,
        recommendation_id: str,
        min_similarity: float = 0.7,
        min_weight: float = 0.5
    ) -> List[Dict]:
        """Get a cluster of related recommendations using both stores"""
        try:
            # Get the recommendation's embedding
            vector_result = await self.vector_store.search_recommendations(
                recommendation_id,
                limit=1
            )
            if not vector_result:
                return []
            
            # Get similar recommendations by vector
            similar_vector = await self.vector_store.search_recommendations(
                vector_result[0]["embedding"],
                limit=10
            )
            
            # Get related recommendations by graph
            graph_cluster = await self.graph_store.get_recommendation_cluster(
                recommendation_id,
                min_weight=min_weight
            )
            
            # Combine results
            return self._combine_rankings(
                similar_vector,
                graph_cluster,
                {"min_similarity": min_similarity}
            )
        except Exception as e:
            print(f"Error getting recommendation cluster: {e}")
            return []

    def _combine_rankings(
        self,
        vector_results: List[Dict],
        graph_results: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """Combine and rank results from both sources"""
        # Create a map of all results
        combined_map = {}
        
        # Process vector results
        for result in vector_results:
            combined_map[result["id"]] = {
                "id": result["id"],
                "title": result["metadata"]["title"],
                "vector_score": result["score"],
                "graph_score": 0.0,
                "metadata": result["metadata"]
            }
        
        # Process graph results
        for result in graph_results:
            if result["id"] in combined_map:
                combined_map[result["id"]]["graph_score"] = result.get("weight", 0)
            else:
                combined_map[result["id"]] = {
                    "id": result["id"],
                    "title": result["title"],
                    "vector_score": 0.0,
                    "graph_score": result.get("weight", 0),
                    "metadata": {}
                }
        
        # Calculate final scores
        results = list(combined_map.values())
        for result in results:
            result["final_score"] = (
                result["vector_score"] * 0.7 +  # Vector similarity weight
                result["graph_score"] * 0.3     # Graph relationship weight
            )
        
        # Sort by final score
        return sorted(results, key=lambda x: x["final_score"], reverse=True) 