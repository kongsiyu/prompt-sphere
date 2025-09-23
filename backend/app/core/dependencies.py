"""FastAPI依赖注入函数。

该模块提供：
- 数据库会话依赖注入
- Redis客户端依赖注入
- 缓存管理器依赖注入
- 服务层依赖注入
- 认证和授权依赖注入
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheManager, get_cache, get_session_cache, SessionCache
from app.core.redis import RedisClient, get_redis_client
from app.core.config import Settings, get_settings
from app.services.base import BaseService, get_service, health_check_all_services
from backend.database.session import DatabaseSession, get_session, get_transaction

# 配置日志
logger = logging.getLogger(__name__)


# === 配置依赖 ===

def get_app_settings() -> Settings:
    """获取应用配置依赖。"""
    return get_settings()


# === 数据库依赖 ===

async def get_database_session() -> AsyncGenerator[DatabaseSession, None]:
    """
    获取数据库会话依赖。

    Yields:
        DatabaseSession: 数据库会话实例
    """
    async with get_session() as session:
        try:
            logger.debug("Created database session for request")
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection error"
            ) from e


async def get_database_transaction() -> AsyncGenerator[DatabaseSession, None]:
    """
    获取数据库事务依赖。

    Yields:
        DatabaseSession: 数据库事务会话实例
    """
    async with get_transaction() as session:
        try:
            logger.debug("Created database transaction for request")
            yield session
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database transaction error"
            ) from e


# === Redis和缓存依赖 ===

async def get_redis_dependency() -> RedisClient:
    """
    获取Redis客户端依赖。

    Returns:
        RedisClient: Redis客户端实例
    """
    try:
        client = await get_redis_client()
        # 健康检查
        if not await client.health_check():
            logger.warning("Redis health check failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        return client
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        ) from e


def get_cache_manager(namespace: str = "default") -> CacheManager:
    """
    获取缓存管理器依赖。

    Args:
        namespace: 缓存命名空间

    Returns:
        CacheManager: 缓存管理器实例
    """
    return get_cache(namespace=namespace)


def get_session_cache_dependency() -> SessionCache:
    """
    获取会话缓存依赖。

    Returns:
        SessionCache: 会话缓存实例
    """
    return get_session_cache()


# === 服务层依赖 ===

def create_service_dependency(service_name: str):
    """
    创建服务依赖注入函数。

    Args:
        service_name: 服务名称

    Returns:
        服务依赖注入函数
    """
    def get_service_dependency() -> BaseService:
        """获取指定服务依赖。"""
        service = get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Service {service_name} not available"
            )
        return service

    return get_service_dependency


# 预定义常用服务依赖
def get_prompt_service() -> BaseService:
    """获取提示词服务依赖。"""
    return create_service_dependency("prompt_service")()


def get_user_service() -> BaseService:
    """获取用户服务依赖。"""
    return create_service_dependency("user_service")()


def get_template_service() -> BaseService:
    """获取模板服务依赖。"""
    return create_service_dependency("template_service")()


def get_dashscope_service() -> BaseService:
    """获取DashScope服务依赖。"""
    return create_service_dependency("dashscope_service")()


# === 认证和授权依赖 ===

class CurrentUser:
    """当前用户信息。"""

    def __init__(self, user_id: str, username: str, email: str, permissions: list[str]):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限。"""
        return permission in self.permissions or "admin" in self.permissions


async def get_current_user(
    # token: str = Depends(oauth2_scheme),  # JWT token依赖
    session_cache: SessionCache = Depends(get_session_cache_dependency)
) -> Optional[CurrentUser]:
    """
    获取当前用户依赖。

    Args:
        session_cache: 会话缓存

    Returns:
        CurrentUser: 当前用户信息

    Raises:
        HTTPException: 认证失败时抛出
    """
    # TODO: 实现JWT token解析和用户验证
    # 这里暂时返回模拟用户，实际项目中需要：
    # 1. 解析JWT token
    # 2. 验证token有效性
    # 3. 从数据库或缓存获取用户信息
    # 4. 检查用户状态（是否启用、是否过期等）

    # 模拟用户（开发环境）
    mock_user = CurrentUser(
        user_id="dev_user_001",
        username="developer",
        email="dev@example.com",
        permissions=["read", "write", "admin"]
    )

    logger.debug(f"Current user: {mock_user.username}")
    return mock_user


def require_permissions(*required_permissions: str):
    """
    权限检查装饰器依赖。

    Args:
        required_permissions: 必需的权限列表

    Returns:
        权限检查函数
    """
    def check_permissions(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        """检查用户权限。"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        for permission in required_permissions:
            if not current_user.has_permission(permission):
                logger.warning(
                    f"User {current_user.username} lacks permission: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )

        return current_user

    return check_permissions


# 预定义权限检查依赖
require_read_permission = require_permissions("read")
require_write_permission = require_permissions("write")
require_admin_permission = require_permissions("admin")


# === 健康检查依赖 ===

async def get_system_health() -> Dict[str, Any]:
    """
    获取系统健康状态依赖。

    Returns:
        系统健康状态信息
    """
    try:
        health_info = {
            "status": "healthy",
            "timestamp": None,
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "services": {"status": "unknown"},
            "errors": []
        }

        from datetime import datetime
        health_info["timestamp"] = datetime.utcnow().isoformat()

        # 检查数据库连接
        try:
            async with get_session() as db:
                await db.session.execute("SELECT 1")
                health_info["database"]["status"] = "healthy"
        except Exception as e:
            health_info["database"]["status"] = "unhealthy"
            health_info["database"]["error"] = str(e)
            health_info["errors"].append(f"Database: {str(e)}")
            health_info["status"] = "degraded"

        # 检查Redis连接
        try:
            redis = await get_redis_client()
            if await redis.health_check():
                health_info["redis"]["status"] = "healthy"
            else:
                health_info["redis"]["status"] = "unhealthy"
                health_info["errors"].append("Redis: Health check failed")
                health_info["status"] = "degraded"
        except Exception as e:
            health_info["redis"]["status"] = "unhealthy"
            health_info["redis"]["error"] = str(e)
            health_info["errors"].append(f"Redis: {str(e)}")
            health_info["status"] = "degraded"

        # 检查服务健康状态
        try:
            services_health = await health_check_all_services()
            health_info["services"] = services_health

            if services_health.get("overall_status") != "healthy":
                health_info["status"] = "degraded"
                health_info["errors"].append("Services: Some services are unhealthy")

        except Exception as e:
            health_info["services"]["status"] = "unhealthy"
            health_info["services"]["error"] = str(e)
            health_info["errors"].append(f"Services: {str(e)}")
            health_info["status"] = "degraded"

        # 如果有错误，状态为不健康
        if health_info["errors"]:
            if len(health_info["errors"]) >= 2:  # 多个组件失败
                health_info["status"] = "unhealthy"

        return health_info

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "errors": [f"System: {str(e)}"]
        }


# === 请求上下文依赖 ===

class RequestContext:
    """请求上下文信息。"""

    def __init__(
        self,
        request_id: str,
        user: Optional[CurrentUser] = None,
        db_session: Optional[DatabaseSession] = None,
        cache: Optional[CacheManager] = None
    ):
        self.request_id = request_id
        self.user = user
        self.db_session = db_session
        self.cache = cache


async def get_request_context(
    user: Optional[CurrentUser] = Depends(get_current_user),
    db_session: DatabaseSession = Depends(get_database_session),
    cache: CacheManager = Depends(lambda: get_cache_manager("request"))
) -> RequestContext:
    """
    获取请求上下文依赖。

    Args:
        user: 当前用户
        db_session: 数据库会话
        cache: 缓存管理器

    Returns:
        RequestContext: 请求上下文信息
    """
    import uuid
    request_id = str(uuid.uuid4())

    logger.debug(f"Created request context: {request_id}")

    return RequestContext(
        request_id=request_id,
        user=user,
        db_session=db_session,
        cache=cache
    )


# === 分页依赖 ===

class PaginationParams:
    """分页参数。"""

    def __init__(self, page: int = 1, size: int = 20, max_size: int = 100):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """
    获取分页参数依赖。

    Args:
        page: 页码（从1开始）
        size: 每页大小

    Returns:
        PaginationParams: 分页参数
    """
    return PaginationParams(page=page, size=size)


# === 查询过滤器依赖 ===

def create_filter_dependency(*allowed_fields: str):
    """
    创建查询过滤器依赖。

    Args:
        allowed_fields: 允许过滤的字段列表

    Returns:
        过滤器依赖函数
    """
    def get_filters(**kwargs) -> Dict[str, Any]:
        """获取查询过滤器。"""
        filters = {}
        for field in allowed_fields:
            value = kwargs.get(field)
            if value is not None:
                filters[field] = value
        return filters

    return get_filters


# === 缓存依赖封装 ===

class CacheDependency:
    """缓存依赖封装类。"""

    def __init__(self, namespace: str, ttl: int = 3600):
        self.namespace = namespace
        self.ttl = ttl
        self._cache = None

    async def get_cache(self) -> CacheManager:
        """获取缓存实例。"""
        if self._cache is None:
            self._cache = get_cache(namespace=self.namespace)
        return self._cache

    async def get(self, key: str, default=None):
        """获取缓存值。"""
        cache = await self.get_cache()
        return await cache.get(key, default)

    async def set(self, key: str, value, ttl: Optional[int] = None):
        """设置缓存值。"""
        cache = await self.get_cache()
        return await cache.set(key, value, ttl=ttl or self.ttl)

    async def delete(self, *keys: str):
        """删除缓存键。"""
        cache = await self.get_cache()
        return await cache.delete(*keys)


def get_cache_dependency(namespace: str = "api", ttl: int = 3600) -> CacheDependency:
    """
    获取缓存依赖。

    Args:
        namespace: 缓存命名空间
        ttl: 默认TTL

    Returns:
        CacheDependency: 缓存依赖实例
    """
    return CacheDependency(namespace=namespace, ttl=ttl)


# === 导出常用依赖 ===

__all__ = [
    # 配置
    "get_app_settings",
    # 数据库
    "get_database_session",
    "get_database_transaction",
    # Redis和缓存
    "get_redis_dependency",
    "get_cache_manager",
    "get_session_cache_dependency",
    "get_cache_dependency",
    # 服务
    "create_service_dependency",
    "get_prompt_service",
    "get_user_service",
    "get_template_service",
    "get_dashscope_service",
    # 认证授权
    "CurrentUser",
    "get_current_user",
    "require_permissions",
    "require_read_permission",
    "require_write_permission",
    "require_admin_permission",
    # 健康检查
    "get_system_health",
    # 请求上下文
    "RequestContext",
    "get_request_context",
    # 分页
    "PaginationParams",
    "get_pagination_params",
    # 过滤器
    "create_filter_dependency",
    # 缓存
    "CacheDependency",
]