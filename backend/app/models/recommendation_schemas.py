from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class RelationshipCreate(BaseModel):
    target_id: str
    type: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)

class RecommendationBase(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []

class RecommendationCreate(RecommendationBase):
    relationships: Optional[List[RelationshipCreate]] = None
    metadata: Optional[Dict] = None

class RecommendationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    relationships: Optional[List[RelationshipCreate]] = None
    metadata: Optional[Dict] = None
    regenerate_embedding: bool = Field(default=False)

class RecommendationResponse(BaseModel):
    id: str
    status: str
    created_at: datetime = Field(default_factory=datetime.now)

class RecommendationSearchResult(BaseModel):
    id: str
    title: str
    category: str
    vector_score: float
    graph_score: float
    final_score: float
    metadata: Dict

class RecommendationCluster(BaseModel):
    id: str
    title: str
    similarity: float
    relationship_strength: float
    path: Optional[List[str]] = None

class FeedbackCreate(BaseModel):
    is_implemented: bool
    feedback: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    metadata: Optional[Dict] = None 