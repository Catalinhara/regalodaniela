from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.api.dependencies import get_current_user
from app.domain.user import User
from app.services.analysis_service import AnalysisService
from app.services.memory_service import MemoryService
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/analysis", tags=["analysis"])

class InsightResponse(BaseModel):
    observation: str
    validation: str
    gentle_suggestion: str

@router.post("/daily-insight", response_model=Optional[InsightResponse])
async def get_daily_insight(
    language: str = "en",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a daily insight based on recent activity."""
    service = AnalysisService(db)
    insight = await service.generate_daily_insight(current_user.id, language)
    
    if not insight:
        return None
        
    return InsightResponse(
        observation=insight.observation,
        validation=insight.validation,
        gentle_suggestion=insight.gentle_suggestion
    )

@router.post("/process-memory/{conversation_id}")
async def trigger_memory_processing(
    conversation_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually triggers background memory processing for a conversation (Dev/Debug)."""
    service = MemoryService(db)
    
    # We run this in background
    async def _process():
        # Re-instantiate service/db in background task if needed or pass session carefully.
        # FastAPI background tasks with async session can be tricky if session closes.
        # For MVP sync/await here is safer or we use a fresh dependency injection pattern.
        # We'll stick to await for MVP to ensure completion.
        await service.process_conversation_background(conversation_id)
        
    background_tasks.add_task(_process)
    return {"status": "Processing started"}
