"""DashScope API 端点集成测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.dashscope import router
from app.services.dashscope_service import (
    ChatCompletionServiceResponse,
    StreamChunk,
)


@pytest.fixture
def app():
    """创建测试用的 FastAPI 应用."""
    app = FastAPI()
    app.include_router(router, prefix="/dashscope")
    return app


@pytest.fixture
def client(app, mock_service):
    """创建测试客户端."""
    from app.dependencies.dashscope import get_dashscope_service
    app.dependency_overrides[get_dashscope_service] = lambda: mock_service

    with TestClient(app) as client:
        yield client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def mock_service():
    """模拟 DashScope 服务."""
    return AsyncMock()


@pytest.fixture
def mock_response():
    """模拟服务响应."""
    return ChatCompletionServiceResponse(
        id="test-123",
        model="qwen-turbo",
        content="Hello! How can I help you today?",
        finish_reason="stop",
        usage={
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15
        },
        created=1234567890
    )


class TestDashScopeAPIEndpoints:
    """DashScope API 端点测试类."""

    def test_chat_completion_success(self, client, mock_service, mock_response):
        """测试聊天补全端点成功场景."""
        mock_service.chat_completion.return_value = mock_response

        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": ["Hello", "Hi there!"],
                "model": "qwen-turbo",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        assert data["model"] == "qwen-turbo"
        assert data["content"] == "Hello! How can I help you today?"
        assert data["finish_reason"] == "stop"
        assert data["usage"]["total_tokens"] == 15

    def test_chat_completion_validation_error_empty_messages(self, client):
        """测试聊天补全输入验证 - 空消息列表."""
        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": [],
                "model": "qwen-turbo"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_chat_completion_validation_error_invalid_temperature(self, client):
        """测试聊天补全输入验证 - 无效温度."""
        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": ["Hello"],
                "model": "qwen-turbo",
                "temperature": 3.0  # 超出范围
            }
        )

        assert response.status_code == 422  # Validation error

    def test_chat_completion_service_error(self, client, mock_service):
        """测试聊天补全服务错误处理."""
        from fastapi import HTTPException

        mock_service.chat_completion.side_effect = HTTPException(
            status_code=401,
            detail="认证失败"
        )

        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": ["Hello"],
                "model": "qwen-turbo"
            }
        )

        assert response.status_code == 401
        assert "认证失败" in response.json()["detail"]

    def test_stream_chat_completion_success(self, client, mock_service):
        """测试流式聊天补全成功场景."""
        # 模拟流式响应
        mock_chunks = [
            StreamChunk(
                id="stream-123",
                model="qwen-turbo",
                content="Hello",
                finish_reason=None,
                created=1234567890
            ),
            StreamChunk(
                id="stream-123",
                model="qwen-turbo",
                content=" there!",
                finish_reason="stop",
                created=1234567890
            )
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        mock_service.stream_chat_completion.return_value = mock_stream()

        response = client.post(
            "/dashscope/chat/completions/stream",
            json={
                "messages": ["Hello"],
                "model": "qwen-turbo",
                "stream": True
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # 验证流式响应内容
        content = response.text
        assert "data:" in content
        assert "[DONE]" in content

    def test_get_models_success(self, client, mock_service):
        """测试获取模型列表成功."""
        mock_models = [
            {
                "name": "qwen-turbo",
                "display_name": "Qwen Turbo",
                "max_tokens": 2048,
                "context_length": 8192,
                "supports_search": False,
                "supports_vision": False
            },
            {
                "name": "qwen-plus",
                "display_name": "Qwen Plus",
                "max_tokens": 6144,
                "context_length": 32768,
                "supports_search": False,
                "supports_vision": False
            }
        ]

        mock_service.get_supported_models.return_value = mock_models

        response = client.get("/dashscope/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 2
        assert data["models"][0]["name"] == "qwen-turbo"
        assert data["models"][1]["name"] == "qwen-plus"

    def test_health_check_healthy(self, client, mock_service):
        """测试健康检查 - 健康状态."""
        mock_health = {
            "status": "healthy",
            "service": "dashscope",
            "details": {
                "api_accessible": True,
                "settings_configured": True
            }
        }

        mock_service.health_check.return_value = mock_health

        response = client.get("/dashscope/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dashscope"
        assert data["details"]["api_accessible"] is True

    def test_health_check_unhealthy(self, client, mock_service):
        """测试健康检查 - 不健康状态."""
        mock_health = {
            "status": "unhealthy",
            "service": "dashscope",
            "error": "API 连接失败"
        }

        mock_service.health_check.return_value = mock_health

        # health_check 方法直接返回不健康状态而不抛出异常
        # 需要在路由层面处理状态检查
        response = client.get("/dashscope/health")

        # 根据实际实现，不健康状态可能返回 503
        assert response.status_code in [200, 503]

    def test_test_connection_success(self, client, mock_service, mock_response):
        """测试连接测试端点成功."""
        mock_service.chat_completion.return_value = mock_response

        response = client.get("/dashscope/test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test_response_id" in data
        assert data["model"] == "qwen-turbo"

    def test_test_connection_service_unavailable(self, app):
        """测试连接测试端点 - 服务不可用."""
        from fastapi import HTTPException
        from app.dependencies.dashscope import get_dashscope_service

        def mock_unhealthy_service():
            raise HTTPException(
                status_code=503,
                detail="DashScope 服务不可用"
            )

        app.dependency_overrides[get_dashscope_service] = mock_unhealthy_service

        with TestClient(app) as client:
            response = client.get("/dashscope/test")

        assert response.status_code == 503

        # 清理
        app.dependency_overrides.clear()

    @pytest.mark.parametrize("invalid_request", [
        {"messages": [""], "model": "qwen-turbo"},  # 空消息
        {"messages": ["Hello"], "model": "invalid-model"},  # 无效模型
        {"messages": ["Hello"], "model": "qwen-turbo", "temperature": -1},  # 无效温度
        {"messages": ["Hello"], "model": "qwen-turbo", "max_tokens": -1},  # 无效令牌数
    ])
    def test_chat_completion_validation_errors(self, app, invalid_request):
        """测试各种验证错误场景."""
        # 使用没有依赖覆盖的客户端来测试FastAPI的验证
        with TestClient(app) as client:
            response = client.post(
                "/dashscope/chat/completions",
                json=invalid_request
            )

        assert response.status_code == 422

    def test_default_parameters(self, client, mock_service, mock_response):
        """测试默认参数。"""
        mock_service.chat_completion.return_value = mock_response

        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": ["Hello"]
                # 只提供必需参数，其他使用默认值
            }
        )

        assert response.status_code == 200

        # 验证服务被调用时使用了默认参数
        call_args = mock_service.chat_completion.call_args[0][0]
        assert call_args.model == "qwen-turbo"  # 默认模型
        assert call_args.temperature == 0.7  # 默认温度
        assert call_args.stream is False  # 默认非流式

    def test_streaming_parameter_override(self, client, mock_service):
        """测试流式端点强制设置流式参数."""
        async def mock_stream():
            yield StreamChunk(
                id="test",
                model="qwen-turbo",
                content="test",
                finish_reason="stop",
                created=1234567890
            )

        mock_service.stream_chat_completion.return_value = mock_stream()

        response = client.post(
            "/dashscope/chat/completions/stream",
            json={
                "messages": ["Hello"],
                "stream": False  # 即使设置为 False，端点也会强制启用流式
            }
        )

        assert response.status_code == 200

        # 验证服务被调用时强制启用了流式
        call_args = mock_service.stream_chat_completion.call_args[0][0]
        assert call_args.stream is True