"""令牌管理器实现，负责令牌的存储、验证、撤销和清理"""
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any

import aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_jwt_handler, JWTPayload
from app.core.redis import get_redis_client
from app.core.security import get_security_manager
from app.models.tokens import (
    UserTokenModel,
    TokenInfo,
    TokenType,
    TokenStatus,
    TokenBlacklistEntry,
    UserSession,
    LoginAttempt,
    SecurityEvent,
    TokenMetrics,
    CleanupResult
)

logger = logging.getLogger(__name__)


class TokenManager:
    """令牌管理器，提供完整的令牌生命周期管理"""

    def __init__(self):
        self.jwt_handler = get_jwt_handler()
        self.security_manager = get_security_manager()
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """获取Redis客户端"""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    def _generate_token_hash(self, token: str) -> str:
        """生成令牌哈希"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_tokens(
        self,
        user_id: str,
        username: str,
        roles: List[str] = None,
        client_info: Dict[str, Any] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, str]:
        """创建访问令牌和刷新令牌"""
        if roles is None:
            roles = []

        try:
            # 使用JWT处理器生成令牌
            token_data = self.jwt_handler.generate_tokens(user_id, username, roles)

            # 存储令牌信息到Redis
            await self._store_token_in_redis(
                token_data["access_jti"],
                user_id,
                TokenType.ACCESS,
                900,  # 15分钟
                roles,
                client_info
            )

            await self._store_token_in_redis(
                token_data["refresh_jti"],
                user_id,
                TokenType.REFRESH,
                604800,  # 7天
                roles,
                client_info
            )

            # 如果提供了数据库会话，存储到数据库
            if session:
                await self._store_tokens_in_db(
                    session,
                    token_data,
                    user_id,
                    client_info
                )

            return token_data

        except Exception as e:
            logger.error(f"Failed to create tokens for user {user_id}: {e}")
            raise RuntimeError("Failed to create authentication tokens")

    async def _store_token_in_redis(
        self,
        jti: str,
        user_id: str,
        token_type: TokenType,
        expires_in: int,
        roles: List[str] = None,
        client_info: Dict[str, Any] = None
    ) -> None:
        """在Redis中存储令牌信息"""
        try:
            redis = await self._get_redis()

            token_data = {
                "user_id": user_id,
                "token_type": token_type.value,
                "roles": roles or [],
                "created_at": datetime.utcnow().isoformat(),
                "client_info": client_info or {}
            }

            # 存储令牌数据
            key = f"token:{jti}"
            await redis.setex(key, expires_in, json.dumps(token_data))

            # 添加到用户令牌集合
            user_tokens_key = f"user_tokens:{user_id}"
            await redis.sadd(user_tokens_key, jti)
            await redis.expire(user_tokens_key, expires_in)

            # 添加到类型索引
            type_key = f"tokens_by_type:{token_type.value}"
            await redis.sadd(type_key, jti)
            await redis.expire(type_key, expires_in)

        except Exception as e:
            logger.error(f"Failed to store token in Redis: {e}")
            raise

    async def _store_tokens_in_db(
        self,
        session: AsyncSession,
        token_data: Dict[str, str],
        user_id: str,
        client_info: Dict[str, Any] = None
    ) -> None:
        """在数据库中存储令牌信息"""
        try:
            now = datetime.utcnow()

            # 存储访问令牌记录
            access_token = UserTokenModel(
                jti=token_data["access_jti"],
                user_id=user_id,
                token_type=TokenType.ACCESS.value,
                token_hash=self._generate_token_hash(token_data["access_token"]),
                expires_at=now + timedelta(minutes=15),
                issued_at=now,
                status=TokenStatus.ACTIVE.value,
                client_info=json.dumps(client_info) if client_info else None
            )

            # 存储刷新令牌记录
            refresh_token = UserTokenModel(
                jti=token_data["refresh_jti"],
                user_id=user_id,
                token_type=TokenType.REFRESH.value,
                token_hash=self._generate_token_hash(token_data["refresh_token"]),
                expires_at=now + timedelta(days=7),
                issued_at=now,
                status=TokenStatus.ACTIVE.value,
                client_info=json.dumps(client_info) if client_info else None
            )

            session.add_all([access_token, refresh_token])
            await session.commit()

        except Exception as e:
            logger.error(f"Failed to store tokens in database: {e}")
            await session.rollback()
            raise

    async def verify_token(self, token: str) -> Optional[JWTPayload]:
        """验证令牌"""
        try:
            # 首先使用JWT处理器验证令牌格式和签名
            payload = self.jwt_handler.verify_token(token)
            if not payload:
                return None

            # 检查令牌是否在黑名单中
            if await self._is_token_blacklisted(payload.jti):
                logger.debug(f"Token {payload.jti} is blacklisted")
                return None

            # 检查Redis中的令牌状态
            redis = await self._get_redis()
            token_key = f"token:{payload.jti}"
            token_data = await redis.get(token_key)

            if not token_data:
                logger.debug(f"Token {payload.jti} not found in Redis")
                return None

            # 更新最后使用时间
            await self._update_token_last_used(payload.jti)

            return payload

        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """刷新访问令牌"""
        try:
            # 验证刷新令牌
            payload = await self.verify_token(refresh_token)
            if not payload or payload.scope != "refresh":
                return None

            # 生成新的访问令牌
            new_token_data = self.jwt_handler.refresh_access_token(refresh_token)
            if not new_token_data:
                return None

            # 存储新令牌信息到Redis
            await self._store_token_in_redis(
                new_token_data["access_jti"],
                payload.user_id,
                TokenType.ACCESS,
                900,  # 15分钟
                payload.roles
            )

            return new_token_data

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    async def revoke_token(self, token: str, reason: str = None) -> bool:
        """撤销令牌"""
        try:
            # 获取令牌信息
            payload = self.jwt_handler.get_token_claims(token)
            if not payload:
                return False

            jti = payload.get("jti")
            if not jti:
                return False

            # 添加到黑名单
            await self._add_to_blacklist(jti, payload.get("user_id"), token, reason)

            # 从Redis中删除令牌
            redis = await self._get_redis()
            await redis.delete(f"token:{jti}")

            # 从用户令牌集合中移除
            user_id = payload.get("user_id")
            if user_id:
                await redis.srem(f"user_tokens:{user_id}", jti)

            # 记录安全事件
            await self._record_security_event(
                "token_revoked",
                user_id,
                {"jti": jti, "reason": reason}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def revoke_all_user_tokens(self, user_id: str, reason: str = None) -> int:
        """撤销用户的所有令牌"""
        try:
            redis = await self._get_redis()
            user_tokens_key = f"user_tokens:{user_id}"

            # 获取用户的所有令牌
            token_jtis = await redis.smembers(user_tokens_key)
            revoked_count = 0

            for jti in token_jtis:
                if isinstance(jti, bytes):
                    jti = jti.decode()

                # 获取令牌数据
                token_data = await redis.get(f"token:{jti}")
                if token_data:
                    # 添加到黑名单
                    await self._add_to_blacklist(jti, user_id, "", reason)

                    # 删除令牌
                    await redis.delete(f"token:{jti}")
                    revoked_count += 1

            # 清空用户令牌集合
            await redis.delete(user_tokens_key)

            # 记录安全事件
            await self._record_security_event(
                "all_tokens_revoked",
                user_id,
                {"revoked_count": revoked_count, "reason": reason}
            )

            return revoked_count

        except Exception as e:
            logger.error(f"Failed to revoke all tokens for user {user_id}: {e}")
            return 0

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            redis = await self._get_redis()
            return await redis.exists(f"blacklist:{jti}")
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return True  # 默认认为在黑名单中以确保安全

    async def _add_to_blacklist(
        self,
        jti: str,
        user_id: str,
        token: str,
        reason: str = None
    ) -> None:
        """添加令牌到黑名单"""
        try:
            redis = await self._get_redis()

            blacklist_data = {
                "user_id": user_id,
                "token_hash": self._generate_token_hash(token) if token else "",
                "blacklisted_at": datetime.utcnow().isoformat(),
                "reason": reason or "manual_revocation"
            }

            # 添加到黑名单，过期时间为原令牌的剩余时间
            key = f"blacklist:{jti}"
            await redis.setex(key, 604800, json.dumps(blacklist_data))  # 默认7天

        except Exception as e:
            logger.error(f"Failed to add token to blacklist: {e}")
            raise

    async def _update_token_last_used(self, jti: str) -> None:
        """更新令牌最后使用时间"""
        try:
            redis = await self._get_redis()
            key = f"token_last_used:{jti}"
            await redis.setex(key, 900, datetime.utcnow().isoformat())  # 15分钟过期
        except Exception as e:
            logger.debug(f"Failed to update token last used time: {e}")

    async def _record_security_event(
        self,
        event_type: str,
        user_id: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """记录安全事件"""
        try:
            redis = await self._get_redis()

            event = SecurityEvent(
                event_id=str(__import__('uuid').uuid4()),
                event_type=event_type,
                user_id=user_id,
                details=details
            )

            # 存储事件
            key = f"security_event:{event.event_id}"
            await redis.setex(key, 2592000, event.json())  # 30天过期

            # 添加到事件列表
            list_key = f"security_events:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await redis.lpush(list_key, event.event_id)
            await redis.expire(list_key, 2592000)

        except Exception as e:
            logger.error(f"Failed to record security event: {e}")

    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """获取用户的活跃会话"""
        try:
            redis = await self._get_redis()
            user_tokens_key = f"user_tokens:{user_id}"

            # 获取用户的所有令牌
            token_jtis = await redis.smembers(user_tokens_key)
            sessions = []

            for jti in token_jtis:
                if isinstance(jti, bytes):
                    jti = jti.decode()

                token_data_str = await redis.get(f"token:{jti}")
                if token_data_str:
                    token_data = json.loads(token_data_str)

                    # 只处理访问令牌
                    if token_data.get("token_type") == TokenType.ACCESS.value:
                        session = UserSession(
                            session_id=jti,
                            user_id=user_id,
                            username=token_data.get("username", ""),
                            roles=token_data.get("roles", []),
                            login_time=datetime.fromisoformat(token_data.get("created_at")),
                            ip_address=token_data.get("client_info", {}).get("ip_address"),
                            user_agent=token_data.get("client_info", {}).get("user_agent")
                        )
                        sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []

    async def cleanup_expired_tokens(self) -> CleanupResult:
        """清理过期的令牌和相关数据"""
        start_time = datetime.utcnow()
        result = CleanupResult()

        try:
            redis = await self._get_redis()

            # Redis会自动清理过期的键，这里主要做一些额外的清理工作

            # 清理过期的安全事件
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            for days_ago in range(31, 90):  # 清理31-90天前的事件
                date_str = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                list_key = f"security_events:{date_str}"

                # 获取事件列表
                event_ids = await redis.lrange(list_key, 0, -1)
                for event_id in event_ids:
                    if isinstance(event_id, bytes):
                        event_id = event_id.decode()
                    await redis.delete(f"security_event:{event_id}")
                    result.cleaned_events += 1

                await redis.delete(list_key)

            operation_time = (datetime.utcnow() - start_time).total_seconds()
            result.operation_time = operation_time

            logger.info(f"Token cleanup completed: {result.dict()}")
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return result

    async def get_token_metrics(self) -> TokenMetrics:
        """获取令牌统计指标"""
        try:
            redis = await self._get_redis()
            metrics = TokenMetrics()

            # 获取所有令牌类型的统计
            for token_type in TokenType:
                type_key = f"tokens_by_type:{token_type.value}"
                count = await redis.scard(type_key)
                metrics.tokens_by_type[token_type.value] = count
                metrics.total_tokens += count

            # 活跃令牌数量等于总令牌数量（Redis中的都是活跃的）
            metrics.active_tokens = metrics.total_tokens

            return metrics

        except Exception as e:
            logger.error(f"Failed to get token metrics: {e}")
            return TokenMetrics()


# 全局令牌管理器实例
_token_manager: Optional[TokenManager] = None


async def get_token_manager() -> TokenManager:
    """获取令牌管理器实例（单例模式）"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager