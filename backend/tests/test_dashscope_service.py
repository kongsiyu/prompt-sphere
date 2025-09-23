"""DashScope 服务层测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.dashscope_service import (
    DashScopeService,
    ChatRequest,
    ChatCompletionServiceResponse,
    StreamChunk,
)
from app.dashscope.models import (
    QwenModel,
    ChatCompletionResponse,
    StreamResponse,
    Choice,
    StreamChoice,
    Message,
    Usage,
    MessageRole,
)
from app.dashscope.exceptions import (
    DashScopeAPIError,
    DashScopeAuthenticationError,
    DashScopeRateLimitError,
)


class TestDashScopeService:
    """DashScope 服务层测试类."""

    @pytest.fixture
    def mock_settings(self):
        """模拟 DashScope 设置."""
        from app.dashscope.config import DashScopeSettings

        settings = MagicMock(spec=DashScopeSettings)
        settings.api_key = "test-api-key"
        settings.max_retries = 3
        settings.retry_delay = 1.0
        return settings

    @pytest.fixture
    def mock_client(self):
        """模拟 DashScope 客户端."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_settings):
        """创建服务实例用于测试."""
        with patch('app.services.dashscope_service.DashScopeClient'):
            service = DashScopeService(mock_settings)
            return service

    @pytest.fixture
    def chat_request(self):
        """测试用的聊天请求."""
        return ChatRequest(
            messages=["Hello", "Hi there!", "How are you?"],
            model="qwen-turbo",
            temperature=0.7,
            max_tokens=100,
            stream=False
        )

    @pytest.fixture
    def mock_response(self):
        """模拟的 DashScope 响应."""
        return ChatCompletionResponse(
            id="test-id-123",
            model=QwenModel.TURBO,
            choices=[
                Choice(
                    index=0,
                    message=Message(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!"),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=10,
                completion_tokens=8,
                total_tokens=18
            ),
            created=1234567890
        )

    def test_service_initialization(self, mock_settings):
        """测试服务初始化."""
        with patch('app.services.dashscope_service.DashScopeClient') as mock_client_class:
            service = DashScopeService(mock_settings)

            # 验证客户端被正确创建
            mock_client_class.assert_called_once_with(mock_settings)
            assert service.settings == mock_settings

    def test_validate_model_valid(self, service):
        """测试有效模型验证."""
        model = service._validate_model("qwen-turbo")
        assert model == QwenModel.TURBO

    def test_validate_model_invalid(self, service):
        """测试无效模型验证."""
        with pytest.raises(HTTPException) as exc_info:
            service._validate_model("invalid-model")

        assert exc_info.value.status_code == 400
        assert "不支持的模型" in exc_info.value.detail

    def test_build_messages_valid(self, service):
        """测试构建消息列表 - 有效输入."""
        messages = service._build_messages(["Hello", "Hi", "How are you?"])

        assert len(messages) == 3
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi"
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == "How are you?"

    def test_build_messages_empty(self, service):
        """测试构建消息列表 - 空输入."""
        with pytest.raises(HTTPException) as exc_info:
            service._build_messages([])

        assert exc_info.value.status_code == 400
        assert "消息列表不能为空" in exc_info.value.detail

    def test_build_messages_empty_content(self, service):
        """测试构建消息列表 - 空内容."""
        with pytest.raises(HTTPException) as exc_info:
            service._build_messages(["Hello", "", "How are you?"])

        assert exc_info.value.status_code == 400
        assert "消息 2 内容不能为空" in exc_info.value.detail

    def test_build_parameters_valid(self, service):
        """测试构建参数 - 有效输入."""
        request = ChatRequest(
            messages=["Hello"],
            model="qwen-turbo",
            temperature=0.8,
            max_tokens=500
        )

        params = service._build_parameters(request, QwenModel.TURBO)

        assert params.temperature == 0.8
        assert params.max_tokens == 500
        assert params.stream == False

    def test_build_parameters_invalid_temperature(self, service):
        """测试构建参数 - 无效温度."""
        request = ChatRequest(
            messages=["Hello"],
            model="qwen-turbo",
            temperature=3.0  # 超出范围
        )

        with pytest.raises(HTTPException) as exc_info:
            service._build_parameters(request, QwenModel.TURBO)

        assert exc_info.value.status_code == 400
        assert "temperature 必须在" in exc_info.value.detail

    def test_build_parameters_max_tokens_exceeded(self, service):
        """测试构建参数 - 超出令牌限制."""
        request = ChatRequest(
            messages=["Hello"],
            model="qwen-turbo",
            max_tokens=5000  # 超过 qwen-turbo 的限制
        )

        with pytest.raises(HTTPException) as exc_info:
            service._build_parameters(request, QwenModel.TURBO)

        assert exc_info.value.status_code == 400
        assert "max_tokens" in exc_info.value.detail
        assert "超过模型限制" in exc_info.value.detail

    def test_convert_response(self, service, mock_response):
        """测试响应转换."""
        result = service._convert_response(mock_response)

        assert isinstance(result, ChatCompletionServiceResponse)
        assert result.id == "test-id-123"
        assert result.model == "qwen-turbo"
        assert result.content == "I'm doing well, thank you!"
        assert result.finish_reason == "stop"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 8
        assert result.usage["total_tokens"] == 18

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, service, chat_request, mock_response):
        """测试聊天补全成功场景."""
        service.client.chat_completion = AsyncMock(return_value=mock_response)

        result = await service.chat_completion(chat_request)

        assert isinstance(result, ChatCompletionServiceResponse)
        assert result.content == "I'm doing well, thank you!"
        service.client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_authentication_error(self, service, chat_request):
        """测试聊天补全认证错误."""
        service.client.chat_completion = AsyncMock(
            side_effect=DashScopeAuthenticationError("认证失败")
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.chat_completion(chat_request)

        assert exc_info.value.status_code == 401
        assert "认证失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit_error(self, service, chat_request):
        """测试聊天补全速率限制错误."""
        service.client.chat_completion = AsyncMock(
            side_effect=DashScopeRateLimitError("速率限制")
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.chat_completion(chat_request)

        assert exc_info.value.status_code == 429
        assert "调用频率超限" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, service, chat_request):
        """测试聊天补全 API 错误."""
        service.client.chat_completion = AsyncMock(
            side_effect=DashScopeAPIError("API 错误")
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.chat_completion(chat_request)

        assert exc_info.value.status_code == 502
        assert "DashScope API 错误" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_stream_chat_completion_success(self, service, chat_request):
        """测试流式聊天补全成功场景."""
        # 模拟流式响应
        mock_stream_chunks = [
            StreamResponse(
                id="test-stream-123",
                model=QwenModel.TURBO,
                choices=[
                    StreamChoice(
                        index=0,
                        delta={"content": "Hello"},
                        finish_reason=None
                    )
                ],
                created=1234567890
            ),
            StreamResponse(
                id="test-stream-123",
                model=QwenModel.TURBO,
                choices=[
                    StreamChoice(
                        index=0,
                        delta={"content": " there!"},
                        finish_reason="stop"
                    )
                ],
                created=1234567890
            )
        ]

        async def mock_stream(request):
            for chunk in mock_stream_chunks:
                yield chunk

        service.client.stream_chat_completion = mock_stream

        chunks = []
        async for chunk in service.stream_chat_completion(chat_request):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " there!"
        assert chunks[1].finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, service):
        """测试健康检查 - 健康状态."""
        service.client.health_check = AsyncMock(return_value=True)

        result = await service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "dashscope"
        assert result["details"]["api_accessible"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, service):
        """测试健康检查 - 不健康状态."""
        service.client.health_check = AsyncMock(return_value=False)

        result = await service.health_check()

        assert result["status"] == "unhealthy"
        assert result["service"] == "dashscope"
        assert result["details"]["api_accessible"] is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, service):
        """测试健康检查 - 异常情况."""
        service.client.health_check = AsyncMock(side_effect=Exception("连接失败"))

        result = await service.health_check()

        assert result["status"] == "unhealthy"
        assert result["service"] == "dashscope"
        assert "连接失败" in result["error"]

    def test_get_supported_models(self, service):
        """测试获取支持的模型列表."""
        models = service.get_supported_models()

        assert len(models) > 0
        assert any(model["name"] == "qwen-turbo" for model in models)
        assert any(model["name"] == "qwen-plus" for model in models)

        # 验证模型信息结构
        turbo_model = next(m for m in models if m["name"] == "qwen-turbo")
        assert "display_name" in turbo_model
        assert "max_tokens" in turbo_model
        assert "context_length" in turbo_model
        assert "supports_search" in turbo_model
        assert "supports_vision" in turbo_model

    def test_convert_stream_chunk(self, service):
        """测试流式响应块转换."""
        stream_response = StreamResponse(
            id="stream-123",
            model=QwenModel.PLUS,
            choices=[
                StreamChoice(
                    index=0,
                    delta={"content": "Test content"},
                    finish_reason="stop"
                )
            ],
            created=1234567890
        )

        chunk = service._convert_stream_chunk(stream_response)

        assert isinstance(chunk, StreamChunk)
        assert chunk.id == "stream-123"
        assert chunk.model == "qwen-plus"
        assert chunk.content == "Test content"
        assert chunk.finish_reason == "stop"
        assert chunk.created == 1234567890

    def test_convert_stream_chunk_empty_choices(self, service):
        """测试流式响应块转换 - 空选择."""
        stream_response = StreamResponse(
            id="stream-123",
            model=QwenModel.PLUS,
            choices=[],
            created=1234567890
        )

        chunk = service._convert_stream_chunk(stream_response)

        assert chunk.content == ""
        assert chunk.finish_reason is None