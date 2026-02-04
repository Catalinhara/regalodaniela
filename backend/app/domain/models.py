from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

# --- Value Objects ---

class CheckInIntent(str, Enum):
    RELEASE = "RELEASE"         # Venting
    TRACK = "TRACK"             # Neutral logging
    SEEK_CLARITY = "SEEK_CLARITY"
    SEEK_VALIDATION = "SEEK_VALIDATION"
    SEEK_DISTANCE = "SEEK_DISTANCE"

class MoodState(str, Enum):
    # Simplified mood set for MVP
    CALM = "CALM"
    ANXIOUS = "ANXIOUS"
    DRAINED = "DRAINED"
    ENERGIZED = "ENERGIZED"
    FRUSTRATED = "FRUSTRATED"
    CONTENT = "CONTENT"

class InsightType(str, Enum):
    PATTERN_RECOGNITION = "PATTERN_RECOGNITION"
    VALIDATION = "VALIDATION"
    GENTLE_SUGGESTION = "GENTLE_SUGGESTION"

# --- Entities ---

class CheckIn(BaseModel):
    """
    A distinct atomic event where the user logs data about a Context.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context
    context_type: str  # e.g., "PATIENT", "COLLEAGUE", "EVENT", "SELF"
    context_id: Optional[str] = None # ID of the specific entity (e.g. Patient ID)
    
    # Content
    intent: CheckInIntent
    mood_state: Optional[MoodState] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    text_content: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class Insight(BaseModel):
    """
    AI-generated reflection. strictly analytical/supportive.
    """
    id: UUID = Field(default_factory=uuid4)
    target_check_in_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    type: InsightType
    
    # Structure
    observation: str
    validation: str
    gentle_suggestion: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class CompanionContext(BaseModel):
    """
    Root Aggregate: The user's professional well-being state.
    """
    user_id: UUID
    
    # State
    current_mood: Optional[MoodState] = None
    current_energy: int = 5
    
    # Derived Signals (Non-Clinical)
    burnout_risk_score: float = Field(0.0, ge=0.0, le=1.0)
    last_check_in: Optional[datetime] = None
    
    # Progress
    streak_days: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessage(BaseModel):
    """
    Atomic message in a conversation.
    """
    id: UUID = Field(default_factory=uuid4)
    role: str # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)

class ChatConversation(BaseModel):
    """
    Longitudinal conversation container.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Recycled Context
    last_summary: Optional[str] = None
    extracted_themes: Optional[str] = None
    
    messages: List[ChatMessage] = []
    
    model_config = ConfigDict(from_attributes=True)
