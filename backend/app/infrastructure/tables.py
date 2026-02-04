from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Float, Text, Boolean, and_
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, foreign
import uuid
from datetime import datetime
from app.infrastructure.database import Base


class UserModel(Base):
    """User account table."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    language = Column(String, default="en", nullable=False)
    
    # Onboarding Profile Fields
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    professional_role = Column(String, nullable=True)  # Therapist, Psychologist, etc.
    years_experience = Column(Integer, nullable=True)  # Stored as mid-range value (1, 4, 8, 15, 25)
    primary_stressor = Column(String, nullable=True)  # burnout, workload, etc.
    coping_style = Column(String, nullable=True)  # analytical, reflective, relational, action_oriented
    
    # Memory Profile Fields (New)
    preferences = Column(JSONB, nullable=True) # {tone, verbosity, sensitivity}
    traits = Column(JSONB, nullable=True) # {communication_style, emotional_patterns}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # OAuth Fields
    google_id = Column(String, unique=True, nullable=True)
    auth_provider = Column(String, default="email", nullable=False) # 'email' or 'google'
    
    # Relationships
    companion_context = relationship("CompanionContextModel", back_populates="user", uselist=False)
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")
    check_ins = relationship("CheckInModel", back_populates="user")
    patients = relationship("PatientModel", back_populates="user")
    colleagues = relationship("ColleagueModel", back_populates="user")
    events = relationship("EventModel", back_populates="user")
    conversations = relationship("ChatConversationModel", back_populates="user", cascade="all, delete-orphan")
    facts = relationship("FactModel", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("EpisodicMemoryModel", back_populates="user", cascade="all, delete-orphan")


class RefreshTokenModel(Base):
    """Refresh token tracking for token rotation and theft detection."""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_family = Column(String, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="refresh_tokens")


class CompanionContextModel(Base):
    """User's professional well-being state."""
    __tablename__ = "companion_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_mood = Column(String, nullable=True)
    current_energy = Column(Integer, default=5)
    burnout_risk_score = Column(Float, default=0.0)
    last_check_in = Column(DateTime, nullable=True)
    streak_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="companion_context")
    check_ins = relationship(
        "CheckInModel", 
        back_populates="context",
        primaryjoin="and_(CompanionContextModel.user_id == foreign(CheckInModel.user_id))",
        viewonly=True
    )


class CheckInModel(Base):
    """Atomic event where user logs data about a context."""
    __tablename__ = "check_ins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    context_type = Column(String, nullable=False) # PATIENT, COLLEAGUE, etc
    context_id = Column(String, nullable=True)
    
    intent = Column(String, nullable=False)
    mood_state = Column(String, nullable=True)
    energy_level = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="check_ins")
    # CompanionContext relationship through user_id
    context = relationship(
        "CompanionContextModel",
        back_populates="check_ins",
        foreign_keys=[user_id],
        primaryjoin="and_(foreign(CheckInModel.user_id) == CompanionContextModel.user_id)",
        viewonly=True,
        uselist=False
    )


class InsightModel(Base):
    """AI-generated reflection."""
    __tablename__ = "insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_check_in_id = Column(UUID(as_uuid=True), ForeignKey("check_ins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    type = Column(String, nullable=False)
    observation = Column(Text, nullable=False)
    validation = Column(Text, nullable=False)
    gentle_suggestion = Column(Text, nullable=True)


class PatientModel(Base):
    """Patient entity for healthcare professionals."""
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String, nullable=False) # e.g. "P-101"
    emotional_load = Column(Integer, default=5) # 1-10 drain factor
    
    # Enhanced patient information
    age = Column(Integer, nullable=True)
    avatar_url = Column(String, nullable=True)  # URL, emoji, or None
    avatar_type = Column(String, default='initials')  # 'photo', 'emoji', 'initials'
    description = Column(Text, nullable=True)
    therapy_start_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    trend = Column(String, nullable=True) # 'improving', 'stable', 'declining'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="patients")


class ColleagueModel(Base):
    """Colleague entity for professional relationships."""
    __tablename__ = "colleagues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    relationship_type = Column(String, nullable=False) # Peer, Mentor, Supervisee
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="colleagues")


class EventModel(Base):
    """Event entity for tracking significant occurrences."""
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    impact_level = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="events")

class ChatConversationModel(Base):
    """Container for persistent chat history."""
    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Context Recycling Fields
    last_summary = Column(Text, nullable=True)
    extracted_themes = Column(Text, nullable=True) # JSON or Comma-separated
    
    # Relationships
    user = relationship("UserModel", back_populates="conversations")
    messages = relationship("ChatMessageModel", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessageModel.timestamp")


class ChatMessageModel(Base):
    """Atomic message in a conversation."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("ChatConversationModel", back_populates="messages")


class FactModel(Base):
    """Structured fact about the user."""
    __tablename__ = "facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    category = Column(String, nullable=False) # preference, biographical, goal, etc.
    value = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    
    source_message_id = Column(UUID(as_uuid=True), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True) # avoiding reserved word clash if any, mapped to 'metadata'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reinforced_at = Column(DateTime, nullable=True)
    reinforcement_count = Column(Integer, default=0)

    # Relationships
    user = relationship("UserModel", back_populates="facts")


class EpisodicMemoryModel(Base):
    """Metadata for vector-stored episodic memories."""
    __tablename__ = "episodic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    vector_id = Column(UUID(as_uuid=True), nullable=True) # ID in Qdrant
    
    emotions = Column(JSONB, nullable=True) # List of strings
    topics = Column(JSONB, nullable=True) # List of strings
    
    importance_score = Column(Float, default=0.5)
    context_type = Column(String, nullable=True)
    decay_factor = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="memories")
