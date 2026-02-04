from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, Literal

class PatientCreate(BaseModel):
    alias: str
    emotional_load: int = Field(5, ge=1, le=10)
    age: Optional[int] = None
    avatar_url: Optional[str] = None  # Can be URL, emoji, or None
    avatar_type: Literal['photo', 'emoji', 'initials'] = 'initials'
    description: Optional[str] = None
    therapy_start_date: Optional[date] = None
    notes: Optional[str] = None

class Patient(PatientCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    trend: Optional[str] = None # 'improving', 'stable', 'declining'

class ColleagueCreate(BaseModel):
    name: str
    relationship_type: str

class Colleague(ColleagueCreate):
    id: UUID
    user_id: UUID
    created_at: datetime

class EventCreate(BaseModel):
    title: str
    event_date: datetime
    impact_level: int = Field(5, ge=1, le=10)

class Event(EventCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
