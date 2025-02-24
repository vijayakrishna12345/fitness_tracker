from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime

from ..services.recommendation_service import RecommendationService
from ..services.ingestion_service import IngestionService
from ..services.embedding_service import EmbeddingService
from ..models.schemas import (
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse,
    RelationshipCreate
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Service instances
recommendation_service = RecommendationService()
ingestion_service = IngestionService()
embedding_service = EmbeddingService()

@router.post("/", response_model=RecommendationResponse)
async def create_recommendation(recommendation: RecommendationCreate):
    """Create a new recommendation"""
    try:
        # Ingest the recommendation
        recommendation_id = await ingestion_service.ingest_recommendation(
            recommendation.dict(),
            recommendation.relationships
        )
        
        if not recommendation_id:
            raise HTTPException(
                status_code=400,
                detail="Failed to create recommendation"
            )
        
        return {"id": recommendation_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=List[str])
async def create_recommendations(recommendations: List[RecommendationCreate]):
    """Create multiple recommendations in batch"""
    try:
        recommendation_ids = await ingestion_service.ingest_recommendations(
            [rec.dict() for rec in recommendations]
        )
        
        if not recommendation_ids:
            raise HTTPException(
                status_code=400,
                detail="Failed to create recommendations"
            )
        
        return recommendation_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_recommendations(
    query: str,
    category: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20)
):
    """Search for recommendations"""
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Get recommendations
        results = await recommendation_service.get_recommendations(
            query_embedding=query_embedding,
            category=category,
            user_context={"query": query},
            limit=limit
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cluster/{recommendation_id}")
async def get_recommendation_cluster(
    recommendation_id: str,
    min_similarity: float = Query(0.7, ge=0, le=1),
    min_weight: float = Query(0.5, ge=0, le=1)
):
    """Get a cluster of related recommendations"""
    try:
        cluster = await recommendation_service.get_recommendation_cluster(
            recommendation_id,
            min_similarity=min_similarity,
            min_weight=min_weight
        )
        
        if not cluster:
            raise HTTPException(
                status_code=404,
                detail="No related recommendations found"
            )
        
        return cluster
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{recommendation_id}/relationships")
async def create_relationship(
    recommendation_id: str,
    relationship: RelationshipCreate
):
    """Create a relationship between recommendations"""
    try:
        success = await recommendation_service.create_relationship(
            source_id=recommendation_id,
            target_id=relationship.target_id,
            relationship_type=relationship.type,
            weight=relationship.weight
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to create relationship"
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{recommendation_id}/feedback")
async def provide_feedback(
    recommendation_id: str,
    is_implemented: bool,
    feedback: Optional[str] = None,
    user_id: str = "system"  # This should come from auth
):
    """Provide feedback for a recommendation"""
    try:
        success = await recommendation_service.update_recommendation_feedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            is_implemented=is_implemented,
            feedback=feedback
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update feedback"
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{recommendation_id}")
async def update_recommendation(
    recommendation_id: str,
    updates: RecommendationUpdate
):
    """Update a recommendation"""
    try:
        success = await ingestion_service.update_recommendation(
            recommendation_id=recommendation_id,
            updates=updates.dict(exclude_unset=True),
            regenerate_embedding=updates.regenerate_embedding
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update recommendation"
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{recommendation_id}")
async def delete_recommendation(recommendation_id: str):
    """Delete a recommendation"""
    try:
        success = await ingestion_service.delete_recommendation(recommendation_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to delete recommendation"
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 