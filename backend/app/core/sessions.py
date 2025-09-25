"""Session storage and management using Redis."""

import uuid
import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .redis import get_redis_client
from .cache import CacheManager, TTLConfig

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """会话状态枚举."""

    ACTIVE = "active"       # 活跃
    EXPIRED = "expired"     # 已过期
    REVOKED = "revoked"     # 已撤销
    INACTIVE = "inactive"   # 非活跃


@dataclass
class SessionInfo:
    """会话信息数据类."""

    session_id: str
    user_id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str = None
    last_accessed: str = None
    expires_at: str = None
    status: SessionStatus = SessionStatus.ACTIVE
    data: Dict[str, Any] = None

    def __post_init__(self):
        """初始化后处理."""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow().isoformat()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """从字典创建实例."""
        return cls(**data)

    def is_expired(self) -> bool:
        """检查会话是否已过期."""
        if self.expires_at is None:
            return False

        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except (ValueError, TypeError):
            return True

    def update_last_accessed(self) -> None:
        """更新最后访问时间."""
        self.last_accessed = datetime.utcnow().isoformat()


class SessionManager:
    """会话管理器."""

    def __init__(
        self,
        default_ttl: int = 7200,  # 默认2小时
        max_sessions_per_user: int = 5,  # 每用户最大会话数
        cleanup_interval: int = 3600  # 清理间隔1小时
    ):
        """初始化会话管理器."""
        self.default_ttl = default_ttl
        self.max_sessions_per_user = max_sessions_per_user
        self.cleanup_interval = cleanup_interval

        # 使用专门的会话缓存管理器
        ttl_config = TTLConfig(session_ttl=default_ttl)
        self.cache = CacheManager(namespace="sessions", ttl_config=ttl_config)
        self._redis_client = None

    async def _get_redis(self):
        """获取Redis客户端实例."""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
        return self._redis_client

    def _make_session_key(self, session_id: str) -> str:
        """生成会话键."""
        return f"session:{session_id}"

    def _make_user_sessions_key(self, user_id: str) -> str:
        """生成用户会话列表键."""
        return f"user_sessions:{user_id}"

    async def create_session(
        self,
        user_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        ttl: Optional[int] = None,
        session_data: Optional[Dict[str, Any]] = None
    ) -> SessionInfo:
        """创建新会话."""
        session_id = str(uuid.uuid4())
        ttl = ttl or self.default_ttl
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            data=session_data or {}
        )

        try:
            # 存储会话信息
            session_key = self._make_session_key(session_id)
            await self.cache.set(session_key, session.to_dict(), ttl=ttl, cache_type="session")

            # 更新用户会话列表
            await self._add_user_session(user_id, session_id, ttl)

            # 检查并清理超出限制的会话
            await self._cleanup_user_sessions(user_id)

            logger.info(f"Created session {session_id} for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息."""
        try:
            session_key = self._make_session_key(session_id)
            session_data = await self.cache.get(session_key)

            if session_data is None:
                return None

            session = SessionInfo.from_dict(session_data)

            # 检查会话是否过期
            if session.is_expired():
                await self.revoke_session(session_id)
                return None

            # 更新最后访问时间
            session.update_last_accessed()
            await self.cache.set(session_key, session.to_dict(), cache_type="session")

            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """更新会话数据."""
        try:
            session = await self.get_session(session_id)
            if session is None:
                return False

            # 更新会话数据
            session.data.update(session_data)
            session.update_last_accessed()

            # 保存更新后的会话
            session_key = self._make_session_key(session_id)
            await self.cache.set(session_key, session.to_dict(), cache_type="session")

            logger.debug(f"Updated session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    async def revoke_session(self, session_id: str) -> bool:
        """撤销会话."""
        try:
            session_key = self._make_session_key(session_id)
            session_data = await self.cache.get(session_key)

            if session_data:
                session = SessionInfo.from_dict(session_data)
                # 从用户会话列表中移除
                await self._remove_user_session(session.user_id, session_id)

            # 删除会话
            await self.cache.delete(session_key)

            logger.info(f"Revoked session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke session {session_id}: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """获取用户的所有活跃会话."""
        try:
            user_sessions_key = self._make_user_sessions_key(user_id)
            session_ids = await self.cache.get(user_sessions_key, default=[])

            sessions = []
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session and session.status == SessionStatus.ACTIVE:
                    sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []

    async def revoke_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """撤销用户的所有会话（可选择性保留某个会话）."""
        try:
            sessions = await self.get_user_sessions(user_id)
            revoked_count = 0

            for session in sessions:
                if except_session_id and session.session_id == except_session_id:
                    continue

                if await self.revoke_session(session.session_id):
                    revoked_count += 1

            logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
            return revoked_count

        except Exception as e:
            logger.error(f"Failed to revoke user sessions for {user_id}: {e}")
            return 0

    async def _add_user_session(self, user_id: str, session_id: str, ttl: int) -> None:
        """将会话添加到用户会话列表."""
        user_sessions_key = self._make_user_sessions_key(user_id)
        session_ids = await self.cache.get(user_sessions_key, default=[])

        if session_id not in session_ids:
            session_ids.append(session_id)
            await self.cache.set(user_sessions_key, session_ids, ttl=ttl, cache_type="session")

    async def _remove_user_session(self, user_id: str, session_id: str) -> None:
        """从用户会话列表中移除会话."""
        user_sessions_key = self._make_user_sessions_key(user_id)
        session_ids = await self.cache.get(user_sessions_key, default=[])

        if session_id in session_ids:
            session_ids.remove(session_id)
            await self.cache.set(user_sessions_key, session_ids, cache_type="session")

    async def _cleanup_user_sessions(self, user_id: str) -> None:
        """清理用户超出限制的会话."""
        sessions = await self.get_user_sessions(user_id)

        if len(sessions) <= self.max_sessions_per_user:
            return

        # 按最后访问时间排序，保留最新的会话
        sessions.sort(key=lambda s: s.last_accessed, reverse=True)

        # 撤销超出限制的旧会话
        for session in sessions[self.max_sessions_per_user:]:
            await self.revoke_session(session.session_id)

    async def cleanup_expired_sessions(self) -> int:
        """清理所有过期会话."""
        try:
            redis = await self._get_redis()
            pattern = f"{self.cache.namespace}:session:*"

            cleaned_count = 0
            async for key in redis.redis.scan_iter(match=pattern):
                key_str = key.decode('utf-8')
                session_id = key_str.split(':')[-1]

                session = await self.get_session(session_id)
                if session is None or session.is_expired():
                    await self.revoke_session(session_id)
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息."""
        try:
            redis = await self._get_redis()
            pattern = f"{self.cache.namespace}:session:*"

            total_sessions = 0
            active_sessions = 0
            expired_sessions = 0

            async for key in redis.redis.scan_iter(match=pattern):
                total_sessions += 1
                key_str = key.decode('utf-8')
                session_id = key_str.split(':')[-1]

                session_data = await self.cache.get(f"session:{session_id}")
                if session_data:
                    session = SessionInfo.from_dict(session_data)
                    if session.is_expired():
                        expired_sessions += 1
                    else:
                        active_sessions += 1

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "max_sessions_per_user": self.max_sessions_per_user,
                "default_ttl": self.default_ttl
            }

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}


# 全局会话管理器实例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取或创建会话管理器实例."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def create_session(
    user_id: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    ttl: Optional[int] = None,
    session_data: Optional[Dict[str, Any]] = None
) -> SessionInfo:
    """创建新会话（便捷函数）."""
    manager = get_session_manager()
    return await manager.create_session(user_id, user_agent, ip_address, ttl, session_data)


async def get_session(session_id: str) -> Optional[SessionInfo]:
    """获取会话信息（便捷函数）."""
    manager = get_session_manager()
    return await manager.get_session(session_id)


async def revoke_session(session_id: str) -> bool:
    """撤销会话（便捷函数）."""
    manager = get_session_manager()
    return await manager.revoke_session(session_id)