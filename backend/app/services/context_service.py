from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.tables import PatientModel, EventModel, CheckInModel
from typing import Dict, Any

class ContextHydrator:
    """
    Utility service to gather all relevant clinical context for LLM consumption.
    Enforces the 'last 10 items' rule for history.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_global_context(self, user_id: UUID) -> Dict[str, Any]:
        """Gathers overall state: patients, events, and last 10 global check-ins."""
        # 1. Fetch Patients (Limited summary)
        p_stmt = select(PatientModel).where(PatientModel.user_id == user_id)
        p_res = await self.db.execute(p_stmt)
        patients = p_res.scalars().all()
        
        # 2. Fetch Events (Next 7 days or top 5)
        e_stmt = select(EventModel).where(EventModel.user_id == user_id).order_by(EventModel.event_date.asc()).limit(5)
        e_res = await self.db.execute(e_stmt)
        events = e_res.scalars().all()
        
        # 3. Last 10 Global Check-ins
        c_stmt = (
            select(CheckInModel)
            .where(CheckInModel.user_id == user_id)
            .order_by(CheckInModel.timestamp.desc())
            .limit(10)
        )
        c_res = await self.db.execute(c_stmt)
        check_ins = c_res.scalars().all()
        
        return {
            "patients": [{"alias": p.alias, "load": p.emotional_load, "trend": p.trend} for p in patients],
            "events": [{"title": e.title, "impact": e.impact_level, "date": e.event_date.isoformat()} for e in events],
            "recent_history": [
                {
                    "mood": c.mood_state, 
                    "energy": c.energy_level, 
                    "intent": c.intent, 
                    "note": c.text_content,
                    "type": c.context_type
                } for c in check_ins
            ]
        }

    async def get_entity_context(self, user_id: UUID, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Gathers focused context for one Patient or Colleague (last 10 check-ins)."""
        # 1. Fetch entity-specific check-ins
        stmt = (
            select(CheckInModel)
            .where(CheckInModel.user_id == user_id, CheckInModel.context_type == entity_type, CheckInModel.context_id == entity_id)
            .order_by(CheckInModel.timestamp.desc())
            .limit(10)
        )
        res = await self.db.execute(stmt)
        logs = res.scalars().all()
        
        return {
            "entity": {"type": entity_type, "id": entity_id},
            "history": [
                {"mood": l.mood_state, "energy": l.energy_level, "note": l.text_content, "date": l.timestamp.isoformat()} 
                for l in logs
            ]
        }
