"""会话管理服务

提供用户会话的创建、验证、更新和清理功能，支持Redis存储
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from app.auth.jwt import JWTHandler, JWTPayload, get_jwt_handler
from app.core.config import get_settings
from app.core.redis import RedisClient, get_redis_client

from .base import BaseService, NotFoundError, ServiceError, ValidationError

logger = logging.getLogger(__name__)


class SessionData:
    """会话数据类"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        username: str,
        roles: List[str],
        created_at: datetime,
        last_accessed: datetime,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.created_at = created_at
        self.last_accessed = last_accessed
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """从字典创建会话数据实例"""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            username=data["username"],
            roles=data["roles"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            metadata=data.get("metadata", {})
        )

    def is_expired(self) -> bool:
        """检查会话是否已过期"""
        return datetime.now(timezone.utc) > self.expires_at

    def extend_expiration(self, hours: int = 24) -> None:
        """延长会话过期时间"""
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.last_accessed = datetime.now(timezone.utc)


class SessionService(BaseService):
    """会话管理服务类

    功能包括：
    - 会话创建和销毁
    - 会话验证和更新
    - JWT令牌管理
    - Redis会话存储
    - 会话清理和过期处理
    - 用户活动跟踪
    """

    def __init__(self):
        super().__init__(
            cache_namespace="session",
            enable_caching=True,
            default_cache_ttl=3600
        )
        self.settings = get_settings()
        self._jwt_handler: Optional[JWTHandler] = None
        self._redis: Optional[RedisClient] = None

        # 会话配置
        self.session_timeout_hours = 24  # 会话超时时间（小时）
        self.max_sessions_per_user = 10  # 每用户最大会话数
        self.inactive_timeout_minutes = 120  # 非活跃超时时间（分钟）

    @property
    async def jwt_handler(self) -> JWTHandler:
        """获取JWT处理器实例"""
        if self._jwt_handler is None:
            self._jwt_handler = get_jwt_handler()
        return self._jwt_handler

    @property
    async def redis(self) -> RedisClient:
        """获取Redis客户端实例"""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def create_session(
        self,
        user_id: str,
        username: str,
        roles: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建新用户会话

        Args:
            user_id: 用户ID
            username: 用户名
            roles: 用户角色列表
            ip_address: IP地址
            user_agent: 用户代理
            metadata: 额外的元数据

        Returns:
            包含会话信息和JWT令牌的字典

        Raises:
            ValidationError: 输入数据无效
            ServiceError: 创建失败
        """
        try:
            await self.log_operation("create_session", {"user_id": user_id, "username": username})

            # 验证输入数据
            if not user_id or not username:
                raise ValidationError("User ID and username are required")

            if not isinstance(roles, list):
                raise ValidationError("Roles must be a list")

            # 生成会话ID
            session_id = str(uuid4())
            now = datetime.now(timezone.utc)

            # 创建会话数据
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                username=username,
                roles=roles,
                created_at=now,
                last_accessed=now,
                expires_at=now + timedelta(hours=self.session_timeout_hours),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata
            )

            # 生成JWT令牌
            jwt_handler = await self.jwt_handler
            tokens = jwt_handler.generate_tokens(user_id, username, roles)

            # 存储会话到Redis
            redis = await self.redis
            session_key = f"session:{session_id}"
            session_json = json.dumps(session_data.to_dict())

            await redis.set(session_key, session_json, ex=int(self.session_timeout_hours * 3600))

            # 存储用户的会话列表
            user_sessions_key = f"user_sessions:{user_id}"
            await redis.sadd(user_sessions_key, session_id)
            await redis.expire(user_sessions_key, int(self.session_timeout_hours * 3600))

            # 限制每用户的会话数量
            await self._cleanup_user_sessions(user_id)

            # 存储刷新令牌映射
            refresh_jti = tokens.get("refresh_jti")
            if refresh_jti:
                refresh_key = f"refresh_token:{refresh_jti}"
                refresh_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "username": username,
                    "roles": roles
                }
                await redis.set(refresh_key, json.dumps(refresh_data), ex=7 * 24 * 3600)  # 7天

            await self.log_operation(
                "session_created",
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "username": username,
                    "ip_address": ip_address
                }
            )

            return {
                "session_id": session_id,
                "user_id": user_id,
                "username": username,
                "roles": roles,
                "created_at": session_data.created_at.isoformat(),
                "expires_at": session_data.expires_at.isoformat(),
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"]
            }

        except ValidationError as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "create_session", {"user_id": user_id})
            raise error

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话数据

        Args:
            session_id: 会话ID

        Returns:
            会话数据实例或None
        """
        try:
            redis = await self.redis
            session_key = f"session:{session_id}"
            session_json = await redis.get(session_key)

            if not session_json:
                return None

            session_data_dict = json.loads(session_json.decode())
            session_data = SessionData.from_dict(session_data_dict)

            # 检查会话是否过期
            if session_data.is_expired():
                await self._cleanup_session(session_id)
                return None

            return session_data

        except Exception as e:
            self.logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """验证会话有效性

        Args:
            session_id: 会话ID

        Returns:
            有效的会话信息字典或None
        """
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return None

            # 更新最后访问时间
            session_data.last_accessed = datetime.now(timezone.utc)
            await self._update_session(session_data)

            await self.log_operation(
                "session_validated",
                {"session_id": session_id, "user_id": session_data.user_id},
                level="debug"
            )

            return {
                "session_id": session_data.session_id,
                "user_id": session_data.user_id,
                "username": session_data.username,
                "roles": session_data.roles,
                "last_accessed": session_data.last_accessed.isoformat(),
                "expires_at": session_data.expires_at.isoformat()
            }

        except Exception as e:
            error = await self.handle_error(e, "validate_session", {"session_id": session_id})
            raise error

    async def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """延长会话过期时间

        Args:
            session_id: 会话ID
            hours: 延长的小时数

        Returns:
            是否延长成功
        """
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            session_data.extend_expiration(hours)
            await self._update_session(session_data)

            await self.log_operation(
                "session_extended",
                {"session_id": session_id, "user_id": session_data.user_id, "hours": hours}
            )

            return True

        except Exception as e:
            self.logger.error(f"Error extending session {session_id}: {e}")
            return False

    async def destroy_session(self, session_id: str) -> bool:
        """销毁会话

        Args:
            session_id: 会话ID

        Returns:
            是否销毁成功
        """
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                await self.log_operation(
                    "session_destroyed",
                    {"session_id": session_id, "user_id": session_data.user_id}
                )

            await self._cleanup_session(session_id)
            return True

        except Exception as e:
            error = await self.handle_error(e, "destroy_session", {"session_id": session_id})
            raise error

    async def destroy_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """销毁用户的所有会话

        Args:
            user_id: 用户ID
            except_session_id: 保留的会话ID（可选）

        Returns:
            销毁的会话数量
        """
        try:
            redis = await self.redis
            user_sessions_key = f"user_sessions:{user_id}"

            # 获取用户的所有会话
            session_ids = await redis.smembers(user_sessions_key)
            if not session_ids:
                return 0

            destroyed_count = 0
            for session_id_bytes in session_ids:
                session_id = session_id_bytes.decode()

                # 跳过要保留的会话
                if except_session_id and session_id == except_session_id:
                    continue

                # 销毁会话
                await self._cleanup_session(session_id)
                destroyed_count += 1

            # 清理用户会话列表
            if except_session_id:
                # 只保留指定的会话
                await redis.delete(user_sessions_key)
                await redis.sadd(user_sessions_key, except_session_id)
                await redis.expire(user_sessions_key, int(self.session_timeout_hours * 3600))
            else:
                # 删除所有会话
                await redis.delete(user_sessions_key)

            await self.log_operation(
                "user_sessions_destroyed",
                {"user_id": user_id, "destroyed_count": destroyed_count}
            )

            return destroyed_count

        except Exception as e:
            error = await self.handle_error(e, "destroy_user_sessions", {"user_id": user_id})
            raise error

    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """使用刷新令牌生成新的访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的令牌信息字典或None
        """
        try:
            jwt_handler = await self.jwt_handler

            # 验证刷新令牌
            payload = jwt_handler.verify_token(refresh_token)
            if not payload or payload.scope != "refresh":
                return None

            # 检查刷新令牌是否在Redis中
            redis = await self.redis
            refresh_key = f"refresh_token:{payload.jti}"
            refresh_data_json = await redis.get(refresh_key)

            if not refresh_data_json:
                return None

            refresh_data = json.loads(refresh_data_json.decode())

            # 生成新的访问令牌
            new_tokens = jwt_handler.refresh_access_token(refresh_token)
            if not new_tokens:
                return None

            await self.log_operation(
                "tokens_refreshed",
                {"user_id": refresh_data["user_id"], "username": refresh_data["username"]}
            )

            return {
                **new_tokens,
                "user_id": refresh_data["user_id"],
                "username": refresh_data["username"],
                "roles": refresh_data["roles"]
            }

        except Exception as e:
            error = await self.handle_error(e, "refresh_tokens")
            raise error

    async def invalidate_refresh_token(self, refresh_jti: str) -> bool:
        """使刷新令牌失效

        Args:
            refresh_jti: 刷新令牌JTI

        Returns:
            是否成功
        """
        try:
            redis = await self.redis
            refresh_key = f"refresh_token:{refresh_jti}"
            result = await redis.delete(refresh_key)

            await self.log_operation(
                "refresh_token_invalidated",
                {"refresh_jti": refresh_jti}
            )

            return result > 0

        except Exception as e:
            self.logger.error(f"Error invalidating refresh token: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            会话信息列表
        """
        try:
            redis = await self.redis
            user_sessions_key = f"user_sessions:{user_id}"

            session_ids = await redis.smembers(user_sessions_key)
            sessions = []

            for session_id_bytes in session_ids:
                session_id = session_id_bytes.decode()
                session_data = await self.get_session(session_id)

                if session_data:
                    sessions.append({
                        "session_id": session_data.session_id,
                        "created_at": session_data.created_at.isoformat(),
                        "last_accessed": session_data.last_accessed.isoformat(),
                        "expires_at": session_data.expires_at.isoformat(),
                        "ip_address": session_data.ip_address,
                        "user_agent": session_data.user_agent
                    })

            # 按创建时间降序排序
            sessions.sort(key=lambda x: x["created_at"], reverse=True)

            return sessions

        except Exception as e:
            error = await self.handle_error(e, "get_user_sessions", {"user_id": user_id})
            raise error

    async def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """清理过期会话

        Returns:
            清理统计信息字典
        """
        try:
            await self.log_operation("cleanup_expired_sessions")

            redis = await self.redis
            cleaned_sessions = 0
            cleaned_refresh_tokens = 0

            # 使用扫描模式避免阻塞Redis
            async def scan_and_cleanup(pattern: str, cleanup_func):
                nonlocal cleaned_sessions, cleaned_refresh_tokens
                cursor = 0
                count = 0

                while True:
                    cursor, keys = await redis.redis.scan(cursor, match=pattern, count=100)

                    for key_bytes in keys:
                        key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                        try:
                            await cleanup_func(key)
                            count += 1
                        except Exception as e:
                            self.logger.error(f"Error cleaning up key {key}: {e}")

                    if cursor == 0:
                        break

                return count

            # 清理过期会话
            async def cleanup_session_key(key: str):
                nonlocal cleaned_sessions
                if key.startswith("session:"):
                    session_id = key.replace("session:", "")
                    session_data = await self.get_session(session_id)
                    if not session_data:  # 过期或无效的会话
                        await self._cleanup_session(session_id)
                        cleaned_sessions += 1

            # 清理过期刷新令牌
            async def cleanup_refresh_key(key: str):
                nonlocal cleaned_refresh_tokens
                if key.startswith("refresh_token:"):
                    # Redis TTL会自动处理过期，这里只是统计
                    ttl = await redis.ttl(key)
                    if ttl <= 0:  # 已过期
                        cleaned_refresh_tokens += 1

            # 执行清理
            await scan_and_cleanup("session:*", cleanup_session_key)
            await scan_and_cleanup("refresh_token:*", cleanup_refresh_key)

            result = {
                "cleaned_sessions": cleaned_sessions,
                "cleaned_refresh_tokens": cleaned_refresh_tokens,
                "cleanup_time": datetime.now(timezone.utc).isoformat()
            }

            await self.log_operation(
                "session_cleanup_completed",
                result
            )

            return result

        except Exception as e:
            error = await self.handle_error(e, "cleanup_expired_sessions")
            raise error

    async def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息

        Returns:
            会话统计信息字典
        """
        try:
            redis = await self.redis

            # 统计活跃会话
            active_sessions = 0
            total_sessions = 0
            users_with_sessions = set()

            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="session:*", count=100)

                for key_bytes in keys:
                    total_sessions += 1
                    key = key_bytes.decode() if isinstance(key_bytes, bytes) else key_bytes
                    session_id = key.replace("session:", "")
                    session_data = await self.get_session(session_id)

                    if session_data and not session_data.is_expired():
                        active_sessions += 1
                        users_with_sessions.add(session_data.user_id)

                if cursor == 0:
                    break

            # 统计刷新令牌
            refresh_tokens = 0
            cursor = 0
            while True:
                cursor, keys = await redis.redis.scan(cursor, match="refresh_token:*", count=100)
                refresh_tokens += len(keys)

                if cursor == 0:
                    break

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": total_sessions - active_sessions,
                "unique_users": len(users_with_sessions),
                "refresh_tokens": refresh_tokens,
                "average_sessions_per_user": (
                    active_sessions / len(users_with_sessions)
                    if users_with_sessions else 0
                )
            }

        except Exception as e:
            error = await self.handle_error(e, "get_session_statistics")
            raise error

    async def _update_session(self, session_data: SessionData) -> None:
        """更新会话数据到Redis"""
        redis = await self.redis
        session_key = f"session:{session_data.session_id}"
        session_json = json.dumps(session_data.to_dict())

        # 计算剩余过期时间
        remaining_seconds = int((session_data.expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining_seconds > 0:
            await redis.set(session_key, session_json, ex=remaining_seconds)

    async def _cleanup_session(self, session_id: str) -> None:
        """清理单个会话"""
        redis = await self.redis
        session_key = f"session:{session_id}"

        # 获取会话数据以获取用户ID
        session_json = await redis.get(session_key)
        if session_json:
            try:
                session_data_dict = json.loads(session_json.decode())
                user_id = session_data_dict.get("user_id")

                # 从用户会话列表中移除
                if user_id:
                    user_sessions_key = f"user_sessions:{user_id}"
                    await redis.srem(user_sessions_key, session_id)
            except Exception as e:
                self.logger.error(f"Error parsing session data during cleanup: {e}")

        # 删除会话
        await redis.delete(session_key)

    async def _cleanup_user_sessions(self, user_id: str) -> None:
        """清理用户过多的会话"""
        try:
            redis = await self.redis
            user_sessions_key = f"user_sessions:{user_id}"

            session_ids = await redis.smembers(user_sessions_key)
            if len(session_ids) <= self.max_sessions_per_user:
                return

            # 获取所有会话的详细信息
            sessions_with_data = []
            for session_id_bytes in session_ids:
                session_id = session_id_bytes.decode()
                session_data = await self.get_session(session_id)
                if session_data:
                    sessions_with_data.append((session_id, session_data))

            # 按最后访问时间排序，保留最新的会话
            sessions_with_data.sort(key=lambda x: x[1].last_accessed, reverse=True)

            # 删除多余的会话
            sessions_to_remove = sessions_with_data[self.max_sessions_per_user:]
            for session_id, _ in sessions_to_remove:
                await self._cleanup_session(session_id)

            await self.log_operation(
                "user_sessions_limited",
                {"user_id": user_id, "removed_count": len(sessions_to_remove)}
            )

        except Exception as e:
            self.logger.error(f"Error cleaning up user sessions for {user_id}: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """会话服务健康检查"""
        health_info = {
            "service": self.service_name,
            "status": "unknown",
            "redis_connection": False,
            "jwt_handler_status": False,
            "active_sessions": 0,
            "error": None
        }

        try:
            # 测试Redis连接
            redis = await self.redis
            await redis.redis.ping()
            health_info["redis_connection"] = True

            # 测试JWT处理器
            jwt_handler = await self.jwt_handler
            test_tokens = jwt_handler.generate_tokens("test_user", "test", ["user"])
            if test_tokens and "access_token" in test_tokens:
                health_info["jwt_handler_status"] = True

            # 获取活跃会话统计
            stats = await self.get_session_statistics()
            health_info["active_sessions"] = stats.get("active_sessions", 0)

            health_info["status"] = "healthy"

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            self.logger.error(f"Health check failed for {self.service_name}: {e}")

        return health_info


# 全局会话服务实例
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """获取会话服务实例（单例模式）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service