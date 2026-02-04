import os
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        logger.info(f"Redis client initialized at {REDIS_URL}")

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int = None):
        if expire:
            await self.redis.set(key, value, ex=expire)
        else:
            await self.redis.set(key, value)
            
    async def delete(self, key: str):
        await self.redis.delete(key)
        
    async def close(self):
        await self.redis.close()

# Global instance
redis_client = RedisClient()
