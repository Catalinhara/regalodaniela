#!/usr/bin/env python3
"""
Database cleanup script for ClaraMente development environment.
Drops all tables and recreates them from scratch using SQLAlchemy models.

Usage:
    python reset_database.py
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import Base and all models
sys.path.append('backend')
from app.infrastructure.database import Base
from app.infrastructure.tables import (
    UserModel, 
    RefreshTokenModel, 
    CompanionContextModel,
    CheckInModel,
    InsightModel,
    PatientModel,
    ColleagueModel,
    EventModel,
    ChatConversationModel,
    ChatMessageModel
)

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/companion"

async def reset_database():
    """Drop all tables and recreate them."""
    print("🔄 Starting database reset...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("\n🗑️  Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            print("\n✨ Creating fresh tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        print("\n✅ Database reset complete!")
        print("📊 Tables recreated:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
            
    except Exception as e:
        print(f"\n❌ Error during database reset: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE RESET SCRIPT - ClaraMente")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("   Database: companion")
    print("   Host: localhost:5433")
    
    response = input("\n🤔 Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        asyncio.run(reset_database())
    else:
        print("\n❌ Reset cancelled.")
        sys.exit(0)
