"""依赖注入测试。

测试内容：
- 数据库会话依赖注入
- Redis客户端依赖注入
- 缓存管理器依赖注入
- 服务层依赖注入
- 认证和授权依赖注入
- 健康检查依赖注入
- 请求上下文依赖注入
- 分页参数依赖注入
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from typing import Dict, Any, Optional

from app.core.dependencies import (
    get_app_settings,
    get_database_session,
    get_database_transaction,
    get_redis_dependency,
    get_cache_manager,
    get_session_cache_dependency,
    create_service_dependency,
    get_prompt_service,
    get_user_service,
    get_template_service,
    get_dashscope_service,
    CurrentUser,
    get_current_user,
    require_permissions,
    require_read_permission,
    require_write_permission,
    require_admin_permission,
    get_system_health,
    RequestContext,
    get_request_context,
    PaginationParams,
    get_pagination_params,
    create_filter_dependency,
    CacheDependency,
    get_cache_dependency
)
from app.core.config import Settings
from app.services.base import BaseService, register_service, _service_registry


@pytest.fixture
def mock_settings():
    """模拟应用设置。"""
    settings = MagicMock(spec=Settings)
    settings.debug = True
    settings.app_name = "Test App"
    settings.app_version = "1.0.0"
    settings.cors_origins = ["http://localhost:3000"]
    return settings


@pytest.fixture
def mock_db_session():
    """模拟数据库会话。"""
    session = AsyncMock()
    session.session = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端。"""
    client = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_cache_manager():
    """模拟缓存管理器。"""
    cache = AsyncMock()
    cache.namespace = "test"
    return cache


@pytest.fixture
def mock_service():
    """模拟服务实例。"""
    service = AsyncMock(spec=BaseService)
    service.service_name = "TestService"
    return service


@pytest.fixture(autouse=True)
def clear_service_registry():
    """每个测试前清空服务注册表。"""
    _service_registry.clear()
    yield
    _service_registry.clear()


class TestConfigDependencies:
    """配置依赖测试类。"""

    @patch('app.core.dependencies.get_settings')
    def test_get_app_settings(self, mock_get_settings, mock_settings):
        """测试获取应用设置。"""
        mock_get_settings.return_value = mock_settings

        result = get_app_settings()

        assert result == mock_settings
        mock_get_settings.assert_called_once()


class TestDatabaseDependencies:
    """数据库依赖测试类。"""

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_session')
    async def test_get_database_session_success(self, mock_get_session, mock_db_session):
        """测试成功获取数据库会话。"""
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        async with get_database_session() as session:
            assert session == mock_db_session

        mock_get_session.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_session')
    async def test_get_database_session_error(self, mock_get_session):
        """测试数据库会话获取失败。"""
        mock_get_session.side_effect = Exception("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            async with get_database_session() as session:
                pass

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database connection error" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_transaction')
    async def test_get_database_transaction_success(self, mock_get_transaction, mock_db_session):
        """测试成功获取数据库事务。"""
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        async with get_database_transaction() as session:
            assert session == mock_db_session

        mock_get_transaction.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_transaction')
    async def test_get_database_transaction_error(self, mock_get_transaction):
        """测试数据库事务获取失败。"""
        mock_get_transaction.side_effect = Exception("Transaction failed")

        with pytest.raises(HTTPException) as exc_info:
            async with get_database_transaction() as session:
                pass

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database transaction error" in exc_info.value.detail


class TestRedisCacheDependencies:
    """Redis和缓存依赖测试类。"""

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_redis_client')
    async def test_get_redis_dependency_success(self, mock_get_redis_client, mock_redis_client):
        """测试成功获取Redis客户端。"""
        mock_get_redis_client.return_value = mock_redis_client

        result = await get_redis_dependency()

        assert result == mock_redis_client
        mock_redis_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_redis_client')
    async def test_get_redis_dependency_unhealthy(self, mock_get_redis_client, mock_redis_client):
        """测试Redis客户端不健康。"""
        mock_redis_client.health_check.return_value = False
        mock_get_redis_client.return_value = mock_redis_client

        with pytest.raises(HTTPException) as exc_info:
            await get_redis_dependency()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Redis service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_redis_client')
    async def test_get_redis_dependency_error(self, mock_get_redis_client):
        """测试Redis客户端连接失败。"""
        mock_get_redis_client.side_effect = Exception("Redis connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_redis_dependency()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Redis service unavailable" in exc_info.value.detail

    @patch('app.core.dependencies.get_cache')
    def test_get_cache_manager(self, mock_get_cache, mock_cache_manager):
        """测试获取缓存管理器。"""
        mock_get_cache.return_value = mock_cache_manager

        result = get_cache_manager("test_namespace")

        assert result == mock_cache_manager
        mock_get_cache.assert_called_once_with(namespace="test_namespace")

    @patch('app.core.dependencies.get_session_cache')
    def test_get_session_cache_dependency(self, mock_get_session_cache):
        """测试获取会话缓存。"""
        mock_session_cache = MagicMock()
        mock_get_session_cache.return_value = mock_session_cache

        result = get_session_cache_dependency()

        assert result == mock_session_cache
        mock_get_session_cache.assert_called_once()


class TestServiceDependencies:
    """服务依赖测试类。"""

    def test_create_service_dependency_success(self, mock_service):
        """测试创建服务依赖成功。"""
        register_service("test_service", mock_service)

        dependency_func = create_service_dependency("test_service")
        result = dependency_func()

        assert result == mock_service

    def test_create_service_dependency_not_found(self):
        """测试服务未找到。"""
        dependency_func = create_service_dependency("non_existent_service")

        with pytest.raises(HTTPException) as exc_info:
            dependency_func()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "non_existent_service not available" in exc_info.value.detail

    def test_predefined_service_dependencies(self, mock_service):
        """测试预定义的服务依赖。"""
        # 注册各种服务
        register_service("prompt_service", mock_service)
        register_service("user_service", mock_service)
        register_service("template_service", mock_service)
        register_service("dashscope_service", mock_service)

        # 测试各个预定义依赖
        assert get_prompt_service() == mock_service
        assert get_user_service() == mock_service
        assert get_template_service() == mock_service
        assert get_dashscope_service() == mock_service


class TestAuthenticationDependencies:
    """认证依赖测试类。"""

    def test_current_user_permissions(self):
        """测试当前用户权限检查。"""
        user = CurrentUser(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            permissions=["read", "write"]
        )

        assert user.has_permission("read") is True
        assert user.has_permission("write") is True
        assert user.has_permission("admin") is False

        # 测试admin权限
        admin_user = CurrentUser(
            user_id="admin123",
            username="admin",
            email="admin@example.com",
            permissions=["admin"]
        )

        assert admin_user.has_permission("read") is True  # admin有所有权限
        assert admin_user.has_permission("admin") is True

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """测试获取当前用户（模拟实现）。"""
        # 目前返回模拟用户
        user = await get_current_user()

        assert isinstance(user, CurrentUser)
        assert user.user_id == "dev_user_001"
        assert user.username == "developer"
        assert "admin" in user.permissions

    def test_require_permissions_success(self):
        """测试权限检查成功。"""
        user = CurrentUser(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            permissions=["read", "write"]
        )

        check_func = require_permissions("read", "write")
        result = check_func(current_user=user)

        assert result == user

    def test_require_permissions_failure(self):
        """测试权限检查失败。"""
        user = CurrentUser(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            permissions=["read"]  # 缺少write权限
        )

        check_func = require_permissions("read", "write")

        with pytest.raises(HTTPException) as exc_info:
            check_func(current_user=user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Permission required: write" in exc_info.value.detail

    def test_require_permissions_no_user(self):
        """测试无用户时权限检查。"""
        check_func = require_permissions("read")

        with pytest.raises(HTTPException) as exc_info:
            check_func(current_user=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication required" in exc_info.value.detail

    def test_predefined_permission_checks(self):
        """测试预定义的权限检查。"""
        user = CurrentUser(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            permissions=["read", "write", "admin"]
        )

        # 测试各个预定义权限检查
        assert require_read_permission(current_user=user) == user
        assert require_write_permission(current_user=user) == user
        assert require_admin_permission(current_user=user) == user


class TestHealthDependencies:
    """健康检查依赖测试类。"""

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_session')
    @patch('app.core.dependencies.get_redis_client')
    @patch('app.core.dependencies.health_check_all_services')
    async def test_get_system_health_all_healthy(
        self,
        mock_health_check_services,
        mock_get_redis_client,
        mock_get_session,
        mock_db_session,
        mock_redis_client
    ):
        """测试系统健康检查 - 全部健康。"""
        # 模拟数据库健康
        mock_get_session.return_value.__aenter__.return_value = mock_db_session
        mock_db_session.session.execute = AsyncMock()

        # 模拟Redis健康
        mock_redis_client.health_check.return_value = True
        mock_get_redis_client.return_value = mock_redis_client

        # 模拟服务健康
        mock_health_check_services.return_value = {"overall_status": "healthy"}

        result = await get_system_health()

        assert result["status"] == "healthy"
        assert result["database"]["status"] == "healthy"
        assert result["redis"]["status"] == "healthy"
        assert result["services"]["overall_status"] == "healthy"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_session')
    @patch('app.core.dependencies.get_redis_client')
    async def test_get_system_health_database_unhealthy(
        self,
        mock_get_redis_client,
        mock_get_session,
        mock_redis_client
    ):
        """测试系统健康检查 - 数据库不健康。"""
        # 模拟数据库连接失败
        mock_get_session.side_effect = Exception("Database connection failed")

        # 模拟Redis健康
        mock_redis_client.health_check.return_value = True
        mock_get_redis_client.return_value = mock_redis_client

        result = await get_system_health()

        assert result["status"] in ["degraded", "unhealthy"]
        assert result["database"]["status"] == "unhealthy"
        assert "Database" in str(result["errors"])

    @pytest.mark.asyncio
    async def test_get_system_health_exception(self):
        """测试系统健康检查异常。"""
        with patch('app.core.dependencies.get_session', side_effect=Exception("Critical error")):
            result = await get_system_health()

            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Critical error" in result["error"]


class TestRequestContextDependencies:
    """请求上下文依赖测试类。"""

    @pytest.mark.asyncio
    async def test_get_request_context(self, mock_db_session, mock_cache_manager):
        """测试获取请求上下文。"""
        user = CurrentUser(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            permissions=["read"]
        )

        context = await get_request_context(
            user=user,
            db_session=mock_db_session,
            cache=mock_cache_manager
        )

        assert isinstance(context, RequestContext)
        assert context.user == user
        assert context.db_session == mock_db_session
        assert context.cache == mock_cache_manager
        assert context.request_id is not None


class TestPaginationDependencies:
    """分页依赖测试类。"""

    def test_get_pagination_params_default(self):
        """测试默认分页参数。"""
        params = get_pagination_params()

        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_get_pagination_params_custom(self):
        """测试自定义分页参数。"""
        params = get_pagination_params(page=3, size=50)

        assert params.page == 3
        assert params.size == 50
        assert params.offset == 100  # (3-1) * 50
        assert params.limit == 50

    def test_get_pagination_params_boundary_values(self):
        """测试边界值。"""
        # 测试负数和0
        params = get_pagination_params(page=0, size=-10)

        assert params.page == 1  # 最小为1
        assert params.size == 1  # 最小为1

        # 测试超大值
        params = get_pagination_params(page=999, size=1000)

        assert params.page == 999
        assert params.size == 100  # 最大为100


class TestFilterDependencies:
    """过滤器依赖测试类。"""

    def test_create_filter_dependency(self):
        """测试创建过滤器依赖。"""
        filter_func = create_filter_dependency("name", "status", "created_at")

        # 测试有值的过滤器
        filters = filter_func(name="test", status="active", invalid_field="ignored")

        assert filters == {"name": "test", "status": "active"}
        assert "invalid_field" not in filters

        # 测试None值过滤器
        filters = filter_func(name=None, status="active")

        assert filters == {"status": "active"}
        assert "name" not in filters


class TestCacheDependencies:
    """缓存依赖测试类。"""

    @pytest.mark.asyncio
    @patch('app.core.dependencies.get_cache')
    async def test_cache_dependency_operations(self, mock_get_cache, mock_cache_manager):
        """测试缓存依赖操作。"""
        mock_get_cache.return_value = mock_cache_manager
        mock_cache_manager.get.return_value = "cached_value"
        mock_cache_manager.set.return_value = True
        mock_cache_manager.delete.return_value = 1

        cache_dep = get_cache_dependency("test_namespace", ttl=1800)

        assert cache_dep.namespace == "test_namespace"
        assert cache_dep.ttl == 1800

        # 测试获取缓存
        cache = await cache_dep.get_cache()
        assert cache == mock_cache_manager
        mock_get_cache.assert_called_with(namespace="test_namespace")

        # 测试缓存操作
        value = await cache_dep.get("test_key", "default")
        assert value == "cached_value"

        result = await cache_dep.set("test_key", "test_value", ttl=3600)
        assert result is True

        count = await cache_dep.delete("test_key1", "test_key2")
        assert count == 1

    def test_cache_dependency_default_values(self):
        """测试缓存依赖默认值。"""
        cache_dep = get_cache_dependency()

        assert cache_dep.namespace == "api"
        assert cache_dep.ttl == 3600