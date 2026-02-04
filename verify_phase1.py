import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Testing imports...")
    from app.domain.memory_models import Fact, EpisodicMemory
    print("✅ Domain Models imported")
    
    from app.infrastructure.tables import FactModel, EpisodicMemoryModel
    print("✅ SQLAlchemy Models imported")
    
    from app.infrastructure.vector_db import vector_db
    print("✅ VectorDB client imported")
    
    from app.infrastructure.cache import redis_client
    print("✅ Redis client imported")
    
    from app.services.memory_service import MemoryService
    print("✅ MemoryService imported")
    
    print("\nPhase 1 Static Verification Passed!")
    
except Exception as e:
    print(f"\n❌ Verification Failed: {e}")
    sys.exit(1)
