"""Redis client and connection management."""

import asyncio
import logging
from typing import Optional, Any, Dict, Union
from urllib.parse import urlparse

import aioredis
from aioredis import Redis

from .config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self.settings = get_settings()
        self._redis: Optional[Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None

    async def connect(self) -> None:
        """Connect to Redis server."""
        if self._redis is not None:
            return

        try:
            # Build connection URL
            if self.settings.redis_url:
                # Use provided URL
                redis_url = self.settings.redis_url
            else:
                # Build URL from components
                password_part = f":{self.settings.redis_password}@" if self.settings.redis_password else ""
                redis_url = f"redis://{password_part}{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}"

            # Create connection pool
            self._connection_pool = aioredis.ConnectionPool.from_url(
                redis_url,
                max_connections=self.settings.redis_pool_size,
                socket_timeout=self.settings.redis_timeout,
                socket_connect_timeout=self.settings.redis_timeout,
                health_check_interval=30
            )

            # Create Redis client
            self._redis = aioredis.Redis(connection_pool=self._connection_pool)

            # Test connection
            await self._redis.ping()
            logger.info("Successfully connected to Redis")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

        if self._connection_pool:
            await self._connection_pool.aclose()
            self._connection_pool = None

        logger.info("Disconnected from Redis")

    @property
    def redis(self) -> Redis:
        """Get Redis client instance."""
        if self._redis is None:
            raise RuntimeError("Redis client is not connected. Call connect() first.")
        return self._redis

    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if self._redis is None:
                return False
            await self._redis.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    async def get(self, key: str) -> Optional[bytes]:
        """Get value from Redis."""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key} from Redis: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Union[str, bytes],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in Redis."""
        try:
            result = await self.redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set key {key} in Redis: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis."""
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete keys {keys} from Redis: {e}")
            return 0

    async def exists(self, *keys: str) -> int:
        """Check if keys exist in Redis."""
        try:
            return await self.redis.exists(*keys)
        except Exception as e:
            logger.error(f"Failed to check existence of keys {keys} in Redis: {e}")
            return 0

    async def expire(self, key: str, time: int) -> bool:
        """Set expiration for a key."""
        try:
            return await self.redis.expire(key, time)
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key} in Redis: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key} from Redis: {e}")
            return -2  # Key does not exist

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment value of a key."""
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key} in Redis: {e}")
            return 0

    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """Get field from Redis hash."""
        try:
            return await self.redis.hget(name, key)
        except Exception as e:
            logger.error(f"Failed to get hash field {key} from {name} in Redis: {e}")
            return None

    async def hset(self, name: str, key: str, value: Union[str, bytes]) -> int:
        """Set field in Redis hash."""
        try:
            return await self.redis.hset(name, key, value)
        except Exception as e:
            logger.error(f"Failed to set hash field {key} in {name} in Redis: {e}")
            return 0

    async def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """Get all fields from Redis hash."""
        try:
            return await self.redis.hgetall(name)
        except Exception as e:
            logger.error(f"Failed to get all hash fields from {name} in Redis: {e}")
            return {}


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get or create global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client


async def close_redis_client() -> None:
    """Close global Redis client instance."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None