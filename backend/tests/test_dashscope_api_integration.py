"""DashScope API 集成测试（简化版本，专注功能验证）."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.dashscope import router
from app.services.dashscope_service import (
    ChatCompletionServiceResponse,
    StreamChunk,
)


@pytest.fixture
def mock_service():
    """模拟 DashScope 服务."""
    return AsyncMock()


@pytest.fixture
def app_with_mock_service(mock_service):
    """创建带有模拟服务的测试应用."""
    app = FastAPI()

    # 模拟依赖注入
    def get_mock_service():
        return mock_service

    # 重写依赖
    app.dependency_overrides = {
        "app.dependencies.dashscope.get_dashscope_service": get_mock_service
    }

    app.include_router(router, prefix="/dashscope")
    return app


@pytest.fixture
def client(app_with_mock_service):
    """创建测试客户端."""
    return TestClient(app_with_mock_service)


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


class TestDashScopeAPIIntegration:
    """DashScope API 集成测试类."""

    def test_chat_completion_success(self, client, mock_service, mock_response):
        """测试聊天补全端点成功场景."""
        # 设置模拟返回值
        mock_service.chat_completion.return_value = mock_response

        # 发送请求
        response = client.post(
            "/dashscope/chat/completions",
            json={
                "messages": ["Hello", "Hi there!"],
                "model": "qwen-turbo",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        assert data["model"] == "qwen-turbo"
        assert data["content"] == "Hello! How can I help you today?"
        assert data["finish_reason"] == "stop"
        assert data["usage"]["total_tokens"] == 15

        # 验证服务被正确调用
        mock_service.chat_completion.assert_called_once()
        call_args = mock_service.chat_completion.call_args[0][0]
        assert call_args.messages == ["Hello", "Hi there!"]
        assert call_args.model == "qwen-turbo"
        assert call_args.temperature == 0.7
        assert call_args.max_tokens == 100

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

    @pytest.mark.parametrize("invalid_request", [
        {"messages": ["Hello"], "model": "qwen-turbo", "temperature": -1},  # 无效温度
        {"messages": ["Hello"], "model": "qwen-turbo", "max_tokens": -1},  # 无效令牌数
    ])
    def test_chat_completion_validation_errors(self, client, invalid_request):
        """测试各种验证错误场景."""
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