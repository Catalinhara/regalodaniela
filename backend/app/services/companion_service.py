from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.tables import CompanionContextModel, CheckInModel
from app.domain.models import CheckInIntent, MoodState, CheckIn as CheckInSchema
from datetime import datetime

class CompanionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_context(self, user_id: UUID) -> CompanionContextModel:
        """
        Retrieves the user's longitudinal context or creates a fresh one.
        """
        stmt = select(CompanionContextModel).where(CompanionContextModel.user_id == user_id)
        result = await self.db.execute(stmt)
        context = result.scalar_one_or_none()
        
        if not context:
            context = CompanionContextModel(user_id=user_id)
            self.db.add(context)
            await self.db.commit()
            await self.db.refresh(context)
            
        return context

    async def record_check_in(self, check_in_data: CheckInSchema) -> CheckInModel:
        """
        Records a check-in and updates the context (simple logic for now).
        """
        # 1. Save Check-In
        db_check_in = CheckInModel(
            user_id=check_in_data.user_id,
            timestamp=check_in_data.timestamp,
            context_type=check_in_data.context_type,
            context_id=check_in_data.context_id,
            intent=check_in_data.intent.value,
            mood_state=check_in_data.mood_state.value if check_in_data.mood_state else None,
            energy_level=check_in_data.energy_level,
            text_content=check_in_data.text_content
        )
        self.db.add(db_check_in)
        
        # 2. Update Context (Simple Logic for MVP)
        # In a real system, this would be more complex or async
        context = await self.get_or_create_context(check_in_data.user_id)
        
        if check_in_data.energy_level:
            # Simple moving average or just set current? Let's just set current for now.
            context.current_energy = check_in_data.energy_level
            
        if check_in_data.mood_state:
            context.current_mood = check_in_data.mood_state.value
            
        context.last_check_in = check_in_data.timestamp
        # Naive streak logic placeholder
        # context.streak_days += 1 
        
        await self.db.commit()
        await self.db.refresh(db_check_in)
        return db_check_in
