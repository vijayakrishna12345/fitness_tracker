from typing import List, Dict, Optional
import asyncio
from datetime import datetime

from .embedding_service import EmbeddingService
from .vector_store import VectorStore
from .graph_store import GraphStore

class IngestionService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()

    async def ingest_recommendations(
        self,
        recommendations: List[Dict]
    ) -> List[str]:
        """
        Ingest multiple recommendations with their relationships
        Returns list of successfully ingested recommendation IDs
        """
        try:
            # Generate embeddings for all recommendations
            texts = [
                self.embedding_service.combine_text_fields(rec)
                for rec in recommendations
            ]
            embeddings = await self.embedding_service.generate_batch_embeddings(texts)
            
            # Prepare recommendations with embeddings
            enriched_recommendations = []
            for rec, embedding in zip(recommendations, embeddings):
                rec_with_embedding = {
                    "id": rec.get("id"),
                    "embedding": embedding,
                    "metadata": {
                        "title": rec.get("title"),
                        "category": rec.get("category"),
                        "tags": rec.get("tags", []),
                        "created_at": datetime.now().isoformat()
                    }
                }
                enriched_recommendations.append(rec_with_embedding)
            
            # Store in vector database
            vector_success = await self.vector_store.batch_store_recommendations(
                enriched_recommendations
            )
            
            if not vector_success:
                raise Exception("Failed to store recommendations in vector database")
            
            # Store in graph database and create relationships
            successful_ids = []
            for rec in recommendations:
                # Create node
                node_success = await self.graph_store.create_recommendation_node(
                    rec["id"],
                    {
                        "title": rec["title"],
                        "category": rec["category"]
                    }
                )
                
                if node_success:
                    successful_ids.append(rec["id"])
                    
                    # Create relationships if specified
                    if "relationships" in rec:
                        for rel in rec["relationships"]:
                            await self.graph_store.create_relationship(
                                rec["id"],
                                rel["target_id"],
                                rel["type"],
                                {"weight": rel.get("weight", 1.0)}
                            )
            
            return successful_ids
        except Exception as e:
            print(f"Error in batch ingestion: {e}")
            return []

    async def ingest_recommendation(
        self,
        recommendation: Dict,
        relationships: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """
        Ingest a single recommendation with optional relationships
        """
        try:
            # Generate embedding
            text = self.embedding_service.combine_text_fields(recommendation)
            embedding = await self.embedding_service.generate_embedding(text)
            
            # Store in vector database
            vector_success = await self.vector_store.store_recommendation(
                recommendation["id"],
                embedding,
                {
                    "title": recommendation["title"],
                    "category": recommendation["category"],
                    "tags": recommendation.get("tags", []),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if not vector_success:
                raise Exception("Failed to store recommendation in vector database")
            
            # Store in graph database
            graph_success = await self.graph_store.create_recommendation_node(
                recommendation["id"],
                {
                    "title": recommendation["title"],
                    "category": recommendation["category"]
                }
            )
            
            if not graph_success:
                # Rollback vector store
                await self.vector_store.delete_recommendation(recommendation["id"])
                raise Exception("Failed to store recommendation in graph database")
            
            # Create relationships if provided
            if relationships:
                for rel in relationships:
                    await self.graph_store.create_relationship(
                        recommendation["id"],
                        rel["target_id"],
                        rel["type"],
                        {"weight": rel.get("weight", 1.0)}
                    )
            
            return recommendation["id"]
        except Exception as e:
            print(f"Error ingesting recommendation: {e}")
            return None

    async def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation from both stores"""
        try:
            vector_success = await self.vector_store.delete_recommendation(
                recommendation_id
            )
            graph_success = await self.graph_store.delete_recommendation(
                recommendation_id
            )
            return vector_success and graph_success
        except Exception as e:
            print(f"Error deleting recommendation: {e}")
            return False

    async def update_recommendation(
        self,
        recommendation_id: str,
        updates: Dict,
        regenerate_embedding: bool = False
    ) -> bool:
        """Update a recommendation in both stores"""
        try:
            metadata_updates = {}
            graph_updates = {}
            
            # Update basic fields
            if "title" in updates:
                metadata_updates["title"] = updates["title"]
                graph_updates["title"] = updates["title"]
            if "category" in updates:
                metadata_updates["category"] = updates["category"]
                graph_updates["category"] = updates["category"]
            if "tags" in updates:
                metadata_updates["tags"] = updates["tags"]
            
            # Update embedding if requested
            if regenerate_embedding and ("title" in updates or "content" in updates):
                text = self.embedding_service.combine_text_fields(updates)
                embedding = await self.embedding_service.generate_embedding(text)
                
                await self.vector_store.store_recommendation(
                    recommendation_id,
                    embedding,
                    metadata_updates
                )
            else:
                await self.vector_store.update_metadata(
                    recommendation_id,
                    metadata_updates
                )
            
            # Update relationships if provided
            if "relationships" in updates:
                for rel in updates["relationships"]:
                    await self.graph_store.create_relationship(
                        recommendation_id,
                        rel["target_id"],
                        rel["type"],
                        {"weight": rel.get("weight", 1.0)}
                    )
            
            return True
        except Exception as e:
            print(f"Error updating recommendation: {e}")
            return False 