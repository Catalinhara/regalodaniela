from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.services.companion_service import CompanionService
from app.domain.models import CompanionContext, CheckIn, CheckInIntent, MoodState
from app.domain.user import User
from app.api.dependencies import get_current_user
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/companion", tags=["companion"])

# --- DTOs ---
class CheckInCreate(BaseModel):
    """Check-in creation DTO - user_id inferred from auth token."""
    context_type: str
    context_id: Optional[str] = None
    intent: CheckInIntent
    mood_state: Optional[MoodState] = None
    energy_level: Optional[int] = None
    text_content: Optional[str] = None


class InsightRequest(BaseModel):
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    context_name: Optional[str] = None
    language: Optional[str] = "en"


@router.get("/context", response_model=CompanionContext)
async def get_companion_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's companion context."""
    service = CompanionService(db)
    context = await service.get_or_create_context(current_user.id)
    return context


@router.post("/check-in", response_model=CheckIn)
async def submit_check_in(
    check_in_data: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a check-in for the authenticated user."""
    # Add user_id from authenticated user
    data = check_in_data.model_dump()
    data['user_id'] = current_user.id
    domain_check_in = CheckIn(**data)
    
    service = CompanionService(db)
    result = await service.record_check_in(domain_check_in)
    return result


@router.post("/generate-insight")
async def trigger_insight(
    request: InsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate insight for authenticated user. Now relies on user.language from DB."""
    from app.services.insight_service import InsightService
    service = InsightService(db)
    
    # Extract filters if provided
    c_type = request.context_type if request else None
    c_id = request.context_id if request else None
    c_name = request.context_name if request else None

    insight = await service.generate_daily_insight(
        current_user.id,
        context_type=c_type,
        context_id=c_id,
        context_name=c_name
    )
    if not insight:
        return {"message": "Not enough data for insight."}
    return insight


# --- Entity Management ---
from app.domain.entities import PatientCreate, Patient, ColleagueCreate, Colleague, EventCreate, Event
from app.services.entity_service import EntityService


@router.post("/patients", response_model=Patient)
async def create_patient(
    data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a patient for the authenticated user."""
    service = EntityService(db)
    return await service.create_patient(current_user.id, data)


@router.get("/patients", response_model=list[Patient])
async def list_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all patients for the authenticated user."""
    service = EntityService(db)
    return await service.list_patients(current_user.id)


@router.get("/patients/{patient_id}/history", response_model=list[CheckIn])
async def get_patient_history(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get check-in history for a specific patient."""
    service = EntityService(db)
    return await service.get_patient_history(current_user.id, patient_id)


@router.post("/colleagues", response_model=Colleague)
async def create_colleague(
    data: ColleagueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a colleague for the authenticated user."""
    service = EntityService(db)
    return await service.create_colleague(current_user.id, data)


@router.get("/colleagues", response_model=list[Colleague])
async def list_colleagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all colleagues for the authenticated user."""
    service = EntityService(db)
    return await service.list_colleagues(current_user.id)


@router.get("/colleagues/{colleague_id}/history", response_model=list[CheckIn])
async def get_colleague_history(
    colleague_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get check-in history for a specific colleague."""
    service = EntityService(db)
    return await service.get_colleague_history(current_user.id, colleague_id)


@router.post("/events", response_model=Event)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an event for the authenticated user."""
    service = EntityService(db)
    return await service.create_event(current_user.id, data)


@router.get("/events", response_model=list[Event])
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all events for the authenticated user."""
    service = EntityService(db)
    return await service.list_events(current_user.id)


# --- Chat ---
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


@router.post("/chat")
async def chat_interaction(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Chat interaction for authenticated user. Now relies on DB for language/profile."""
    from app.services.chat_service import ChatService
    service = ChatService(db)
    response = await service.generate_response(current_user.id, request.message)
    return {"role": "assistant", "content": response}


# --- Specialized Analysis Chat ---
class AnalysisChatRequest(BaseModel):
    context_type: str
    context_id: str
    message: str
    history: list[dict] = []
    language: Optional[str] = "en"


@router.post("/analysis/chat")
async def entity_analysis_chat(
    request: AnalysisChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stateless deep analysis for Patients/Colleagues. Now relies on user.language from DB."""
    from app.services.analysis_service import AnalysisService
    service = AnalysisService(db)
    response = await service.generate_analysis_response(
        user_id=current_user.id,
        entity_type=request.context_type,
        entity_id=request.context_id,
        message=request.message,
        history=request.history
    )
    return {"role": "assistant", "content": response}
