import logging
import json
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.tables import ChatConversationModel, ChatMessageModel
from app.services.llm import get_llm_provider
from app.services.memory_service import MemoryService
from app.services.entity_service import EntityService
from app.domain.prompts import get_chat_system_prompt

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()
        self.memory_service = MemoryService(db)
        self.entity_service = EntityService(db)

    async def get_or_create_conversation(self, user_id: UUID) -> ChatConversationModel:
        """Retrieves the active persistent conversation or creates one."""
        stmt = select(ChatConversationModel).where(ChatConversationModel.user_id == user_id).order_by(ChatConversationModel.updated_at.desc())
        res = await self.db.execute(stmt)
        conv = res.scalars().first()
        
        if not conv:
            conv = ChatConversationModel(user_id=user_id, title="Main Companion")
            self.db.add(conv)
            await self.db.commit()
            await self.db.refresh(conv)
        return conv

    async def generate_response(self, user_id: UUID, message: str) -> str:
        try:
            # 1. Fetch User (for profile & language)
            from app.infrastructure.tables import UserModel
            user_stmt = select(UserModel).where(UserModel.id == user_id)
            user_res = await self.db.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {user_id} not found")

            # 1b. Get/Create Conversation (Moved up to fix UnboundLocalError)
            conv = await self.get_or_create_conversation(user_id)

            # 2. Parallel Context Assembly
            # A) Get STM (Short Term Memory)
            stm_context = await self.memory_service.get_stm_context(user_id)
            
            # B) Get Relevant LTM (Facts) - Top 5 generic facts for now
            relevant_facts = await self.memory_service.get_relevant_facts(user_id)
            facts_str = "\n".join([f"- [{f.category}] {f.value}" for f in relevant_facts[:5]])
            
            # C) Get Episodic Recall (Vector Search)
            embedding = await self.llm.get_embedding(message)
            memories = await self.memory_service.search_memories(user_id, embedding, limit=3)
            memories_str = "\n".join([f"- {m.summary} (Importance: {m.importance_score})" for m in memories])

            # D) Get Clinical Context (Patients & Events)
            patients = await self.entity_service.list_patients(user_id)
            events = await self.entity_service.list_events(user_id)
            
            patients_data = [{"alias": p.alias, "load": p.emotional_load, "notes": p.notes} for p in patients]
            events_data = [{"title": e.title, "date": e.event_date.isoformat(), "impact": e.impact_level} for e in events]

            # 3. Formulate Prompt
            language = user.language or "en"
            
            # Extract basic user info
            user_name = user.full_name.split(' ')[0] if user.full_name else "there"
            
            # Format JSON-like structures for the prompt slots
            # We use json.dumps for clean string representation of lists/dicts
            current_role = user.professional_role or "Unknown Role"
            stressor = user.primary_stressor or "Unknown Stressor"
            years_exp = str(user.years_experience or 0)
            coping = user.coping_style or "Unknown"

            # Format STM (Short Term Memory) into a string with freshness check
            chat_history_str = ""
            is_fresh_session = True
            
            if stm_context:
                # 1. Check if the last interaction was recent (e.g., within 30 minutes)
                last_msg = stm_context[-1]
                last_ts = datetime.fromisoformat(last_msg["timestamp"])
                time_gap = datetime.utcnow() - last_ts
                
                if time_gap.total_seconds() < 1800: # 30 minutes
                    is_fresh_session = False
                
                formatted_turns = []
                for turn in stm_context:
                    role_label = "PROFESIONAL" if turn["role"] == "user" else "COMPY"
                    formatted_turns.append(f"[{role_label}]: {turn['content']}")
                chat_history_str = "\n".join(formatted_turns)
            else:
                chat_history_str = "(No previous history)"

            # If it's a fresh session, we want the AI to greet first or acknowledge it's been a while
            session_instruction = ""
            if is_fresh_session and chat_history_str != "(No previous history)":
                session_instruction = "\n[SYSTEM NOTE]: Some time has passed. Briefly acknowledge the gap without a full greeting if the conversation is ongoing."
            elif is_fresh_session:
                 session_instruction = "\n[SYSTEM NOTE]: Brand new session. Greet the user by name exactly as requested."

            # Prepare data for prompt slots
            prompt_data = {
                "today_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "user_name": user_name,
                "professional_role": current_role,
                "years_experience": years_exp,
                "primary_stressor": stressor,
                "coping_style": coping,
                "last_summary": "No previous summary available." if not conv.last_summary else conv.last_summary,
                "chat_history": chat_history_str,
                "patients_json": json.dumps(patients_data, ensure_ascii=False), 
                "events_json": json.dumps(events_data, ensure_ascii=False),
                "recent_logs_json": f"<professional_personal_memory>\n{facts_str}\n{memories_str}\n</professional_personal_memory>"
            }
            
            # Get template and format it
            info_system_prompt = get_chat_system_prompt(language)
            
            # Add session-specific guidance
            info_system_prompt += session_instruction
            
            # Safe formatting to ignore missing keys if template changes
            try:
                system_prompt = info_system_prompt.format(**prompt_data)
            except KeyError as e:
                # Fallback if template has keys we didn't provide
                logger.warning(f"Missing key in prompt template: {e}")
                system_prompt = info_system_prompt.replace("{", "{{").replace("}", "}}") # Degrade to raw string if fail
            
            full_user_prompt = message
            if message == "START_SESSION":
                greet_msg = f"Hola {user_name}, soy Compy, ¿sobre qué tienes ganas de hablar hoy?" if language == "es" else f"Hi {user_name}, I'm Compy, what do you feel like talking about today?"
                full_user_prompt = f"(Start the conversation by saying exactly this or very similar: '{greet_msg}')"
            
            # 4. Generate & Save
            logger.info(f"Generating AI response for {user_id}")
            response_text = await self.llm.generate(system_prompt, full_user_prompt)
            
            # 5. Persist to STM (Redis) - ONLY if it's a real user message
            if message != "START_SESSION":
                await self.memory_service.append_stm_message(user_id, "user", message)
                await self.memory_service.append_stm_message(user_id, "assistant", response_text)
                
                # 6. Persist to DB (for audit/long term history)
                user_msg = ChatMessageModel(conversation_id=conv.id, role="user", content=message)
                assistant_msg = ChatMessageModel(conversation_id=conv.id, role="assistant", content=response_text.strip())
                
                self.db.add(user_msg)
                self.db.add(assistant_msg)
                conv.updated_at = datetime.utcnow()
                await self.db.commit()
            
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"ERROR in ChatService: {e}", exc_info=True)
            return "I apologize, but I'm having trouble connecting to my memory banks right now. Please try again in a moment."
