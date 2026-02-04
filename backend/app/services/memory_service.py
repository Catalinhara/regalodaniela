import logging
import json
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.infrastructure.tables import FactModel, EpisodicMemoryModel, UserModel
from app.infrastructure.cache import redis_client
from app.infrastructure.vector_db import vector_db
from app.domain.memory_models import FactCreate, EpisodicMemoryCreate

logger = logging.getLogger(__name__)

STM_TTL = 3600 * 4 # 4 hours for short term context

class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Short Term Memory (STM) ---
    async def get_stm_context(self, user_id: UUID) -> List[Dict]:
        """Retrieves recent conversation window from Redis."""
        key = f"stm:{user_id}"
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis unavailable for STM get: {e}")
        return []

    async def append_stm_message(self, user_id: UUID, role: str, content: str):
        """Appends a message to the sliding window STM."""
        try:
            key = f"stm:{user_id}"
            current = await self.get_stm_context(user_id)
            
            current.append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep last 20 messages only
            if len(current) > 20:
                current = current[-20:]
                
            await redis_client.set(key, json.dumps(current), expire=STM_TTL)
        except Exception as e:
            logger.warning(f"Redis unavailable for STM set: {e}")

    # --- Long Term Memory (Facts) ---
    async def add_fact(self, user_id: UUID, fact_data: FactCreate) -> FactModel:
        """Adds a structured fact, checking for duplicates/updates first."""
        # Simple duplicate check logic: Same category and similar value (exact match for MVP)
        # In a real system, you'd use semantic similarity or more complex dedupe
        stmt = select(FactModel).where(
            FactModel.user_id == user_id,
            FactModel.category == fact_data.category,
            FactModel.value == fact_data.value
        )
        existing = await self.db.execute(stmt)
        fact = existing.scalar_one_or_none()
        
        if fact:
            # Reinforce existing fact
            fact.reinforcement_count += 1
            fact.last_reinforced_at = datetime.utcnow()
            fact.metadata_ = fact_data.metadata # Update metadata
            await self.db.commit()
            await self.db.refresh(fact)
            return fact
        
        # Create new
        new_fact = FactModel(
            user_id=user_id,
            category=fact_data.category,
            value=fact_data.value,
            confidence_score=fact_data.confidence_score,
            source_message_id=fact_data.source_message_id,
            metadata_=fact_data.metadata
        )
        self.db.add(new_fact)
        await self.db.commit()
        await self.db.refresh(new_fact)
        return new_fact

    async def get_relevant_facts(self, user_id: UUID, category: Optional[str] = None) -> List[FactModel]:
        stmt = select(FactModel).where(FactModel.user_id == user_id)
        if category:
            stmt = stmt.where(FactModel.category == category)
        stmt = stmt.order_by(desc(FactModel.confidence_score))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # --- Episodic Memory (Vector) ---
    async def create_episodic_memory(self, user_id: UUID, memory_data: EpisodicMemoryCreate, embedding: List[float]):
        """Stores a memory in Postgres and its vector in Qdrant."""
        
        # 1. DB Record
        db_memory = EpisodicMemoryModel(
            user_id=user_id,
            content=memory_data.content,
            summary=memory_data.summary,
            emotions=memory_data.emotions,
            topics=memory_data.topics,
            importance_score=memory_data.importance_score,
            context_type=memory_data.context_type
        )
        self.db.add(db_memory)
        await self.db.commit()
        await self.db.refresh(db_memory)
        
        # 2. Vector DB
        # Ensure collection exists (idempotent)
        vector_db.ensure_collection("episodic_memories")
        
        from qdrant_client.http import models
        point = models.PointStruct(
            id=str(db_memory.id),
            vector=embedding,
            payload={
                "user_id": str(user_id),
                "summary": memory_data.summary,
                "created_at": db_memory.created_at.isoformat(),
                "importance": memory_data.importance_score
            }
        )
        
        vector_db.upsert_vectors("episodic_memories", [point])
        
        # Update DB with vector ID (same as UUID) - actually redundant if using same ID, but good for explicit tracking
        # db_memory.vector_id = db_memory.id 
        # await self.db.commit()

        return db_memory

    async def search_memories(self, user_id: UUID, query_embedding: List[float], limit: int = 3) -> List[EpisodicMemoryModel]:
        # Ensure collection exists (idempotent)
        vector_db.ensure_collection("episodic_memories")

        # 1. Search Vector DB
        results = vector_db.search(
            collection_name="episodic_memories",
            vector=query_embedding,
            limit=limit,
            filter_conditions={"user_id": str(user_id)}
        )
        
        if not results:
            return []
            
        # 2. Hydrate from DB
        memory_ids = [UUID(point.id) for point in results]
        if not memory_ids:
            return []
            
        stmt = select(EpisodicMemoryModel).where(EpisodicMemoryModel.id.in_(memory_ids))
        db_results = await self.db.execute(stmt)
        memories = db_results.scalars().all()
        
        # Sort by relevance order from vector search
        memories_map = {m.id: m for m in memories}
        ordered = []
        for rid in memory_ids:
            if rid in memories_map:
                ordered.append(memories_map[rid])
                
        return ordered
    # --- Background Processing ---
    async def process_conversation_background(self, conversation_id: UUID) -> Dict[str, int]:
        """
        'Subconscious' processing:
        1. Fetch full conversation
        2. LLM Extraction (Facts, Summary, Episodic Moments)
        3. Persist to LTM (Facts & Vector)
        4. Clean up STM if needed (optional)
        """
        from app.infrastructure.tables import ChatConversationModel
        from app.services.llm import get_llm_provider
        
        llm = get_llm_provider()
        
        # 1. Fetch Conversation
        stmt = select(ChatConversationModel).where(ChatConversationModel.id == conversation_id)
        res = await self.db.execute(stmt)
        conv = res.scalar_one_or_none()
        
        if not conv:
            return {"status": "error", "message": "Conversation not found"}
            
        # Get messages
        # Ideally we process only new messages since last processing, but for MVP we process the "session"
        # Assuming we trigger this after a "session" ends or periodically.
        # For simplicity, let's take the last 20 messages.
        msgs = conv.messages[-20:] 
        if not msgs:
             return {"status": "skipped", "message": "No messages"}
             
        transcript = "\n".join([f"{m.role}: {m.content}" for m in msgs])
        
        # 2. LLM Extraction
        system_prompt = """
        Analyze this therapeutic conversation. Extract:
        1. FACTS: Structured basics about the user (Role, Stressor, new Preferences).
        2. MEMORY: One distinct episodic moment worth remembering (e.g. valid realization, strong emotion).
        
        Output JSON:
        {
          "facts": [{"category": "...", "value": "...", "confidence": 0.9}],
          "memory": {"summary": "...", "content": "...", "emotions": ["..."], "importance": 0.8}
        }
        """
        
        try:
            response_json = await llm.generate(system_prompt, f"Transcript:\n{transcript}")
            response_json = response_json.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_json)
            
            stats = {"facts": 0, "memories": 0}
            
            # 3. Persist Facts
            for f in data.get("facts", []):
                await self.add_fact(conv.user_id, FactCreate(
                    category=f.get("category", "general"),
                    value=f.get("value"),
                    confidence_score=f.get("confidence", 0.5)
                ))
                stats["facts"] += 1
                
            # 4. Persist Memory (Episodic)
            mem_data = data.get("memory")
            if mem_data:
                # Generate embedding for the summary/content
                text_to_embed = f"{mem_data.get('summary')} {mem_data.get('content')}"
                embedding = await llm.get_embedding(text_to_embed)
                
                await self.create_episodic_memory(
                    conv.user_id,
                    EpisodicMemoryCreate(
                        content=mem_data.get("content"),
                        summary=mem_data.get("summary"),
                        emotions=mem_data.get("emotions", []),
                        importance_score=mem_data.get("importance", 0.5),
                        context_type="conversation_fragment"
                    ),
                    embedding
                )
                stats["memories"] += 1
                
            return {"status": "success", "stats": stats}
            
        except Exception as e:
            logger.error(f"Error in background processing: {e}")
            return {"status": "error", "message": str(e)}
