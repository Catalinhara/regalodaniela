from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.infrastructure.tables import PatientModel, ColleagueModel, EventModel, CompanionContextModel, CheckInModel
from app.domain.entities import PatientCreate, ColleagueCreate, EventCreate

class EntityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_context_exists(self, user_id: UUID):
         stmt = select(CompanionContextModel).where(CompanionContextModel.user_id == user_id)
         result = await self.db.execute(stmt)
         if not result.scalar():
             # Create stub context if missing
             try:
                 self.db.add(CompanionContextModel(user_id=user_id))
                 await self.db.commit()
             except Exception:
                 # Race condition or error? Rollback just in case.
                 await self.db.rollback()

    # --- Patients ---
    async def _calculate_dynamic_load(self, user_id: UUID, patient_id: UUID, current_static_load: int) -> tuple[int, str]:
        from app.infrastructure.tables import CheckInModel
        from sqlalchemy import desc
        
        # Fetch last 7 check-ins for this specific patient
        stmt = (
            select(CheckInModel)
            .where(CheckInModel.user_id == user_id)
            .where(CheckInModel.context_type == "PATIENT")
            .where(CheckInModel.context_id == str(patient_id))
            .order_by(desc(CheckInModel.timestamp))
            .limit(7)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        
        if not logs:
            return current_static_load, "stable"

        total_score = 0
        mood_weights = {
            "CALM": 2,
            "CONTENT": 3,
            "ENERGIZED": 1,
            "ANXIOUS": 8,
            "FRUSTRATED": 9,
            "DRAINED": 10
        }
        
        for log in logs:
            base_weight = mood_weights.get(log.mood_state, 5)
            energy = log.energy_level or 5
            
            # For positive moods, high energy reduces load
            if log.mood_state in ["CALM", "CONTENT", "ENERGIZED"]:
                adjustment = (energy / 5) # 1-10 -> 0.2 - 2.0
                total_score += max(1, base_weight - adjustment)
            else:
                # For negative moods, high energy increases load (more intense distress)
                adjustment = (energy / 5)
                total_score += min(10, base_weight + adjustment)
        
        # Calculate trend: Compare avg of last 3 vs prev 4
        if len(logs) >= 4:
            recent_avg = sum(mood_weights.get(l.mood_state, 5) for l in logs[:3]) / 3
            prev_avg = sum(mood_weights.get(l.mood_state, 5) for l in logs[3:]) / (len(logs)-3)
            
            if recent_avg < prev_avg - 0.5: trend = "improving"
            elif recent_avg > prev_avg + 0.5: trend = "declining"
            else: trend = "stable"
        else:
            trend = "stable"

        return int(round(total_score / len(logs))), trend

    async def create_patient(self, user_id: UUID, data: PatientCreate) -> PatientModel:
        await self.ensure_context_exists(user_id)
        patient = PatientModel(user_id=user_id, **data.model_dump())
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def get_patient_history(self, user_id: UUID, patient_id: UUID) -> List[CheckInModel]:
        stmt = (
            select(CheckInModel)
            .where(CheckInModel.user_id == user_id)
            .where(CheckInModel.context_type == "PATIENT")
            .where(CheckInModel.context_id == str(patient_id))
            .order_by(desc(CheckInModel.timestamp))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_patients(self, user_id: UUID) -> List[PatientModel]:
        result = await self.db.execute(select(PatientModel).where(PatientModel.user_id == user_id))
        patients = result.scalars().all()
        
        # Hydrate with dynamic load and trend
        for p in patients:
            load, trend = await self._calculate_dynamic_load(user_id, p.id, p.emotional_load)
            p.emotional_load = load
            p.trend = trend # Note: This requires adding 'trend' to the SQLAlchemy model or handling it in a DTO
            
        return patients

    # --- Colleagues ---
    async def create_colleague(self, user_id: UUID, data: ColleagueCreate) -> ColleagueModel:
        await self.ensure_context_exists(user_id)
        col = ColleagueModel(user_id=user_id, **data.model_dump())
        self.db.add(col)
        await self.db.commit()
        await self.db.refresh(col)
        return col

    async def list_colleagues(self, user_id: UUID) -> List[ColleagueModel]:
        result = await self.db.execute(select(ColleagueModel).where(ColleagueModel.user_id == user_id))
        return result.scalars().all()

    async def get_colleague_history(self, user_id: UUID, colleague_id: UUID) -> List[CheckInModel]:
        stmt = (
            select(CheckInModel)
            .where(CheckInModel.user_id == user_id)
            .where(CheckInModel.context_type == "COLLEAGUE")
            .where(CheckInModel.context_id == str(colleague_id))
            .order_by(desc(CheckInModel.timestamp))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


    # --- Events ---
    async def create_event(self, user_id: UUID, data: EventCreate) -> EventModel:
        await self.ensure_context_exists(user_id)
        # SQLAlchemy/AsyncPG often struggle with TZ-aware datetimes in Naive columns.
        # Ensure date is naive UTC.
        naive_date = data.event_date.replace(tzinfo=None) if data.event_date.tzinfo else data.event_date
        
        event = EventModel(
            user_id=user_id, 
            title=data.title,
            event_date=naive_date,
            impact_level=data.impact_level
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def list_events(self, user_id: UUID) -> List[EventModel]:
        result = await self.db.execute(select(EventModel).where(EventModel.user_id == user_id).order_by(EventModel.event_date))
        return result.scalars().all()
