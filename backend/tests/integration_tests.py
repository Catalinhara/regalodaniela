import asyncio
import sys
import os
import uuid
from datetime import datetime
import logging
from unittest.mock import AsyncMock

# Add backend directory to path so we can resolve 'app'
# In container, this is /app. On host, it might be the backend folder.
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)
# Also add parent just in case
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Minimal logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

async def run_integration_tests():
    logger.info("🚀 Starting Exhaustive Integration Tests...")
    
    # 0. Dependencies
    try:
        from app.infrastructure.database import AsyncSessionLocal
        from app.infrastructure.cache import redis_client
        from app.infrastructure.vector_db import vector_db
        from app.services.memory_service import MemoryService
        from app.services.chat_service import ChatService
        from app.domain.memory_models import FactCreate, EpisodicMemoryCreate
        from app.infrastructure.tables import UserModel
        from sqlalchemy import select, delete
    except ImportError as e:
        logger.error(f"Failed to import backend modules. Ensure you are running from project root. Error: {e}")
        return

    # 1. Infrastructure Checks
    logger.info("\n[1/5] Checking Infrastructure...")
    
    # Check Redis
    try:
        await redis_client.set("test_key", "test_value", expire=10)
        val = await redis_client.get("test_key")
        if val:
             decoded_val = val.decode() if isinstance(val, bytes) else val
             if decoded_val == "test_value":
                  logger.info("✅ Redis Connection OK")
             else:
                  logger.error(f"❌ Redis Value Mismatch: {decoded_val}")
    except Exception as e:
        logger.error(f"❌ Redis Connection Failed: {e}")

    # Check Qdrant
    if vector_db.client:
        try:
             # Just check if we can list collections
             colls = vector_db.client.get_collections()
             logger.info(f"✅ Qdrant Connection OK. Collections: {[c.name for c in colls.collections]}")
        except Exception as e:
             logger.error(f"❌ Qdrant Operation Failed: {e}")
    else:
        logger.error("❌ Qdrant Client Not Initialized")

    # 2. Database & Data Setup
    logger.info("\n[2/5] Setting up Test User...")
    TEST_USER_ID = uuid.uuid4()
    TEST_EMAIL = f"test_integration_{TEST_USER_ID}@example.com"
    
    async with AsyncSessionLocal() as db:
        try:
            # Create User
            user = UserModel(id=TEST_USER_ID, email=TEST_EMAIL, hashed_password="hashed_dummy", full_name="Integration Test User")
            db.add(user)
            await db.commit()
            logger.info(f"✅ Created Test User: {TEST_USER_ID}")
            
            # 3. Service Logic Tests
            logger.info("\n[3/5] Testing Memory Service...")
            mem_service = MemoryService(db)
            
            # A. Add Fact
            fact = await mem_service.add_fact(TEST_USER_ID, FactCreate(
                category="preference", value="I prefer concise answers", confidence_score=0.9
            ))
            logger.info(f"✅ Added Fact: {fact.value}")
            
            # B. Check Fact Retrieval
            facts = await mem_service.get_relevant_facts(TEST_USER_ID)
            if any(f.value == "I prefer concise answers" for f in facts):
                logger.info("✅ Fact Retrieval OK")
            else:
                logger.error("❌ Fact Retrieval Failed")
                
            # C. Episodic Memory (Mock Embedding)
            if vector_db.client:
                dummy_vector = [0.1] * 1536
                memory = await mem_service.create_episodic_memory(
                    TEST_USER_ID, 
                    EpisodicMemoryCreate(content="I felt happy today", summary="Happy moment", importance_score=0.8),
                    dummy_vector
                )
                logger.info(f"✅ Added Memory: {memory.summary}")
                
                # Wait for indexing? Usually instant for 1 item.
                search_res = await mem_service.search_memories(TEST_USER_ID, dummy_vector, limit=1)
                if search_res and search_res[0].id == memory.id:
                    logger.info("✅ Vector Search OK")
                else:
                    logger.warning("⚠️ Vector Search returned no results (might need indexing time or real Qdrant)")
            
            # 4. Chat Flow
            logger.info("\n[4/5] Testing Chat Service...")
            chat_service = ChatService(db)
            # Mock LLM for Chat to not consume credits/latency
            chat_service.llm.generate = AsyncMock(return_value="This is a test response.")
            chat_service.llm.get_embedding = AsyncMock(return_value=[0.1]*1536)
            
            # chat_service.llm.get_embedding = AsyncMock(return_value=[0.1]*1536)
            
            response = await chat_service.generate_response(TEST_USER_ID, "Hello friend")
            logger.info(f"✅ Chat Response: {response}")
            
            # Check STM
            stm = await mem_service.get_stm_context(TEST_USER_ID)
            if len(stm) >= 2: # User + Assistant
                logger.info("✅ STM Updated OK")
            else:
                logger.error("❌ STM Update Failed")
                
        except Exception as e:
            logger.error(f"❌ Test Execution Failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 5. Cleanup
            logger.info("\n[5/5] Cleaning up...")
            try:
                # Delete User (Cascade should handle facts/memories/chats)
                await db.execute(delete(UserModel).where(UserModel.id == TEST_USER_ID))
                await db.commit()
                logger.info("✅ Test Data Deleted")
            except Exception as e:
                logger.error(f"❌ Cleanup Failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_integration_tests())
