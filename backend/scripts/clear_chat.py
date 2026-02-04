import asyncio
import os
import sys

# Add app to sys.path
sys.path.append(os.getcwd())

from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.cache import redis_client
from app.infrastructure.tables import ChatConversationModel, ChatMessageModel, UserModel
from sqlalchemy import delete, select

async def clear_all_chats():
    print("🧹 Clearing all chat history (Postgres & Redis)...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Get all users to clear their Redis keys
            res = await db.execute(select(UserModel.id))
            user_ids = res.scalars().all()
            
            for uid in user_ids:
                key = f"stm:{uid}"
                await redis_client.delete(key)
                print(f"  - Cleared Redis STM for user {uid}")
            
            # 2. Delete all chat messages
            await db.execute(delete(ChatMessageModel))
            # 3. Delete all chat conversations
            await db.execute(delete(ChatConversationModel))
            
            await db.commit()
            print("✅ All chat history deleted from database.")
        except Exception as e:
            print(f"❌ Error during clear: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(clear_all_chats())
