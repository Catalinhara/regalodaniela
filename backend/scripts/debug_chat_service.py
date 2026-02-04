import asyncio
import sys
import os
from uuid import UUID

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.infrastructure.database import engine
from app.infrastructure.tables import UserModel
from app.services.chat_service import ChatService

async def debug_chat():
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        # 1. Get a real user
        stmt = select(UserModel).limit(1)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            print("No user found.")
            return

        print(f"Testing for user: {user.email} (ID: {user.id})")
        service = ChatService(db)
        
        try:
            print("\n--- Calling generate_response ---")
            resp = await service.generate_response(user.id, "Hola Compy, ¿cómo estás?")
            print(f"Response: {resp}")
        except Exception as e:
            import traceback
            print(f"FAILED with exception: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chat())
