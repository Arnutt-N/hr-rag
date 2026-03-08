"""Redis Cache Service for HR-RAG

Provides caching functionality for search queries and chat responses.
Includes graceful degradation when Redis is unavailable.
"""

import hashlib
import json
import logging
from typing import Optional, Any, List, Dict

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache service with graceful degradation"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._enabled = False
    
    async def connect(self) -> bool:
        """Connect to Redis server"""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self.client.ping()
            self._enabled = True
            logger.info(f"✅ Redis cache connected: {settings.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, caching disabled: {e}")
            self.client = None
            self._enabled = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server"""
        if self.client:
            await self.client.close()
            self.client = None
            self._enabled = False
            logger.info("Redis cache disconnected")
    
    @property
    def is_enabled(self) -> bool:
        """Check if cache is enabled and connected"""
        return self._enabled and self.client is not None

    async def ping(self) -> bool:
        """Ping Redis to verify connectivity"""
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_enabled:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.is_enabled:
            return False
        try:
            ttl = ttl or settings.cache_ttl_seconds
            await self.client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_enabled:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_enabled:
            return 0
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    @staticmethod
    def make_search_key(project_id: int, query: str, top_k: int) -> str:
        """Create cache key for search query"""
        # Hash the query to keep key length manageable
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"rag:search:p{project_id}:k{top_k}:{query_hash}"
    
    @staticmethod
    def make_chat_key(project_id: int, session_id: int, message: str) -> str:
        """Create cache key for chat response"""
        message_hash = hashlib.sha256(message.encode()).hexdigest()[:16]
        return f"rag:chat:p{project_id}:s{session_id}:{message_hash}"
    
    @staticmethod
    def invalidate_project_cache(project_id: int) -> str:
        """Generate pattern to invalidate all cache for a project"""
        return f"rag:*:p{project_id}:*"


# Global singleton instance
_cache: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the global cache service instance"""
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
