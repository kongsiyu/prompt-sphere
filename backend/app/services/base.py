"""基础服务类定义和服务层架构。

该模块提供：
- 基础服务类和依赖注入模式
- 业务逻辑分离和错误处理策略
- 服务间通信接口定义
- 异步操作和事务管理
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Callable, Union
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.cache import CacheManager, get_cache
from app.core.redis import RedisClient, get_redis_client
from database.session import DatabaseSession, get_session, get_transaction

# 配置日志
logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar('T')
ServiceType = TypeVar('ServiceType', bound='BaseService')


class ServiceError(Exception):
    """服务层基础异常类。"""

    def __init__(self, message: str, code: str = "SERVICE_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)


class ValidationError(ServiceError):
    """输入验证错误。"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(ServiceError):
    """资源未找到错误。"""

    def __init__(self, resource: str, identifier: Union[str, int], details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, "NOT_FOUND", details)
        self.resource = resource
        self.identifier = identifier


class ConflictError(ServiceError):
    """资源冲突错误。"""

    def __init__(self, message: str, resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFLICT", details)
        self.resource = resource


class BaseService(ABC):
    """
    基础服务类，提供通用的服务层功能。

    特性：
    - 数据库会话管理
    - 缓存集成
    - 错误处理和日志记录
    - 事务支持
    - 异步操作
    """

    def __init__(
        self,
        cache_namespace: Optional[str] = None,
        enable_caching: bool = True,
        default_cache_ttl: int = 3600
    ):
        """
        初始化基础服务。

        Args:
            cache_namespace: 缓存命名空间
            enable_caching: 是否启用缓存
            default_cache_ttl: 默认缓存TTL（秒）
        """
        self.service_name = self.__class__.__name__
        self.cache_namespace = cache_namespace or self.service_name.lower()
        self.enable_caching = enable_caching
        self.default_cache_ttl = default_cache_ttl

        # 缓存和Redis客户端
        self._cache: Optional[CacheManager] = None
        self._redis: Optional[RedisClient] = None

        # 日志记录器
        self.logger = logging.getLogger(f"services.{self.service_name}")

        self.logger.info(f"Initialized {self.service_name} service")

    @property
    async def cache(self) -> CacheManager:
        """获取缓存管理器实例。"""
        if self._cache is None:
            self._cache = get_cache(namespace=self.cache_namespace)
        return self._cache

    @property
    async def redis(self) -> RedisClient:
        """获取Redis客户端实例。"""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def log_operation(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> None:
        """
        记录服务操作日志。

        Args:
            operation: 操作名称
            details: 操作详情
            level: 日志级别
        """
        log_data = {
            "service": self.service_name,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(details or {})
        }

        getattr(self.logger, level)(f"{operation}", extra=log_data)

    async def handle_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ServiceError:
        """
        统一错误处理。

        Args:
            error: 原始异常
            operation: 操作名称
            context: 错误上下文

        Returns:
            ServiceError: 包装后的服务错误
        """
        error_context = {
            "service": self.service_name,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {})
        }

        # 数据库错误处理
        if isinstance(error, SQLAlchemyError):
            self.logger.error("Database error occurred", extra=error_context)
            return ServiceError(
                f"Database operation failed: {operation}",
                code="DATABASE_ERROR",
                details=error_context
            )

        # 服务错误直接返回
        if isinstance(error, ServiceError):
            self.logger.error("Service error occurred", extra=error_context)
            return error

        # 其他未知错误
        self.logger.error("Unexpected error occurred", extra=error_context, exc_info=True)
        return ServiceError(
            f"Unexpected error in {operation}",
            code="INTERNAL_ERROR",
            details=error_context
        )

    @asynccontextmanager
    async def with_session(self):
        """提供数据库会话上下文管理器。"""
        async with get_session() as session:
            try:
                yield session
            except Exception as e:
                await self.log_operation(
                    "session_error",
                    {"error": str(e)},
                    level="error"
                )
                raise

    @asynccontextmanager
    async def with_transaction(self):
        """提供事务上下文管理器。"""
        async with get_transaction() as session:
            try:
                await self.log_operation("transaction_started")
                yield session
                await self.log_operation("transaction_committed")
            except Exception as e:
                await self.log_operation(
                    "transaction_rollback",
                    {"error": str(e)},
                    level="error"
                )
                raise

    async def cache_get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        从缓存获取数据。

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存的值或默认值
        """
        if not self.enable_caching:
            return default

        try:
            cache = await self.cache
            return await cache.get(key, default)
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {key}: {e}")
            return default

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据。

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否设置成功
        """
        if not self.enable_caching:
            return False

        try:
            cache = await self.cache
            return await cache.set(key, value, ttl=ttl or self.default_cache_ttl)
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    async def cache_delete(self, *keys: str) -> int:
        """
        删除缓存键。

        Args:
            keys: 要删除的缓存键

        Returns:
            删除的键数量
        """
        if not self.enable_caching:
            return 0

        try:
            cache = await self.cache
            return await cache.delete(*keys)
        except Exception as e:
            self.logger.warning(f"Cache delete failed for keys {keys}: {e}")
            return 0

    async def cache_get_or_set(
        self,
        key: str,
        default_func: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        获取缓存或设置新值。

        Args:
            key: 缓存键
            default_func: 生成默认值的函数
            ttl: 过期时间（秒）

        Returns:
            缓存的值或新生成的值
        """
        if not self.enable_caching:
            if callable(default_func):
                if hasattr(default_func, '__await__'):
                    return await default_func()
                else:
                    return default_func()
            return default_func

        try:
            cache = await self.cache
            return await cache.get_or_set(
                key,
                default_func,
                ttl=ttl or self.default_cache_ttl
            )
        except Exception as e:
            self.logger.warning(f"Cache get_or_set failed for key {key}: {e}")
            if callable(default_func):
                if hasattr(default_func, '__await__'):
                    return await default_func()
                else:
                    return default_func()
            return default_func

    async def validate_input(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入数据验证。

        Args:
            data: 输入数据
            rules: 验证规则

        Returns:
            验证后的数据

        Raises:
            ValidationError: 验证失败时抛出
        """
        validated_data = {}
        errors = []

        for field, rule in rules.items():
            value = data.get(field)

            # 必填字段检查
            if rule.get("required", False) and value is None:
                errors.append(f"Field '{field}' is required")
                continue

            # 类型检查
            if value is not None and "type" in rule:
                expected_type = rule["type"]
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                    continue

            # 长度检查
            if value is not None and "min_length" in rule:
                if hasattr(value, "__len__") and len(value) < rule["min_length"]:
                    errors.append(f"Field '{field}' must be at least {rule['min_length']} characters")
                    continue

            if value is not None and "max_length" in rule:
                if hasattr(value, "__len__") and len(value) > rule["max_length"]:
                    errors.append(f"Field '{field}' must be at most {rule['max_length']} characters")
                    continue

            # 自定义验证器
            if value is not None and "validator" in rule:
                validator = rule["validator"]
                if callable(validator):
                    try:
                        if asyncio.iscoroutinefunction(validator):
                            is_valid = await validator(value)
                        else:
                            is_valid = validator(value)

                        if not is_valid:
                            errors.append(f"Field '{field}' failed validation")
                            continue
                    except Exception as e:
                        errors.append(f"Field '{field}' validation error: {str(e)}")
                        continue

            validated_data[field] = value

        if errors:
            raise ValidationError(
                "Input validation failed",
                details={"errors": errors, "input_data": data}
            )

        return validated_data

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        服务健康检查。

        Returns:
            健康状态信息
        """
        pass


class CRUDService(BaseService, Generic[T]):
    """
    通用CRUD服务基类。

    提供标准的创建、读取、更新、删除操作。
    """

    def __init__(
        self,
        model_class: Type[T],
        cache_namespace: Optional[str] = None,
        enable_caching: bool = True,
        default_cache_ttl: int = 3600
    ):
        """
        初始化CRUD服务。

        Args:
            model_class: 数据模型类
            cache_namespace: 缓存命名空间
            enable_caching: 是否启用缓存
            default_cache_ttl: 默认缓存TTL
        """
        super().__init__(cache_namespace, enable_caching, default_cache_ttl)
        self.model_class = model_class
        self.model_name = model_class.__name__.lower()

    async def create(self, data: Dict[str, Any]) -> T:
        """
        创建新记录。

        Args:
            data: 创建数据

        Returns:
            创建的记录

        Raises:
            ServiceError: 创建失败时抛出
        """
        try:
            async with self.with_transaction() as db:
                # 验证输入数据
                validated_data = await self.validate_create_data(data)

                # 创建新实例
                instance = self.model_class(**validated_data)
                db.session.add(instance)
                await db.session.flush()  # 获取ID

                # 记录操作日志
                await self.log_operation(
                    f"create_{self.model_name}",
                    {"instance_id": getattr(instance, "id", None)}
                )

                return instance

        except Exception as e:
            error = await self.handle_error(e, f"create_{self.model_name}", {"data": data})
            raise error

    async def get_by_id(self, id: Union[str, int]) -> Optional[T]:
        """
        根据ID获取记录。

        Args:
            id: 记录ID

        Returns:
            记录实例或None
        """
        cache_key = f"{self.model_name}:id:{id}"

        # 尝试从缓存获取
        cached_result = await self.cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            async with self.with_session() as db:
                result = await db.session.get(self.model_class, id)

                # 缓存结果
                if result:
                    await self.cache_set(cache_key, result)

                return result

        except Exception as e:
            error = await self.handle_error(e, f"get_{self.model_name}_by_id", {"id": id})
            raise error

    async def update(self, id: Union[str, int], data: Dict[str, Any]) -> Optional[T]:
        """
        更新记录。

        Args:
            id: 记录ID
            data: 更新数据

        Returns:
            更新后的记录或None

        Raises:
            NotFoundError: 记录不存在时抛出
            ServiceError: 更新失败时抛出
        """
        try:
            async with self.with_transaction() as db:
                # 获取现有记录
                instance = await db.session.get(self.model_class, id)
                if not instance:
                    raise NotFoundError(self.model_name, id)

                # 验证更新数据
                validated_data = await self.validate_update_data(data, instance)

                # 更新字段
                for key, value in validated_data.items():
                    setattr(instance, key, value)

                await db.session.flush()

                # 清除缓存
                cache_key = f"{self.model_name}:id:{id}"
                await self.cache_delete(cache_key)

                # 记录操作日志
                await self.log_operation(
                    f"update_{self.model_name}",
                    {"instance_id": id, "updated_fields": list(validated_data.keys())}
                )

                return instance

        except Exception as e:
            error = await self.handle_error(e, f"update_{self.model_name}", {"id": id, "data": data})
            raise error

    async def delete(self, id: Union[str, int]) -> bool:
        """
        删除记录。

        Args:
            id: 记录ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 记录不存在时抛出
            ServiceError: 删除失败时抛出
        """
        try:
            async with self.with_transaction() as db:
                # 获取现有记录
                instance = await db.session.get(self.model_class, id)
                if not instance:
                    raise NotFoundError(self.model_name, id)

                # 软删除或硬删除
                if hasattr(instance, "is_deleted"):
                    instance.is_deleted = True
                else:
                    await db.session.delete(instance)

                await db.session.flush()

                # 清除缓存
                cache_key = f"{self.model_name}:id:{id}"
                await self.cache_delete(cache_key)

                # 记录操作日志
                await self.log_operation(
                    f"delete_{self.model_name}",
                    {"instance_id": id}
                )

                return True

        except Exception as e:
            error = await self.handle_error(e, f"delete_{self.model_name}", {"id": id})
            raise error

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        获取记录列表。

        Args:
            limit: 返回记录数量限制
            offset: 偏移量
            filters: 过滤条件
            order_by: 排序字段

        Returns:
            记录列表
        """
        try:
            async with self.with_session() as db:
                # 构建查询
                query = db.session.query(self.model_class)

                # 应用过滤器
                if filters:
                    query = await self.apply_filters(query, filters)

                # 应用排序
                if order_by:
                    query = await self.apply_ordering(query, order_by)

                # 应用分页
                query = query.offset(offset).limit(limit)

                # 执行查询
                result = await query.all()

                return result

        except Exception as e:
            error = await self.handle_error(
                e,
                f"list_{self.model_name}",
                {"limit": limit, "offset": offset, "filters": filters}
            )
            raise error

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        获取记录总数。

        Args:
            filters: 过滤条件

        Returns:
            记录总数
        """
        try:
            async with self.with_session() as db:
                # 构建计数查询
                query = db.session.query(self.model_class)

                # 应用过滤器
                if filters:
                    query = await self.apply_filters(query, filters)

                # 执行计数
                count = await query.count()

                return count

        except Exception as e:
            error = await self.handle_error(
                e,
                f"count_{self.model_name}",
                {"filters": filters}
            )
            raise error

    # 抽象方法，子类需要实现
    async def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证创建数据。"""
        return data

    async def validate_update_data(self, data: Dict[str, Any], instance: T) -> Dict[str, Any]:
        """验证更新数据。"""
        return data

    async def apply_filters(self, query, filters: Dict[str, Any]):
        """应用查询过滤器。"""
        return query

    async def apply_ordering(self, query, order_by: str):
        """应用查询排序。"""
        return query

    async def health_check(self) -> Dict[str, Any]:
        """CRUD服务健康检查。"""
        health_info = {
            "service": self.service_name,
            "model": self.model_name,
            "status": "unknown",
            "database_connection": False,
            "cache_connection": False,
            "error": None
        }

        try:
            # 测试数据库连接
            async with self.with_session() as db:
                await db.session.execute("SELECT 1")
                health_info["database_connection"] = True

            # 测试缓存连接
            if self.enable_caching:
                cache = await self.cache
                test_key = f"health_check:{self.service_name}"
                await cache.set(test_key, "test", ttl=10)
                await cache.get(test_key)
                await cache.delete(test_key)
                health_info["cache_connection"] = True
            else:
                health_info["cache_connection"] = "disabled"

            health_info["status"] = "healthy"

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            self.logger.error(f"Health check failed for {self.service_name}: {e}")

        return health_info


# 服务注册表
_service_registry: Dict[str, BaseService] = {}


def register_service(name: str, service: BaseService) -> None:
    """注册服务实例。"""
    _service_registry[name] = service
    logger.info(f"Registered service: {name}")


def get_service(name: str) -> Optional[BaseService]:
    """获取已注册的服务实例。"""
    return _service_registry.get(name)


def list_services() -> List[str]:
    """获取所有已注册的服务名称。"""
    return list(_service_registry.keys())


async def health_check_all_services() -> Dict[str, Any]:
    """
    检查所有注册服务的健康状态。

    Returns:
        所有服务的健康状态信息
    """
    health_results = {
        "overall_status": "healthy",
        "total_services": len(_service_registry),
        "healthy_services": 0,
        "unhealthy_services": 0,
        "services": {}
    }

    for name, service in _service_registry.items():
        try:
            service_health = await service.health_check()
            health_results["services"][name] = service_health

            if service_health.get("status") == "healthy":
                health_results["healthy_services"] += 1
            else:
                health_results["unhealthy_services"] += 1
                health_results["overall_status"] = "degraded"

        except Exception as e:
            health_results["services"][name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_results["unhealthy_services"] += 1
            health_results["overall_status"] = "degraded"

    if health_results["unhealthy_services"] == health_results["total_services"]:
        health_results["overall_status"] = "unhealthy"

    return health_results