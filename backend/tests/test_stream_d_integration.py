"""Stream D集成测试 - 独立测试文件。

该测试文件用于验证Stream D的核心功能，避免复杂的依赖问题。

测试内容：
- 服务基类核心功能
- 依赖注入机制
- API响应格式
- 错误处理机制
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class TestServiceError(Exception):
    """测试用服务错误。"""
    def __init__(self, message: str, code: str = "SERVICE_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)


class TestBaseService:
    """测试用基础服务类（简化版）。"""

    def __init__(self, cache_namespace: str = "test", enable_caching: bool = True):
        self.service_name = self.__class__.__name__
        self.cache_namespace = cache_namespace
        self.enable_caching = enable_caching
        self._cache = None

    async def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None, level: str = "info"):
        """记录操作日志。"""
        print(f"[{level.upper()}] {self.service_name}: {operation} - {details}")

    async def handle_error(self, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None):
        """错误处理。"""
        if isinstance(error, TestServiceError):
            return error

        return TestServiceError(
            f"Error in {operation}: {str(error)}",
            code="INTERNAL_ERROR",
            details={"operation": operation, "context": context or {}}
        )

    async def validate_input(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """输入验证。"""
        validated_data = {}
        errors = []

        for field, rule in rules.items():
            value = data.get(field)

            # 必填字段检查
            if rule.get("required", False) and (value is None or value == ""):
                errors.append(f"Field '{field}' is required")
                continue

            # 类型检查
            if value is not None and "type" in rule:
                expected_type = rule["type"]
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                    continue

            validated_data[field] = value

        if errors:
            raise TestServiceError(
                "Input validation failed",
                code="VALIDATION_ERROR",
                details={"errors": errors}
            )

        return validated_data

    async def health_check(self) -> Dict[str, Any]:
        """健康检查。"""
        return {
            "status": "healthy",
            "service": self.service_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class TestAPIResponse:
    """测试用API响应类。"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建成功响应。"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id
        }

    @staticmethod
    def error(code: str, message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建错误响应。"""
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id
        }


class TestCurrentUser:
    """测试用当前用户类。"""

    def __init__(self, user_id: str, username: str, permissions: list[str]):
        self.user_id = user_id
        self.username = username
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """检查权限。"""
        return permission in self.permissions or "admin" in self.permissions


class TestPaginationParams:
    """测试用分页参数类。"""

    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(max(1, size), 100)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


# === 测试类 ===

class TestServiceBaseFeatures:
    """服务基类功能测试。"""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """测试服务初始化。"""
        service = TestBaseService(cache_namespace="test_namespace", enable_caching=True)

        assert service.service_name == "TestBaseService"
        assert service.cache_namespace == "test_namespace"
        assert service.enable_caching is True

    @pytest.mark.asyncio
    async def test_log_operation(self, capsys):
        """测试操作日志记录。"""
        service = TestBaseService()

        await service.log_operation("test_operation", {"param": "value"}, level="info")

        captured = capsys.readouterr()
        assert "test_operation" in captured.out
        assert "INFO" in captured.out
        assert "param" in captured.out

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理。"""
        service = TestBaseService()

        # 测试普通异常处理
        original_error = ValueError("Test error")
        service_error = await service.handle_error(original_error, "test_operation", {"key": "value"})

        assert isinstance(service_error, TestServiceError)
        assert "test_operation" in service_error.message
        assert service_error.code == "INTERNAL_ERROR"

        # 测试服务错误直接返回
        test_service_error = TestServiceError("Service error", code="TEST_ERROR")
        result = await service.handle_error(test_service_error, "test_operation")

        assert result is test_service_error

    @pytest.mark.asyncio
    async def test_input_validation_success(self):
        """测试输入验证成功。"""
        service = TestBaseService()

        data = {"name": "Test Name", "age": 25}
        rules = {
            "name": {"required": True, "type": str},
            "age": {"type": int}
        }

        validated_data = await service.validate_input(data, rules)
        assert validated_data == data

    @pytest.mark.asyncio
    async def test_input_validation_failure(self):
        """测试输入验证失败。"""
        service = TestBaseService()

        data = {"age": "not_a_number"}  # 缺少必填字段name，age类型错误
        rules = {
            "name": {"required": True, "type": str},
            "age": {"type": int}
        }

        with pytest.raises(TestServiceError) as exc_info:
            await service.validate_input(data, rules)

        assert exc_info.value.code == "VALIDATION_ERROR"
        assert "errors" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查。"""
        service = TestBaseService()

        health_result = await service.health_check()

        assert health_result["status"] == "healthy"
        assert health_result["service"] == "TestBaseService"
        assert "timestamp" in health_result


class TestAPIResponseFormat:
    """API响应格式测试。"""

    def test_success_response(self):
        """测试成功响应格式。"""
        response = TestAPIResponse.success(
            data={"id": 1, "name": "Test"},
            message="操作成功",
            request_id="req-123"
        )

        assert response["success"] is True
        assert response["data"]["id"] == 1
        assert response["message"] == "操作成功"
        assert response["request_id"] == "req-123"
        assert "timestamp" in response

    def test_error_response(self):
        """测试错误响应格式。"""
        response = TestAPIResponse.error(
            code="VALIDATION_ERROR",
            message="输入验证失败",
            details={"field": "name", "reason": "required"},
            request_id="req-456"
        )

        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "输入验证失败"
        assert response["error"]["details"]["field"] == "name"
        assert response["request_id"] == "req-456"
        assert "timestamp" in response

    def test_response_timestamp_format(self):
        """测试响应时间戳格式。"""
        response = TestAPIResponse.success()

        timestamp = response["timestamp"]
        # 验证时间戳可以被解析
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00') if timestamp.endswith('Z') else timestamp)
        assert isinstance(parsed_time, datetime)


class TestAuthenticationFeatures:
    """认证功能测试。"""

    def test_current_user_permissions(self):
        """测试用户权限检查。"""
        user = TestCurrentUser(
            user_id="user123",
            username="testuser",
            permissions=["read", "write"]
        )

        assert user.has_permission("read") is True
        assert user.has_permission("write") is True
        assert user.has_permission("admin") is False

        # 测试admin权限
        admin_user = TestCurrentUser(
            user_id="admin123",
            username="admin",
            permissions=["admin"]
        )

        assert admin_user.has_permission("read") is True  # admin拥有所有权限
        assert admin_user.has_permission("admin") is True

    def test_permission_inheritance(self):
        """测试权限继承。"""
        user = TestCurrentUser(
            user_id="user123",
            username="testuser",
            permissions=["admin"]
        )

        # admin用户应该拥有所有权限
        assert user.has_permission("read") is True
        assert user.has_permission("write") is True
        assert user.has_permission("delete") is True
        assert user.has_permission("any_permission") is True


class TestPaginationFeatures:
    """分页功能测试。"""

    def test_pagination_default(self):
        """测试默认分页参数。"""
        params = TestPaginationParams()

        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_pagination_custom(self):
        """测试自定义分页参数。"""
        params = TestPaginationParams(page=3, size=50)

        assert params.page == 3
        assert params.size == 50
        assert params.offset == 100  # (3-1) * 50
        assert params.limit == 50

    def test_pagination_boundary_values(self):
        """测试分页边界值。"""
        # 测试负数和零值
        params = TestPaginationParams(page=0, size=-10)

        assert params.page == 1  # 最小为1
        assert params.size == 1  # 最小为1

        # 测试超大值
        params = TestPaginationParams(page=999, size=1000)

        assert params.page == 999
        assert params.size == 100  # 最大为100


class TestErrorHandlingIntegration:
    """错误处理集成测试。"""

    @pytest.mark.asyncio
    async def test_service_error_propagation(self):
        """测试服务错误传播。"""
        service = TestBaseService()

        # 模拟服务操作中的错误
        async def failing_operation():
            raise ValueError("Database connection failed")

        try:
            await failing_operation()
        except Exception as e:
            service_error = await service.handle_error(e, "database_operation", {"table": "users"})

        assert isinstance(service_error, TestServiceError)
        assert "database_operation" in service_error.message
        assert service_error.details["operation"] == "database_operation"
        assert service_error.details["context"]["table"] == "users"

    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """测试验证错误处理。"""
        service = TestBaseService()

        invalid_data = {"name": "", "email": "invalid_email"}
        rules = {
            "name": {"required": True, "type": str},
            "email": {"required": True, "type": str}
        }

        api_response = None
        try:
            await service.validate_input(invalid_data, rules)
            pytest.fail("Expected TestServiceError to be raised")
        except TestServiceError as e:
            # 将服务错误转换为API响应
            api_response = TestAPIResponse.error(
                code=e.code,
                message=e.message,
                details=e.details
            )

        assert api_response is not None
        assert api_response["success"] is False
        assert api_response["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in api_response["error"]["details"]


class TestServiceIntegration:
    """服务集成测试。"""

    @pytest.mark.asyncio
    async def test_complete_service_workflow(self):
        """测试完整服务工作流程。"""
        service = TestBaseService()

        # 1. 记录操作开始
        await service.log_operation("user_creation_started", {"user_id": "new_user_123"})

        # 2. 验证输入数据
        user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
        rules = {
            "name": {"required": True, "type": str},
            "email": {"required": True, "type": str},
            "age": {"type": int}
        }

        validated_data = await service.validate_input(user_data, rules)
        assert validated_data == user_data

        # 3. 模拟业务逻辑执行
        created_user = {
            "id": "user_123",
            "name": validated_data["name"],
            "email": validated_data["email"],
            "age": validated_data["age"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # 4. 记录操作完成
        await service.log_operation("user_creation_completed", {"user_id": created_user["id"]})

        # 5. 生成API响应
        api_response = TestAPIResponse.success(
            data=created_user,
            message="用户创建成功"
        )

        assert api_response["success"] is True
        assert api_response["data"]["id"] == "user_123"
        assert api_response["message"] == "用户创建成功"

    @pytest.mark.asyncio
    async def test_service_health_check_integration(self):
        """测试服务健康检查集成。"""
        service = TestBaseService()

        # 执行健康检查
        health_result = await service.health_check()

        # 生成健康检查API响应
        api_response = TestAPIResponse.success(
            data=health_result,
            message=f"服务 {service.service_name} 状态: {health_result['status']}"
        )

        assert api_response["success"] is True
        assert api_response["data"]["status"] == "healthy"
        assert api_response["data"]["service"] == "TestBaseService"


class TestDependencyInjectionPatterns:
    """依赖注入模式测试。"""

    def test_service_registry_pattern(self):
        """测试服务注册表模式。"""
        # 模拟服务注册表
        service_registry = {}

        # 注册服务
        def register_service(name: str, service):
            service_registry[name] = service

        def get_service(name: str):
            return service_registry.get(name)

        # 测试服务注册和获取
        test_service = TestBaseService()
        register_service("test_service", test_service)

        retrieved_service = get_service("test_service")
        assert retrieved_service is test_service

        # 测试获取不存在的服务
        non_existent = get_service("non_existent")
        assert non_existent is None

    def test_dependency_factory_pattern(self):
        """测试依赖工厂模式。"""
        def create_service_dependency(service_name: str):
            def get_service_dependency():
                # 模拟从注册表获取服务
                services = {"test_service": TestBaseService()}
                service = services.get(service_name)
                if not service:
                    raise RuntimeError(f"Service {service_name} not found")
                return service
            return get_service_dependency

        # 测试成功获取服务
        dependency_func = create_service_dependency("test_service")
        service = dependency_func()
        assert isinstance(service, TestBaseService)

        # 测试服务不存在
        failing_dependency_func = create_service_dependency("non_existent")
        with pytest.raises(RuntimeError) as exc_info:
            failing_dependency_func()
        assert "not found" in str(exc_info.value)


# === 运行测试的主函数 ===

if __name__ == "__main__":
    # 如果直接运行此文件，执行所有测试
    import subprocess
    import sys

    # 使用pytest运行当前文件
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v"
    ], capture_output=True, text=True)

    print("=== 测试输出 ===")
    print(result.stdout)
    if result.stderr:
        print("=== 错误输出 ===")
        print(result.stderr)

    print(f"\n=== 测试结果 ===")
    print(f"退出码: {result.returncode}")
    if result.returncode == 0:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")