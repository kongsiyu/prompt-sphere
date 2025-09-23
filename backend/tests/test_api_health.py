"""健康检查API测试。

测试内容：
- 系统整体健康检查端点
- 数据库健康检查端点
- Redis健康检查端点
- 服务健康检查端点
- 缓存健康检查端点
- 就绪检查端点
- 存活检查端点
- 健康检查响应格式验证
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from app.api.health import router, _app_start_time, measure_response_time
from app.api import APIResponse
from app.main import create_application


@pytest.fixture
def client():
    """创建测试客户端。"""
    app = create_application()
    return TestClient(app)


@pytest.fixture
def mock_system_health():
    """模拟系统健康状态。"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "services": {"overall_status": "healthy"},
        "errors": []
    }


@pytest.fixture
def mock_db_health():
    """模拟数据库健康状态。"""
    return {
        "status": "healthy",
        "session_creation": True,
        "query_execution": True,
        "transaction_handling": True,
        "error": None
    }


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端。"""
    client = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    client.set = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=b"test_data")
    client.delete = AsyncMock(return_value=1)
    client._connection_pool = MagicMock()
    client._connection_pool.connection_kwargs = {"max_connections": 10}
    return client


@pytest.fixture
def mock_services_health():
    """模拟服务健康状态。"""
    return {
        "overall_status": "healthy",
        "total_services": 2,
        "healthy_services": 2,
        "unhealthy_services": 0,
        "services": {
            "service1": {"status": "healthy"},
            "service2": {"status": "healthy"}
        }
    }


class TestResponseTimeMeasurement:
    """响应时间测量测试类。"""

    @pytest.mark.asyncio
    async def test_measure_response_time_sync_function(self):
        """测试同步函数响应时间测量。"""
        def sync_func(x, y):
            time.sleep(0.01)  # 模拟处理时间
            return x + y

        result, response_time = await measure_response_time(sync_func, 1, 2)

        assert result == 3
        assert response_time >= 10  # 至少10毫秒
        assert response_time < 50   # 应该不超过50毫秒

    @pytest.mark.asyncio
    async def test_measure_response_time_async_function(self):
        """测试异步函数响应时间测量。"""
        async def async_func(x, y):
            await asyncio.sleep(0.01)  # 模拟异步处理时间
            return x * y

        import asyncio
        result, response_time = await measure_response_time(async_func, 3, 4)

        assert result == 12
        assert response_time >= 10  # 至少10毫秒
        assert response_time < 50   # 应该不超过50毫秒

    @pytest.mark.asyncio
    async def test_measure_response_time_with_exception(self):
        """测试异常情况下的响应时间测量。"""
        def failing_func():
            time.sleep(0.01)
            raise ValueError("Test error")

        result, response_time = await measure_response_time(failing_func)

        assert result is None
        assert response_time >= 10  # 即使失败也要测量时间


class TestSystemHealthEndpoint:
    """系统健康检查端点测试类。"""

    @patch('app.api.health.get_system_health')
    @patch('app.api.health.get_cache')
    def test_health_check_all_healthy(self, mock_get_cache, mock_get_system_health, client, mock_system_health):
        """测试所有组件都健康的情况。"""
        mock_get_system_health.return_value = mock_system_health

        # 模拟缓存操作
        mock_cache = AsyncMock()
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = 1
        mock_get_cache.return_value = mock_cache

        response = client.get("/health/")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["overall"]["status"] == "healthy"
        assert "uptime" in data["data"]["overall"]
        assert "version" in data["data"]["overall"]
        assert "components" in data["data"]
        assert "database" in data["data"]["components"]
        assert "redis" in data["data"]["components"]
        assert "services" in data["data"]["components"]
        assert "cache" in data["data"]["components"]

    @patch('app.api.health.get_system_health')
    def test_health_check_degraded(self, mock_get_system_health, client):
        """测试系统降级状态。"""
        degraded_health = {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {"status": "healthy"},
            "redis": {"status": "unhealthy", "error": "Connection failed"},
            "services": {"overall_status": "healthy"},
            "errors": ["Redis: Connection failed"]
        }
        mock_get_system_health.return_value = degraded_health

        response = client.get("/health/")

        assert response.status_code == status.HTTP_200_OK  # 仍返回200，但状态为degraded

        data = response.json()
        assert data["success"] is True
        assert data["data"]["overall"]["status"] == "degraded"
        assert len(data["data"]["errors"]) > 0

    @patch('app.api.health.get_system_health')
    def test_health_check_unhealthy(self, mock_get_system_health, client):
        """测试系统不健康状态。"""
        unhealthy_health = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {"status": "unhealthy", "error": "Database down"},
            "redis": {"status": "unhealthy", "error": "Redis down"},
            "services": {"overall_status": "unhealthy"},
            "errors": ["Database: Database down", "Redis: Redis down"]
        }
        mock_get_system_health.return_value = unhealthy_health

        response = client.get("/health/")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is True
        assert data["data"]["overall"]["status"] == "unhealthy"

    @patch('app.api.health.get_system_health')
    def test_health_check_exception(self, mock_get_system_health, client):
        """测试健康检查异常。"""
        mock_get_system_health.side_effect = Exception("Critical system error")

        response = client.get("/health/")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "HEALTH_CHECK_FAILED"
        assert "Critical system error" in data["error"]["details"]["error"]


class TestDatabaseHealthEndpoint:
    """数据库健康检查端点测试类。"""

    @patch('app.api.health.check_session_health')
    def test_database_health_check_healthy(self, mock_check_session_health, client, mock_db_health):
        """测试数据库健康检查成功。"""
        mock_check_session_health.return_value = mock_db_health

        response = client.get("/health/database")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["component"] == "database"
        assert "response_time" in data["data"]

    @patch('app.api.health.check_session_health')
    def test_database_health_check_unhealthy(self, mock_check_session_health, client):
        """测试数据库健康检查失败。"""
        unhealthy_db = {
            "status": "unhealthy",
            "session_creation": False,
            "query_execution": False,
            "transaction_handling": False,
            "error": "Database connection timeout"
        }
        mock_check_session_health.return_value = unhealthy_db

        response = client.get("/health/database")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["error"] == "Database connection timeout"

    @patch('app.api.health.check_session_health')
    def test_database_health_check_exception(self, mock_check_session_health, client):
        """测试数据库健康检查异常。"""
        mock_check_session_health.side_effect = Exception("Database check failed")

        response = client.get("/health/database")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DATABASE_HEALTH_CHECK_FAILED"


class TestRedisHealthEndpoint:
    """Redis健康检查端点测试类。"""

    @patch('app.api.health.get_redis_dependency')
    def test_redis_health_check_healthy(self, mock_get_redis_dependency, client, mock_redis_client):
        """测试Redis健康检查成功。"""
        mock_get_redis_dependency.return_value = mock_redis_client

        response = client.get("/health/redis")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["component"] == "redis"
        assert "response_time" in data["data"]
        assert "operations" in data["data"]
        assert "connection_pool" in data["data"]

    @patch('app.api.health.get_redis_dependency')
    def test_redis_health_check_unhealthy(self, mock_get_redis_dependency, client, mock_redis_client):
        """测试Redis健康检查失败。"""
        mock_redis_client.health_check.return_value = False
        mock_get_redis_dependency.return_value = mock_redis_client

        response = client.get("/health/redis")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["error"] == "Redis ping failed"

    @patch('app.api.health.get_redis_dependency')
    def test_redis_health_check_operations_failure(self, mock_get_redis_dependency, client, mock_redis_client):
        """测试Redis操作失败。"""
        mock_redis_client.health_check.return_value = True
        mock_redis_client.set.side_effect = Exception("Set operation failed")
        mock_get_redis_dependency.return_value = mock_redis_client

        response = client.get("/health/redis")

        # 仍然返回200，但状态为degraded
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "degraded"
        assert "operations_error" in data["data"]

    @patch('app.api.health.get_redis_dependency')
    def test_redis_health_check_exception(self, mock_get_redis_dependency, client):
        """测试Redis健康检查异常。"""
        mock_get_redis_dependency.side_effect = Exception("Redis connection failed")

        response = client.get("/health/redis")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "REDIS_HEALTH_CHECK_FAILED"


class TestServicesHealthEndpoint:
    """服务健康检查端点测试类。"""

    @patch('app.api.health.health_check_all_services')
    def test_services_health_check_healthy(self, mock_health_check_all_services, client, mock_services_health):
        """测试服务健康检查成功。"""
        mock_health_check_all_services.return_value = mock_services_health

        response = client.get("/health/services")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["overall_status"] == "healthy"
        assert data["data"]["component"] == "services"
        assert "response_time" in data["data"]
        assert data["data"]["total_services"] == 2
        assert data["data"]["healthy_services"] == 2

    @patch('app.api.health.health_check_all_services')
    def test_services_health_check_unhealthy(self, mock_health_check_all_services, client):
        """测试服务健康检查失败。"""
        unhealthy_services = {
            "overall_status": "unhealthy",
            "total_services": 2,
            "healthy_services": 0,
            "unhealthy_services": 2,
            "services": {
                "service1": {"status": "unhealthy", "error": "Service1 down"},
                "service2": {"status": "unhealthy", "error": "Service2 down"}
            }
        }
        mock_health_check_all_services.return_value = unhealthy_services

        response = client.get("/health/services")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is True
        assert data["data"]["overall_status"] == "unhealthy"

    @patch('app.api.health.health_check_all_services')
    def test_services_health_check_exception(self, mock_health_check_all_services, client):
        """测试服务健康检查异常。"""
        mock_health_check_all_services.side_effect = Exception("Services check failed")

        response = client.get("/health/services")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SERVICES_HEALTH_CHECK_FAILED"


class TestCacheHealthEndpoint:
    """缓存健康检查端点测试类。"""

    @patch('app.api.health.get_cache')
    def test_cache_health_check_healthy(self, mock_get_cache, client):
        """测试缓存健康检查成功。"""
        mock_cache = AsyncMock()
        mock_cache.namespace = "health_check"
        mock_cache.set.return_value = True
        mock_cache.get.return_value = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        mock_cache.exists.return_value = True
        mock_cache.delete.return_value = 1
        mock_get_cache.return_value = mock_cache

        response = client.get("/health/cache")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["component"] == "cache"
        assert "operations" in data["data"]
        assert "average_response_time" in data["data"]
        assert data["data"]["namespace"] == "health_check"

    @patch('app.api.health.get_cache')
    def test_cache_health_check_degraded(self, mock_get_cache, client):
        """测试缓存健康检查降级。"""
        mock_cache = AsyncMock()
        mock_cache.namespace = "health_check"
        mock_cache.set.return_value = False  # 设置操作失败
        mock_cache.get.return_value = None
        mock_cache.exists.return_value = True
        mock_cache.delete.return_value = 1
        mock_get_cache.return_value = mock_cache

        response = client.get("/health/cache")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "degraded"
        assert "failed_operations" in data["data"]

    @patch('app.api.health.get_cache')
    def test_cache_health_check_exception(self, mock_get_cache, client):
        """测试缓存健康检查异常。"""
        mock_get_cache.side_effect = Exception("Cache connection failed")

        response = client.get("/health/cache")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CACHE_HEALTH_CHECK_FAILED"


class TestReadinessEndpoint:
    """就绪检查端点测试类。"""

    @patch('app.api.health.check_session_health')
    @patch('app.api.health.get_redis_dependency')
    def test_readiness_check_ready(self, mock_get_redis_dependency, mock_check_session_health, client, mock_redis_client):
        """测试应用就绪。"""
        # 模拟数据库健康
        mock_check_session_health.return_value = {"status": "healthy"}

        # 模拟Redis健康
        mock_redis_client.health_check.return_value = True
        mock_get_redis_dependency.return_value = mock_redis_client

        response = client.get("/health/ready")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["ready"] is True
        assert data["data"]["checks"]["database"] is True
        assert data["data"]["checks"]["redis"] is True

    @patch('app.api.health.check_session_health')
    @patch('app.api.health.get_redis_dependency')
    def test_readiness_check_not_ready(self, mock_get_redis_dependency, mock_check_session_health, client):
        """测试应用未就绪。"""
        # 模拟数据库不健康
        mock_check_session_health.side_effect = Exception("Database not ready")

        # 模拟Redis不健康
        mock_get_redis_dependency.side_effect = Exception("Redis not ready")

        response = client.get("/health/ready")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_READY"
        assert data["error"]["details"]["checks"]["database"] is False
        assert data["error"]["details"]["checks"]["redis"] is False

    @patch('app.api.health.check_session_health')
    def test_readiness_check_exception(self, mock_check_session_health, client):
        """测试就绪检查异常。"""
        mock_check_session_health.side_effect = Exception("Critical error")

        response = client.get("/health/ready")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] in ["READINESS_CHECK_FAILED", "NOT_READY"]


class TestLivenessEndpoint:
    """存活检查端点测试类。"""

    def test_liveness_check(self, client):
        """测试存活检查。"""
        response = client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert data["data"]["alive"] is True
        assert "uptime" in data["data"]
        assert "timestamp" in data["data"]
        assert data["message"] == "应用存活"

    def test_liveness_check_uptime(self, client):
        """测试存活检查运行时间计算。"""
        # 记录当前时间
        start_time = time.time()

        response = client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        uptime = data["data"]["uptime"]

        # 运行时间应该是合理的值
        assert uptime >= 0
        assert uptime < (time.time() - _app_start_time + 10)  # 允许一些误差


class TestHealthEndpointResponseFormat:
    """健康检查端点响应格式测试类。"""

    @patch('app.api.health.get_system_health')
    def test_response_format_consistency(self, mock_get_system_health, client, mock_system_health):
        """测试响应格式一致性。"""
        mock_get_system_health.return_value = mock_system_health

        response = client.get("/health/")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # 检查标准响应格式
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data

        # 检查时间戳格式
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # 验证ISO格式

    def test_error_response_format(self, client):
        """测试错误响应格式。"""
        with patch('app.api.health.get_system_health', side_effect=Exception("Test error")):
            response = client.get("/health/")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            data = response.json()

            # 检查错误响应格式
            assert "success" in data
            assert data["success"] is False
            assert "error" in data
            assert "timestamp" in data

            # 检查错误详情
            error = data["error"]
            assert "code" in error
            assert "message" in error
            assert "details" in error

    @patch('app.api.health.get_system_health')
    def test_request_id_header(self, mock_get_system_health, client, mock_system_health):
        """测试请求ID头部。"""
        mock_get_system_health.return_value = mock_system_health

        response = client.get("/health/")

        # 检查响应头中是否包含请求ID
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers

        # 验证请求ID格式（UUID）
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID长度
        assert request_id.count('-') == 4  # UUID格式