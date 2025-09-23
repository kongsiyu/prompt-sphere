"""Cache abstraction layer using Redis."""

import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta

from .redis import get_redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """High-level cache management interface."""

    def __init__(self, namespace: str = "prompt_sphere") -> None:
        """Initialize cache manager with namespace."""
        self.namespace = namespace
        self._redis_client = None

    async def _get_redis(self):
        """Get Redis client instance."""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
        return self._redis_client

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}:{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)

            # Get raw value
            raw_value = await redis.get(namespaced_key)
            if raw_value is None:
                return default

            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(raw_value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(raw_value)
                except pickle.PickleError:
                    # Return raw bytes if both fail
                    return raw_value

        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: str = "json"
    ) -> bool:
        """Set value in cache."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)

            # Serialize value
            if serialize == "json":
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError) as e:
                    logger.warning(f"JSON serialization failed for key {key}, falling back to pickle: {e}")
                    serialized_value = pickle.dumps(value)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                # Assume it's already a string or bytes
                serialized_value = value

            # Set with optional TTL
            return await redis.set(namespaced_key, serialized_value, ex=ttl)

        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete keys from cache."""
        try:
            redis = await self._get_redis()
            namespaced_keys = [self._make_key(key) for key in keys]
            return await redis.delete(*namespaced_keys)
        except Exception as e:
            logger.error(f"Failed to delete cache keys {keys}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)
            return bool(await redis.exists(namespaced_key))
        except Exception as e:
            logger.error(f"Failed to check existence of cache key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a cache key."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)
            return await redis.expire(namespaced_key, ttl)
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a cache key."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)
            return await redis.ttl(namespaced_key)
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value in cache."""
        try:
            redis = await self._get_redis()
            namespaced_key = self._make_key(key)
            return await redis.incr(namespaced_key, amount)
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        default_func,
        ttl: Optional[int] = None,
        serialize: str = "json"
    ) -> Any:
        """Get value from cache or set it using default function."""
        # Try to get from cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Generate value using default function
        try:
            if callable(default_func):
                if hasattr(default_func, '__await__'):  # Async function
                    value = await default_func()
                else:
                    value = default_func()
            else:
                value = default_func

            # Set in cache
            await self.set(key, value, ttl=ttl, serialize=serialize)
            return value

        except Exception as e:
            logger.error(f"Failed to generate or cache value for key {key}: {e}")
            return None

    async def clear_namespace(self) -> int:
        """Clear all keys in the current namespace."""
        try:
            redis = await self._get_redis()
            pattern = f"{self.namespace}:*"

            # Use scan to find all keys
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await redis.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Failed to clear namespace {self.namespace}: {e}")
            return 0


class SessionCache(CacheManager):
    """Cache manager for user sessions."""

    def __init__(self) -> None:
        """Initialize session cache."""
        super().__init__(namespace="sessions")

    async def create_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> str:
        """Create a new session."""
        import uuid
        session_id = str(uuid.uuid4())
        session_key = f"user:{user_id}:session:{session_id}"

        session_data.update({
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        })

        success = await self.set(session_key, session_data, ttl=ttl)
        return session_id if success else None

    async def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        session_key = f"user:{user_id}:session:{session_id}"
        return await self.get(session_key)

    async def update_session(self, user_id: str, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data."""
        session_key = f"user:{user_id}:session:{session_id}"
        # Get existing TTL
        current_ttl = await self.ttl(session_key)
        if current_ttl > 0:
            return await self.set(session_key, session_data, ttl=current_ttl)
        return False

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a session."""
        session_key = f"user:{user_id}:session:{session_id}"
        return bool(await self.delete(session_key))


# Global cache instances
_default_cache: Optional[CacheManager] = None
_session_cache: Optional[SessionCache] = None


def get_cache(namespace: str = "prompt_sphere") -> CacheManager:
    """Get or create cache manager instance."""
    global _default_cache
    if _default_cache is None or _default_cache.namespace != namespace:
        _default_cache = CacheManager(namespace=namespace)
    return _default_cache


def get_session_cache() -> SessionCache:
    """Get or create session cache instance."""
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCache()
    return _session_cache