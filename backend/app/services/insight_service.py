import re
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.tables import CompanionContextModel, CheckInModel, InsightModel, UserModel
from app.services.llm import get_llm_provider
from app.domain.prompts import get_insight_prompts
from app.domain.models import InsightType

logger = logging.getLogger(__name__)

class InsightService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()

    async def generate_daily_insight(self, user_id: UUID, context_type: str = None, context_id: str = None, context_name: str = None) -> InsightModel:
        # 1. Fetch User (for profile & language)
        user_stmt = select(UserModel).where(UserModel.id == user_id)
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        if not user:
            logger.error(f"User {user_id} not found for insight generation")
            return None

        # 2. Fetch Context & Recent Check-Ins (Last 5 for context)
        stmt = select(CheckInModel).where(CheckInModel.user_id == user_id)
        
        if context_type and context_id:
            stmt = stmt.where(CheckInModel.context_type == context_type, CheckInModel.context_id == str(context_id))
            
        stmt = stmt.order_by(CheckInModel.timestamp.desc()).limit(5)
        
        result = await self.db.execute(stmt)
        check_ins = result.scalars().all()

        # --- Context Fetching (Entity awareness) ---
        from app.services.entity_service import EntityService
        entity_service = EntityService(self.db)
        
        active_context_summary = ""
        if not context_id:
            patients = await entity_service.list_patients(user_id)
            events = await entity_service.list_events(user_id)
            
            p_text = ", ".join([f"{p.alias} (Load: {p.emotional_load})" for p in patients[:5]])
            e_text = ", ".join([f"{e.title} (Impact: {e.impact_level})" for e in events[:3]])
            
            active_context_summary = f"""
            Profile Overview:
            - Active Patients: {len(patients)} ({p_text})
            - Upcoming Events: {len(events)} ({e_text})
            """

        if not check_ins and not active_context_summary:
            return None

        # 3. Construct Prompts
        check_in_text = "\n".join([
            f"- [{c.timestamp.strftime('%Y-%m-%d %H:%M')}] Intent: {c.intent}, Mood: {c.mood_state}, Energy: {c.energy_level}, Note: {c.text_content or ''}"
            for c in check_ins
        ])
        
        user_language = user.language or "en"
        prompts = get_insight_prompts(user_language)
        system_prompt_base = prompts["system"]

        # Professional Role Enrichment
        user_name = user.full_name.split(' ')[0] if user.full_name else "there"
        role_context = f"You are speaking with {user_name}, a {user.professional_role} with {user.years_experience} years of experience."
        if user_language == "es":
            role_context = f"Estás hablando con {user_name}, {user.professional_role} con {user.years_experience} años de experiencia."

        system_instructions = f"""{system_prompt_base}
        
        {role_context}
        Primary Stressor: {user.primary_stressor}
        Coping Style: {user.coping_style}

        Updated Objective:
        Provide a daily professional briefing.
        1. Acknowledge their current load (Active Patients/Events) as a {user.professional_role}.
        2. Validate any recent feelings (Check-Ins).
        3. Offer a STRATEGIC TIP for the day based on their {user.coping_style} style.
        Tone: Empathetic, Professional, Peer-to-Peer.
        """
        
        user_prompt = f"""
        Context: {context_name or 'General Global View'}
        {active_context_summary}

        Recent Check-Ins:
        {check_in_text}

        Generate a Daily Insight with:
        Observation: (State facts about load/mood)
        Validation: (Normalize the professional challenge)
        Suggestion: (One specific, actionable strategy for today)
        """

        # 4. Call LLM
        logger.info(f"Generating Daily Insight. System prompt length: {len(system_instructions)}. User prompt length: {len(user_prompt)}")
        
        response_text = await self.llm.generate(system_instructions, user_prompt)
        
        logger.info(f"Daily Insight AI Response received. Length: {len(response_text)}")
        logger.debug(f"AI RESPONSE CONTENT: {response_text}")

        # 4. Parse Response (Simple Regex/Splitting)
        # Expected format:
        # Observation: ...
        # Validation: ...
        # Suggestion: ...
        
        observation = "Analysis pending."
        validation = "You are doing your best."
        suggestion = None

        # 4. Parse Response (Resilient Regex)
        # Expected keys (case-insensitive, supports markdown bolding and variations)
        # English: Observation, Validation, Suggestion
        # Spanish: Observación, Validación, Sugerencia
        
        try:
            # Pattern Explanation:
            # (?:...) -> Non-capturing group for the prefix
            # \** ... \** -> Optional markdown bolding
            # [ÓóOoaá...] -> Support for accented and non-accented variants
            # \s*:\s* -> Colon with optional surrounding whitespace
            # (.*?) -> Capture the content until the next field or end of string
            
            obs_match = re.search(r'(?i)(?:\**Observaci[oó]n|\**Observation)\s*:\s*(.*?)(?=\n(?:\**Valid|Validaci[oó]n|Suggestion|Sugerencia)|$)', response_text, re.DOTALL)
            val_match = re.search(r'(?i)(?:\**Validaci[oó]n|\**Validation)\s*:\s*(.*?)(?=\n(?:\**Sug|Sugerencia|Suggestion)|$)', response_text, re.DOTALL)
            sug_match = re.search(r'(?i)(?:\**Sugerencia|\**Suggestion)\s*:\s*(.*)', response_text, re.DOTALL)

            if obs_match:
                observation = obs_match.group(1).strip()
            if val_match:
                validation = val_match.group(1).strip()
            if sug_match:
                suggestion = sug_match.group(1).strip()

            # Handle multi-line suggestion if it captured extra stuff
            if suggestion:
                # If there are headers in the suggestion match, try to clip it
                suggestion = suggestion.split('\n\n')[0] if '\n\n' in suggestion else suggestion
                suggestion = suggestion.strip()

        except Exception as e:
            logger.error(f"Error parsing LLM response with regex: {e}")
            observation = response_text # Fallback

        # 5. Save Insight
        target_id = check_ins[0].id if check_ins else None # Handle case where only Context exists but no check-ins
        
        insight = InsightModel(
            target_check_in_id=target_id, 
            type=InsightType.PATTERN_RECOGNITION.value,
            observation=observation,
            validation=validation,
            gentle_suggestion=suggestion
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)
        
        return insight
