import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Explicitly use the localhost port 5433
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/companion"

async def check_schema():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("Checking Schema State...")
        
        # Check patients.trend
        try:
            await conn.execute(text("SELECT trend FROM patients LIMIT 1"))
            print("✅ 'patients.trend' column EXISTS (Revision 6c8c7c9dc09b applied)")
            has_trend = True
        except Exception:
            print("❌ 'patients.trend' column MISSING")
            has_trend = False
            
        # Check users.language
        try:
            await conn.execute(text("SELECT language FROM users LIMIT 1"))
            print("✅ 'users.language' column EXISTS (Revision afc18ce3df71 applied)")
            has_language = True
        except Exception:
            print("❌ 'users.language' column MISSING")
            has_language = False

        # Check users.google_id
        try:
            await conn.execute(text("SELECT google_id FROM users LIMIT 1"))
            print("✅ 'users.google_id' column EXISTS (Revision 4838883a80a9 applied)")
            has_google = True
        except Exception:
            print("❌ 'users.google_id' column MISSING")
            has_google = False

        # Check facts table
        try:
            await conn.execute(text("SELECT count(*) FROM facts"))
            print("✅ 'facts' table EXISTS (Revision e985bdea3de9 applied)")
            has_facts = True
        except Exception:
            print("❌ 'facts' table MISSING")
            has_facts = False
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_schema())
