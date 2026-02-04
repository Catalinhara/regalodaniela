from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class User(BaseModel):
    """User domain model."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    language: str = "en"
    
    # Onboarding Profile Fields
    onboarding_completed: bool = False
    professional_role: Optional[str] = None
    years_experience: Optional[int] = None
    primary_stressor: Optional[str] = None
    coping_style: Optional[str] = None
    
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """DTO for user registration."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """DTO for user login."""
    email: EmailStr
    password: str


class UserGoogleLogin(BaseModel):
    """DTO for Google login."""
    credential: str


class Token(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal token payload structure."""
    user_id: UUID
    token_family: Optional[str] = None


class OnboardingData(BaseModel):
    """DTO for completing user onboarding."""
    language: str = Field(..., pattern="^(en|es)$")
    full_name: str = Field(..., min_length=1)
    professional_role: str = Field(..., min_length=1)
    years_experience: int = Field(..., ge=0)
    primary_stressor: str = Field(..., min_length=1)
    coping_style: str = Field(..., min_length=1)
