import json
import pickle
from typing import Any, Optional, Union
from aioredis import Redis
from .config import settings

class RedisClient:
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = Redis.from_url(settings.redis_url, decode_responses=False)
        return self.redis
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self.redis:
            await self.connect()
        
        try:
            serialized = pickle.dumps(value)
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            await self.connect()
        
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis"""
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get_json error: {e}")
            return None
    
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """Set JSON value in Redis"""
        if not self.redis:
            await self.connect()
        
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            print(f"Redis set_json error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.expire(key, seconds)
            return True
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        if not self.redis:
            await self.connect()
        
        try:
            keys = await self.redis.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            print(f"Redis keys error: {e}")
            return []

# Global Redis client instance
redis_client = RedisClient()
