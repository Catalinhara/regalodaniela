import asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
import os

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/companion"

async def check_schema():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        print("Connected.")
        # Async inspection is a bit tricky, often easier to just run SQL queries to check schema
        # or use run_sync to use inspector
        
        await conn.run_sync(run_inspection)

def run_inspection(conn):
    insp = inspect(conn)
    tables = insp.get_table_names()
    print(f"Tables found: {tables}")
    
    required_tables = ["companion_contexts", "chat_conversations", "chat_messages"]
    
    for t in required_tables:
        if t in tables:
            print(f"--- Table: {t} ---")
            columns = [c['name'] for c in insp.get_columns(t)]
            print(f"Columns: {columns}")
        else:
            print(f"MISSING TABLE: {t}")

if __name__ == "__main__":
    asyncio.run(check_schema())
