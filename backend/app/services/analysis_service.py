import logging
import json
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.infrastructure.tables import (
    UserModel, CheckInModel, InsightModel, 
    PatientModel, ColleagueModel, EventModel, EpisodicMemoryModel
)
from app.services.llm import get_llm_provider
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()
        self.memory = MemoryService(db)

    async def generate_daily_insight(self, user_id: UUID, language: str = "en") -> Optional[InsightModel]:
        """Generates a daily wisdom/insight based on recent activity and memories."""
        
        # 1. Fetch recent context (last 72h check-ins + recent memories)
        yesterday = datetime.utcnow() - timedelta(days=3)
        
        stmt_checkins = select(CheckInModel).where(
            CheckInModel.user_id == user_id,
            CheckInModel.timestamp >= yesterday
        ).order_by(CheckInModel.timestamp.desc())
        
        checkins_res = await self.db.execute(stmt_checkins)
        checkins = checkins_res.scalars().all()
        
        # Fetch generic recent memories (last 3 items created)
        stmt_memories = select(EpisodicMemoryModel).where(
            EpisodicMemoryModel.user_id == user_id
        ).order_by(EpisodicMemoryModel.created_at.desc()).limit(3)
        
        memories_res = await self.db.execute(stmt_memories)
        memories = memories_res.scalars().all()
        
        if not checkins and not memories:
            return None # Not enough data
            
        # 2. Prepare Data for LLM
        checkin_summaries = [f"- [{c.timestamp.strftime('%H:%M')}] {c.mood_state} ({c.energy_level}/10): {c.text_content}" for c in checkins]
        memory_summaries = [f"- Memory: {m.summary}" for m in memories]
        
        context_str = "\n".join(checkin_summaries + memory_summaries)
        
        # 3. Prompting (Localized)
        from app.domain.prompts import get_insight_prompts
        prompts = get_insight_prompts(language)
        
        system_prompt = prompts["system"]
        user_prompt = prompts["user"].format(history_text=context_str)
        
        try:
            response_json = await self.llm.generate(system_prompt, user_prompt)
            # Naive cleanup if LLM returns markdown blocks
            clean_json = response_json.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(clean_json)
            except json.JSONDecodeError:
                # Fallback: Try to find the first { and last }
                import re
                match = re.search(r"\{.*\}", clean_json, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(0))
                    except:
                         logger.error(f"Failed to parse inner JSON: {match.group(0)}")
                         raise
                else:
                    logger.error(f"No JSON object found in response: {clean_json}")
                    raise

            # 4. Save Insight
            insight = InsightModel(
                type="daily_daily", # differentiating from check-in specific
                observation=data.get("observation") or data.get("Observación", "No observation"), # Fallback for Spanish JSON keys if mixed
                validation=data.get("validation") or data.get("Validación", "Your dedication is visible."),
                gentle_suggestion=data.get("suggestion") or data.get("Sugerencia", "Take a moment to breathe."),
                created_at=datetime.utcnow()
            )
            
            if checkins:
                insight.target_check_in_id = checkins[0].id
                self.db.add(insight)
                await self.db.commit()
                return insight
            else:
                return insight
                
        except Exception as e:
            logger.error(f"Failed to generate insight: {e} | Raw Response: {response_json if 'response_json' in locals() else 'N/A'}")
            return None

    async def generate_analysis_response(self, user_id: UUID, entity_type: str, entity_id: str, message: str, history: List[Dict]) -> str:
        """
        Generates a specialist analysis response for a specific entity (Patient/Colleague/Event).
        Acting as a clinical supervisor or specialist consultant.
        """
        try:
            # 1. Fetch User (for profile & language)
            user_stmt = select(UserModel).where(UserModel.id == user_id)
            user_res = await self.db.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            language = user.language or "en"
            user_name = user.full_name.split(' ')[0] if user.full_name else "Colleague"
            professional_role = user.professional_role or "Mental Health Professional"
            years_experience = user.years_experience or 0

            # 2. Fetch Entity Details (Rich Context)
            entity_name = "Unknown"
            entity_context = ""
            
            # Normalize for matching
            entity_type_norm = entity_type.lower()
            
            if entity_type_norm == "patient":
                stmt = select(PatientModel).where(and_(PatientModel.id == UUID(entity_id), PatientModel.user_id == user_id))
                res = await self.db.execute(stmt)
                entity = res.scalar_one_or_none()
                if entity:
                    entity_name = entity.alias or "Patient"
                    entity_context = (
                        f"Patient Alias: {entity.alias}\n"
                        f"Age: {entity.age or 'N/A'}\n"
                        f"Emotional Load: {entity.emotional_load}/10\n"
                        f"Clinical Notes: {entity.notes or 'None'}\n"
                        f"Description/Summary: {entity.description or 'No description provided.'}\n"
                        f"Status Trend: {entity.trend or 'Stable'}"
                    )
            
            elif entity_type_norm == "colleague":
                stmt = select(ColleagueModel).where(and_(ColleagueModel.id == UUID(entity_id), ColleagueModel.user_id == user_id))
                res = await self.db.execute(stmt)
                entity = res.scalar_one_or_none()
                if entity:
                    entity_name = entity.name or "Colleague"
                    entity_context = (
                        f"Colleague Name: {entity.name}\n"
                        f"Relationship: {entity.relationship_type or 'Peer'}\n"
                        f"Context: High-stakes professional interaction."
                    )

            elif entity_type_norm == "event":
                stmt = select(EventModel).where(and_(EventModel.id == UUID(entity_id), EventModel.user_id == user_id))
                res = await self.db.execute(stmt)
                entity = res.scalar_one_or_none()
                if entity:
                    entity_name = entity.title or "Event"
                    entity_context = (
                        f"Event Title: {entity.title}\n"
                        f"Date: {entity.event_date.strftime('%Y-%m-%d %H:%M')}\n"
                        f"Impact Level: {entity.impact_level}/10\n"
                        f"Context: Significant upcoming or past professional occurrence."
                    )

            # 3. Guard: If no entity found, return a specific clinical error
            if entity_name == "Unknown":
                error_msg = {
                    "en": "I couldn't locate the clinical details for this specific case. Please check if the patient or event is properly registered.",
                    "es": "No he podido localizar los detalles clínicos de este caso específico. Por favor, verifica que el paciente o evento esté registrado correctamente."
                }
                return error_msg.get(language, error_msg["en"])

            # 3. Construct Prompts
            from app.domain.prompts import get_analysis_prompts
            prompts = get_analysis_prompts(language)
            
            # Format history for context (last 5 turns)
            history_str = ""
            if history:
                turns = []
                for m in history[-5:]:
                    role = "USER" if m['role'] == "user" else "COMPY"
                    turns.append(f"[{role}]: {m['content']}")
                history_str = "\n".join(turns)
            else:
                history_str = "(No recent chat history for this entity)"

            # System prompt only gets role-level data
            system_prompt = prompts["system"].format(
                user_name=user_name,
                professional_role=professional_role,
                years_experience=years_experience,
                entity_name=entity_name
            )
            
            # User prompt contains the heavy data for deep processing
            if language == "es":
                user_trigger = f"""
# DATOS DEL CASO PARA ANÁLISIS
{entity_context}

# CONTEXTO RECIENTE (HISTORIAL DE CHAT)
{history_str}

# SOLICITUD DEL PROFESIONAL
{message or "¿Qué patrones ves en este caso y cómo debería abordarlo?"}

Por favor, proporciona el ANÁLISIS CLÍNICO PROFUNDO para {entity_name} siguiendo tu rol de supervisora experta.
"""
            else:
                user_trigger = f"""
# CASE DATA FOR ANALYSIS
{entity_context}

# RECENT CONTEXT (CHAT HISTORY)
{history_str}

# PROFESSIONAL REQUEST
{message or "What patterns do you see in this case and how should I handle it?"}

Please provide the DEEP CLINICAL ANALYSIS for {entity_name} according to your specialized supervisor role.
"""

            # 4. Generate & Response
            response = await self.llm.generate(system_prompt, user_trigger)
            return response.strip()

        except Exception as e:
            logger.error(f"Error in generate_analysis_response: {e}", exc_info=True)
            return "I am unable to provide a consultation at this moment due to a system error."
