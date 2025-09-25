"""服务基类测试。

测试内容：
- BaseService基础功能
- CRUDService通用CRUD操作
- 服务注册和获取机制
- 错误处理和日志记录
- 缓存集成测试
- 数据库事务测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.base import (
    BaseService,
    CRUDService,
    ServiceError,
    ValidationError,
    NotFoundError,
    ConflictError,
    register_service,
    get_service,
    list_services,
    health_check_all_services,
    _service_registry
)


# 测试模型类
class TestModel:
    """测试用的模型类。"""

    def __init__(self, id: int = None, name: str = None, description: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.is_deleted = False

    def __eq__(self, other):
        if not isinstance(other, TestModel):
            return False
        return self.id == other.id


# 测试服务类
class TestBaseService(BaseService):
    """测试用的基础服务类。"""

    def __init__(self, cache_namespace: str = "test", enable_caching: bool = True):
        super().__init__(cache_namespace=cache_namespace, enable_caching=enable_caching)

    async def health_check(self) -> Dict[str, Any]:
        """实现健康检查方法。"""
        return {
            "status": "healthy",
            "service": self.service_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class TestCRUDService(CRUDService[TestModel]):
    """测试用的CRUD服务类。"""

    def __init__(self):
        super().__init__(
            model_class=TestModel,
            cache_namespace="test_crud",
            enable_caching=True
        )

    async def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证创建数据。"""
        rules = {
            "name": {"required": True, "type": str, "min_length": 1, "max_length": 100},
            "description": {"type": str, "max_length": 500}
        }
        return await self.validate_input(data, rules)

    async def validate_update_data(self, data: Dict[str, Any], instance: TestModel) -> Dict[str, Any]:
        """验证更新数据。"""
        # 更新时name不是必需的
        rules = {
            "name": {"type": str, "min_length": 1, "max_length": 100},
            "description": {"type": str, "max_length": 500}
        }
        return await self.validate_input(data, rules)

    async def apply_filters(self, query, filters: Dict[str, Any]):
        """应用查询过滤器（模拟实现）。"""
        # 这里是模拟实现，实际中会根据SQLAlchemy查询进行过滤
        return query

    async def apply_ordering(self, query, order_by: str):
        """应用查询排序（模拟实现）。"""
        # 这里是模拟实现，实际中会根据SQLAlchemy查询进行排序
        return query


@pytest.fixture
def base_service():
    """创建测试用的基础服务实例。"""
    return TestBaseService(cache_namespace="test_base", enable_caching=True)


@pytest.fixture
def crud_service():
    """创建测试用的CRUD服务实例。"""
    return TestCRUDService()


@pytest.fixture
def mock_cache():
    """模拟缓存管理器。"""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=1)
    cache.exists = AsyncMock(return_value=False)
    cache.get_or_set = AsyncMock()
    return cache


@pytest.fixture
def mock_redis():
    """模拟Redis客户端。"""
    redis = AsyncMock()
    redis.health_check = AsyncMock(return_value=True)
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=b"test_value")
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture
def mock_db_session():
    """模拟数据库会话。"""
    session = AsyncMock()
    session.session = AsyncMock()
    session.session.get = AsyncMock()
    session.session.add = AsyncMock()
    session.session.delete = AsyncMock()
    session.session.flush = AsyncMock()
    session.session.query = AsyncMock()
    session.session.execute = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def clear_service_registry():
    """每个测试前清空服务注册表。"""
    _service_registry.clear()
    yield
    _service_registry.clear()


class TestBaseServiceClass:
    """BaseService测试类。"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, base_service):
        """测试服务初始化。"""
        assert base_service.service_name == "TestBaseService"
        assert base_service.cache_namespace == "test_base"
        assert base_service.enable_caching is True
        assert base_service.default_cache_ttl == 3600

    @pytest.mark.asyncio
    async def test_log_operation(self, base_service, caplog):
        """测试操作日志记录。"""
        await base_service.log_operation(
            "test_operation",
            {"param1": "value1", "param2": "value2"},
            level="info"
        )

        assert "test_operation" in caplog.text
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "INFO"

    @pytest.mark.asyncio
    async def test_handle_error(self, base_service):
        """测试错误处理。"""
        original_error = ValueError("Test error message")
        context = {"operation": "test_op", "data": {"key": "value"}}

        service_error = await base_service.handle_error(
            original_error,
            "test_operation",
            context
        )

        assert isinstance(service_error, ServiceError)
        assert "test_operation" in service_error.message
        assert service_error.code == "INTERNAL_ERROR"
        assert service_error.details["error_type"] == "ValueError"
        assert service_error.details["operation"] == "test_op"

    @pytest.mark.asyncio
    async def test_handle_service_error(self, base_service):
        """测试服务错误直接返回。"""
        original_error = ValidationError("Invalid input", field="name")

        service_error = await base_service.handle_error(
            original_error,
            "test_operation"
        )

        assert service_error is original_error
        assert service_error.code == "VALIDATION_ERROR"
        assert service_error.field == "name"

    @pytest.mark.asyncio
    async def test_validate_input_success(self, base_service):
        """测试输入验证成功。"""
        data = {
            "name": "Test Name",
            "email": "test@example.com",
            "age": 25
        }

        rules = {
            "name": {"required": True, "type": str, "min_length": 3, "max_length": 50},
            "email": {"required": True, "type": str},
            "age": {"type": int}
        }

        validated_data = await base_service.validate_input(data, rules)

        assert validated_data == data

    @pytest.mark.asyncio
    async def test_validate_input_required_field_missing(self, base_service):
        """测试必填字段缺失。"""
        data = {"email": "test@example.com"}
        rules = {
            "name": {"required": True, "type": str},
            "email": {"required": True, "type": str}
        }

        with pytest.raises(ValidationError) as exc_info:
            await base_service.validate_input(data, rules)

        error_details = exc_info.value.details.get("errors", [])
        error_text = " ".join(error_details)
        assert "name" in error_text
        assert "required" in error_text

    @pytest.mark.asyncio
    async def test_validate_input_type_mismatch(self, base_service):
        """测试类型不匹配。"""
        data = {"name": 123, "age": "not_a_number"}
        rules = {
            "name": {"required": True, "type": str},
            "age": {"type": int}
        }

        with pytest.raises(ValidationError) as exc_info:
            await base_service.validate_input(data, rules)

        error_details = exc_info.value.details.get("errors", [])
        error_text = " ".join(error_details)
        assert "type" in error_text

    @pytest.mark.asyncio
    async def test_validate_input_length_validation(self, base_service):
        """测试长度验证。"""
        data = {"name": "ab", "description": "a" * 1001}
        rules = {
            "name": {"type": str, "min_length": 3},
            "description": {"type": str, "max_length": 1000}
        }

        with pytest.raises(ValidationError) as exc_info:
            await base_service.validate_input(data, rules)

        error_details = exc_info.value.details.get("errors", [])
        error_text = " ".join(error_details)
        assert "at least 3 characters" in error_text or "at most 1000 characters" in error_text

    @pytest.mark.asyncio
    async def test_validate_input_custom_validator(self, base_service):
        """测试自定义验证器。"""
        def validate_email(value):
            return "@" in value and "." in value

        data = {"email": "invalid_email"}
        rules = {
            "email": {"type": str, "validator": validate_email}
        }

        with pytest.raises(ValidationError) as exc_info:
            await base_service.validate_input(data, rules)

        assert "validation" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_validate_input_async_validator(self, base_service):
        """测试异步自定义验证器。"""
        async def validate_unique_email(value):
            # 模拟异步验证（如数据库查询）
            await asyncio.sleep(0.01)
            return value != "taken@example.com"

        data = {"email": "taken@example.com"}
        rules = {
            "email": {"type": str, "validator": validate_unique_email}
        }

        with pytest.raises(ValidationError) as exc_info:
            await base_service.validate_input(data, rules)

        assert "validation" in str(exc_info.value.message)

    @pytest.mark.asyncio
    @patch('app.services.base.get_cache')
    async def test_cache_operations(self, mock_get_cache, base_service, mock_cache):
        """测试缓存操作。"""
        mock_get_cache.return_value = mock_cache

        # 测试缓存设置
        result = await base_service.cache_set("test_key", "test_value", ttl=60)
        assert result is True
        mock_cache.set.assert_called_once_with("test_key", "test_value", ttl=60)

        # 测试缓存获取
        mock_cache.get.return_value = "cached_value"
        value = await base_service.cache_get("test_key", default="default_value")
        assert value == "cached_value"
        mock_cache.get.assert_called_once_with("test_key", "default_value")

        # 测试缓存删除
        result = await base_service.cache_delete("test_key1", "test_key2")
        assert result == 1
        mock_cache.delete.assert_called_once_with("test_key1", "test_key2")

    @pytest.mark.asyncio
    @patch('app.services.base.get_cache')
    async def test_cache_get_or_set(self, mock_get_cache, base_service, mock_cache):
        """测试缓存获取或设置。"""
        mock_get_cache.return_value = mock_cache

        # 模拟缓存未命中
        mock_cache.get_or_set.return_value = "generated_value"

        def generate_value():
            return "generated_value"

        result = await base_service.cache_get_or_set("test_key", generate_value, ttl=120)
        assert result == "generated_value"
        mock_cache.get_or_set.assert_called_once_with("test_key", generate_value, ttl=120)

    @pytest.mark.asyncio
    async def test_cache_disabled(self, base_service):
        """测试禁用缓存的情况。"""
        base_service.enable_caching = False

        # 缓存操作应该返回默认值或False
        assert await base_service.cache_set("key", "value") is False
        assert await base_service.cache_get("key", "default") == "default"
        assert await base_service.cache_delete("key") == 0

    @pytest.mark.asyncio
    @patch('app.services.base.get_session')
    async def test_with_session_context(self, mock_get_session, base_service, mock_db_session):
        """测试数据库会话上下文管理器。"""
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        async with base_service.with_session() as session:
            assert session == mock_db_session

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    async def test_with_transaction_context(self, mock_get_transaction, base_service, mock_db_session):
        """测试数据库事务上下文管理器。"""
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        async with base_service.with_transaction() as session:
            assert session == mock_db_session


class TestCRUDService:
    """CRUDService测试类。"""

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    async def test_create_success(self, mock_get_transaction, crud_service, mock_db_session):
        """测试创建记录成功。"""
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        # 模拟创建的实例
        created_instance = TestModel(id=1, name="Test Name", description="Test Description")
        mock_db_session.session.add = MagicMock()
        mock_db_session.session.flush = AsyncMock()

        # 模拟flush后设置ID
        async def mock_flush():
            created_instance.id = 1

        mock_db_session.session.flush.side_effect = mock_flush

        data = {"name": "Test Name", "description": "Test Description"}

        with patch.object(crud_service.model_class, '__new__', return_value=created_instance):
            result = await crud_service.create(data)

        assert result == created_instance
        assert result.id == 1
        mock_db_session.session.add.assert_called_once()
        mock_db_session.session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_validation_error(self, crud_service):
        """测试创建时验证错误。"""
        data = {"name": "", "description": "Valid description"}  # name为空，应该失败

        with pytest.raises(ValidationError):
            await crud_service.create(data)

    @pytest.mark.asyncio
    @patch('app.services.base.get_session')
    @patch('app.services.base.get_cache')
    async def test_get_by_id_from_cache(self, mock_get_cache, mock_get_session, crud_service, mock_cache):
        """测试从缓存获取记录。"""
        mock_get_cache.return_value = mock_cache

        # 模拟缓存命中
        cached_instance = TestModel(id=1, name="Cached Name")
        mock_cache.get.return_value = cached_instance

        result = await crud_service.get_by_id(1)

        assert result == cached_instance
        mock_cache.get.assert_called_once_with("testmodel:id:1")
        # 不应该访问数据库
        mock_get_session.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.base.get_session')
    @patch('app.services.base.get_cache')
    async def test_get_by_id_from_database(self, mock_get_cache, mock_get_session, crud_service, mock_cache, mock_db_session):
        """测试从数据库获取记录。"""
        mock_get_cache.return_value = mock_cache
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        # 模拟缓存未命中
        mock_cache.get.return_value = None

        # 模拟数据库查询结果
        db_instance = TestModel(id=1, name="DB Name")
        mock_db_session.session.get.return_value = db_instance

        result = await crud_service.get_by_id(1)

        assert result == db_instance
        mock_cache.get.assert_called_once_with("testmodel:id:1")
        mock_cache.set.assert_called_once_with("testmodel:id:1", db_instance)
        mock_db_session.session.get.assert_called_once_with(TestModel, 1)

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    @patch('app.services.base.get_cache')
    async def test_update_success(self, mock_get_cache, mock_get_transaction, crud_service, mock_cache, mock_db_session):
        """测试更新记录成功。"""
        mock_get_cache.return_value = mock_cache
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        # 模拟现有实例
        existing_instance = TestModel(id=1, name="Old Name", description="Old Description")
        mock_db_session.session.get.return_value = existing_instance

        update_data = {"name": "New Name", "description": "New Description"}

        result = await crud_service.update(1, update_data)

        assert result == existing_instance
        assert result.name == "New Name"
        assert result.description == "New Description"
        mock_db_session.session.flush.assert_called_once()
        mock_cache.delete.assert_called_once_with("testmodel:id:1")

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    async def test_update_not_found(self, mock_get_transaction, crud_service, mock_db_session):
        """测试更新不存在的记录。"""
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        # 模拟记录不存在
        mock_db_session.session.get.return_value = None

        update_data = {"name": "New Name"}

        with pytest.raises(NotFoundError) as exc_info:
            await crud_service.update(999, update_data)

        assert exc_info.value.resource == "testmodel"
        assert exc_info.value.identifier == 999

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    @patch('app.services.base.get_cache')
    async def test_delete_success(self, mock_get_cache, mock_get_transaction, crud_service, mock_cache, mock_db_session):
        """测试删除记录成功（软删除）。"""
        mock_get_cache.return_value = mock_cache
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        # 模拟现有实例（有is_deleted字段）
        existing_instance = TestModel(id=1, name="Test Name")
        existing_instance.is_deleted = False
        mock_db_session.session.get.return_value = existing_instance

        result = await crud_service.delete(1)

        assert result is True
        assert existing_instance.is_deleted is True
        mock_db_session.session.flush.assert_called_once()
        mock_cache.delete.assert_called_once_with("testmodel:id:1")

    @pytest.mark.asyncio
    @patch('app.services.base.get_transaction')
    async def test_delete_not_found(self, mock_get_transaction, crud_service, mock_db_session):
        """测试删除不存在的记录。"""
        mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

        # 模拟记录不存在
        mock_db_session.session.get.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await crud_service.delete(999)

        assert exc_info.value.resource == "testmodel"
        assert exc_info.value.identifier == 999

    @pytest.mark.asyncio
    async def test_health_check(self, crud_service):
        """测试CRUD服务健康检查。"""
        with patch.object(crud_service, 'with_session'), \
             patch.object(crud_service, 'cache') as mock_cache_property:

            # 模拟成功的健康检查
            mock_session = AsyncMock()
            mock_session.session.execute = AsyncMock()

            mock_cache = AsyncMock()
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache.get = AsyncMock(return_value="test")
            mock_cache.delete = AsyncMock(return_value=1)
            mock_cache_property.return_value = mock_cache

            crud_service.with_session = AsyncMock()
            crud_service.with_session.return_value.__aenter__.return_value = mock_session

            health_result = await crud_service.health_check()

            assert health_result["status"] == "healthy"
            assert health_result["service"] == "TestCRUDService"
            assert health_result["model"] == "testmodel"
            assert health_result["database_connection"] is True
            assert health_result["cache_connection"] is True


class TestServiceRegistry:
    """服务注册表测试类。"""

    def test_register_and_get_service(self):
        """测试服务注册和获取。"""
        service = TestBaseService()
        register_service("test_service", service)

        retrieved_service = get_service("test_service")
        assert retrieved_service is service

        # 测试获取不存在的服务
        non_existent = get_service("non_existent")
        assert non_existent is None

    def test_list_services(self):
        """测试列出所有服务。"""
        service1 = TestBaseService()
        service2 = TestCRUDService()

        register_service("service1", service1)
        register_service("service2", service2)

        services = list_services()
        assert "service1" in services
        assert "service2" in services
        assert len(services) == 2

    @pytest.mark.asyncio
    async def test_health_check_all_services(self):
        """测试所有服务健康检查。"""
        # 注册测试服务
        healthy_service = TestBaseService()
        unhealthy_service = TestBaseService()

        # 模拟不健康的服务
        async def unhealthy_check():
            return {"status": "unhealthy", "error": "Service is down"}

        unhealthy_service.health_check = unhealthy_check

        register_service("healthy_service", healthy_service)
        register_service("unhealthy_service", unhealthy_service)

        result = await health_check_all_services()

        assert result["total_services"] == 2
        assert result["healthy_services"] == 1
        assert result["unhealthy_services"] == 1
        assert result["overall_status"] == "degraded"
        assert "healthy_service" in result["services"]
        assert "unhealthy_service" in result["services"]
        assert result["services"]["healthy_service"]["status"] == "healthy"
        assert result["services"]["unhealthy_service"]["status"] == "unhealthy"


class TestServiceErrors:
    """服务错误类测试。"""

    def test_service_error(self):
        """测试ServiceError基类。"""
        error = ServiceError(
            "Test error message",
            code="TEST_ERROR",
            details={"param": "value"}
        )

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.code == "TEST_ERROR"
        assert error.details["param"] == "value"
        assert isinstance(error.timestamp, datetime)

    def test_validation_error(self):
        """测试ValidationError。"""
        error = ValidationError(
            "Invalid field value",
            field="email",
            details={"expected": "email format"}
        )

        assert error.code == "VALIDATION_ERROR"
        assert error.field == "email"
        assert error.details["expected"] == "email format"

    def test_not_found_error(self):
        """测试NotFoundError。"""
        error = NotFoundError("user", 123, details={"searched_fields": ["id", "email"]})

        assert error.code == "NOT_FOUND"
        assert error.resource == "user"
        assert error.identifier == 123
        assert "user not found: 123" in error.message

    def test_conflict_error(self):
        """测试ConflictError。"""
        error = ConflictError(
            "Email already exists",
            resource="user",
            details={"conflicting_field": "email"}
        )

        assert error.code == "CONFLICT"
        assert error.resource == "user"
        assert error.details["conflicting_field"] == "email"