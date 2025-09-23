"""DashScope service layer for chat completion API integration."""

import logging
from typing import AsyncGenerator, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.dashscope import DashScopeClient, DashScopeSettings
from app.dashscope.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    MessageRole,
    QwenModel,
    ModelParameters,
    StreamResponse,
    get_model_limits,
)
from app.dashscope.exceptions import (
    DashScopeAPIError,
    DashScopeAuthenticationError,
    DashScopeRateLimitError,
    DashScopeError,
)

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """服务层聊天请求模型."""

    messages: list[str] = []
    model: str = "qwen-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatMessage(BaseModel):
    """聊天消息模型."""

    role: str
    content: str


class ChatCompletionServiceResponse(BaseModel):
    """服务层响应模型."""

    id: str
    model: str
    content: str
    finish_reason: str
    usage: dict
    created: int


class StreamChunk(BaseModel):
    """流式响应块."""

    id: str
    model: str
    content: str
    finish_reason: Optional[str] = None
    created: int


class DashScopeService:
    """DashScope 服务层，提供聊天补全功能."""

    def __init__(self, settings: Optional[DashScopeSettings] = None):
        """初始化 DashScope 服务."""
        self.settings = settings or DashScopeSettings()
        self.client = DashScopeClient(self.settings)
        logger.info("DashScope service initialized")

    async def chat_completion(
        self,
        request: ChatRequest
    ) -> ChatCompletionServiceResponse:
        """创建聊天补全."""
        try:
            # 验证模型
            model = self._validate_model(request.model)

            # 构建消息列表
            messages = self._build_messages(request.messages)

            # 构建参数
            parameters = self._build_parameters(request, model)

            # 创建 DashScope 请求
            dashscope_request = ChatCompletionRequest(
                model=model,
                messages=messages,
                parameters=parameters
            )

            # 调用客户端
            response = await self.client.chat_completion(dashscope_request)

            # 转换为服务层响应格式
            return self._convert_response(response)

        except DashScopeAuthenticationError as e:
            logger.error(f"DashScope authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="DashScope API 认证失败"
            )
        except DashScopeRateLimitError as e:
            logger.error(f"DashScope rate limit exceeded: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API 调用频率超限，请稍后重试"
            )
        except DashScopeAPIError as e:
            logger.error(f"DashScope API error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"DashScope API 错误: {str(e)}"
            )
        except DashScopeError as e:
            logger.error(f"DashScope error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DashScope 服务错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="聊天补全服务内部错误"
            )

    async def stream_chat_completion(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """创建流式聊天补全."""
        try:
            # 验证模型
            model = self._validate_model(request.model)

            # 构建消息列表
            messages = self._build_messages(request.messages)

            # 构建参数（强制启用流式）
            parameters = self._build_parameters(request, model)
            parameters.stream = True

            # 创建 DashScope 请求
            dashscope_request = ChatCompletionRequest(
                model=model,
                messages=messages,
                parameters=parameters
            )

            # 调用客户端流式接口
            async for chunk in self.client.stream_chat_completion(dashscope_request):
                yield self._convert_stream_chunk(chunk)

        except DashScopeAuthenticationError as e:
            logger.error(f"DashScope authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="DashScope API 认证失败"
            )
        except DashScopeRateLimitError as e:
            logger.error(f"DashScope rate limit exceeded: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API 调用频率超限，请稍后重试"
            )
        except DashScopeAPIError as e:
            logger.error(f"DashScope API error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"DashScope API 错误: {str(e)}"
            )
        except DashScopeError as e:
            logger.error(f"DashScope error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DashScope 服务错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in stream chat completion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="流式聊天补全服务内部错误"
            )

    async def health_check(self) -> dict:
        """健康检查."""
        try:
            is_healthy = await self.client.health_check()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "dashscope",
                "details": {
                    "api_accessible": is_healthy,
                    "settings_configured": bool(self.settings.api_key)
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "service": "dashscope",
                "error": str(e)
            }

    def get_supported_models(self) -> list[dict]:
        """获取支持的模型列表."""
        models = []
        for model in QwenModel:
            limits = get_model_limits(model)
            models.append({
                "name": model.value,
                "display_name": model.value.replace("-", " ").title(),
                "max_tokens": limits["max_tokens"],
                "context_length": limits["context_length"],
                "supports_search": limits["supports_search"],
                "supports_vision": limits["supports_vision"]
            })
        return models

    def _validate_model(self, model_name: str) -> QwenModel:
        """验证并转换模型名称."""
        try:
            return QwenModel(model_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的模型: {model_name}. 支持的模型: {[m.value for m in QwenModel]}"
            )

    def _build_messages(self, message_contents: list[str]) -> list[Message]:
        """构建消息列表."""
        if not message_contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息列表不能为空"
            )

        messages = []
        for i, content in enumerate(message_contents):
            if not content or not content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"消息 {i+1} 内容不能为空"
                )

            # 简单的角色分配：奇数索引为用户，偶数索引为助手
            # 第一条消息总是用户消息
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT

            messages.append(Message(role=role, content=content.strip()))

        return messages

    def _build_parameters(self, request: ChatRequest, model: QwenModel) -> ModelParameters:
        """构建模型参数."""
        limits = get_model_limits(model)

        # 验证并设置 max_tokens
        max_tokens = request.max_tokens
        if max_tokens is not None:
            if max_tokens > limits["max_tokens"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"max_tokens ({max_tokens}) 超过模型限制 ({limits['max_tokens']})"
                )
        else:
            max_tokens = min(2048, limits["max_tokens"])  # 默认值

        # 验证温度参数
        if not 0.0 <= request.temperature <= 2.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="temperature 必须在 0.0 到 2.0 之间"
            )

        return ModelParameters(
            temperature=request.temperature,
            max_tokens=max_tokens,
            stream=request.stream
        )

    def _convert_response(self, response: ChatCompletionResponse) -> ChatCompletionServiceResponse:
        """转换 DashScope 响应为服务层响应."""
        # 获取第一个选择的内容
        choice = response.choices[0] if response.choices else None
        if not choice:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DashScope 返回空响应"
            )

        return ChatCompletionServiceResponse(
            id=response.id,
            model=response.model.value,
            content=choice.message.content,
            finish_reason=choice.finish_reason.value,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            created=response.created
        )

    def _convert_stream_chunk(self, chunk: StreamResponse) -> StreamChunk:
        """转换流式响应块."""
        choice = chunk.choices[0] if chunk.choices else None
        if not choice:
            content = ""
            finish_reason = None
        else:
            content = choice.delta.get("content", "")
            finish_reason = choice.finish_reason.value if choice.finish_reason else None

        return StreamChunk(
            id=chunk.id,
            model=chunk.model.value,
            content=content,
            finish_reason=finish_reason,
            created=chunk.created
        )