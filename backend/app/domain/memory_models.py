from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime

# Enums
FactCategory = Literal["preference", "biographical", "goal", "medical", "relational", "work"]
EmotionType = Literal["joy", "sadness", "anger", "fear", "anxiety", "neutral", "relief"]

class FactCreate(BaseModel):
    category: FactCategory
    value: str
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    source_message_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Fact(FactCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    last_reinforced_at: Optional[datetime] = None
    reinforcement_count: int = 0

class UserProfileTraits(BaseModel):
    communication_style: List[str] = Field(default_factory=list) # e.g. ["direct", "verbose"]
    emotional_patterns: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

class UserProfilePreferences(BaseModel):
    tone: str = "empathic"
    verbosity: str = "balanced" # concise, balanced, detailed
    emotional_sensitivity: float = 0.8 # 0.0 to 1.0

class EpisodicMemoryCreate(BaseModel):
    content: str
    summary: str
    vector_id: Optional[UUID] = None # ID in Qdrant
    emotions: List[EmotionType] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    context_type: Optional[str] = None # e.g. "session", "check_in"

class EpisodicMemory(EpisodicMemoryCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    decay_factor: float = 1.0
