"""DashScope API 路由端点."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies.dashscope import DashScopeServiceDep, HealthyDashScopeServiceDep
from app.services.dashscope_service import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()


# API 请求/响应模型
class ChatCompletionAPIRequest(BaseModel):
    """聊天补全 API 请求模型."""

    messages: list[str] = Field(
        ...,
        min_length=1,
        description="对话消息列表，按时间顺序排列",
        example=["你好", "你好！有什么可以帮助你的吗？", "请介绍一下自己"]
    )
    model: str = Field(
        default="qwen-turbo",
        description="使用的模型名称",
        example="qwen-turbo"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="控制输出随机性的温度参数 (0.0-2.0)",
        example=0.7
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="生成的最大令牌数",
        example=2048
    )
    stream: bool = Field(
        default=False,
        description="是否启用流式响应",
        example=False
    )


class ChatCompletionAPIResponse(BaseModel):
    """聊天补全 API 响应模型."""

    id: str = Field(..., description="请求的唯一标识符")
    model: str = Field(..., description="使用的模型名称")
    content: str = Field(..., description="生成的文本内容")
    finish_reason: str = Field(..., description="生成结束的原因")
    usage: dict = Field(..., description="令牌使用统计")
    created: int = Field(..., description="创建时间戳")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型."""

    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    details: Optional[dict] = Field(default=None, description="详细信息")
    error: Optional[str] = Field(default=None, description="错误信息")


class ModelsResponse(BaseModel):
    """支持的模型列表响应."""

    models: list[dict] = Field(..., description="支持的模型列表")


@router.post(
    "/chat/completions",
    response_model=ChatCompletionAPIResponse,
    summary="创建聊天补全",
    description="使用 DashScope API 创建聊天补全响应",
    status_code=status.HTTP_200_OK
)
async def create_chat_completion(
    request: ChatCompletionAPIRequest,
    service: DashScopeServiceDep
) -> ChatCompletionAPIResponse:
    """创建聊天补全."""
    try:
        logger.info(f"Creating chat completion with model: {request.model}")

        # 转换为服务层请求格式
        service_request = ChatRequest(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False  # 强制非流式
        )

        # 调用服务层
        response = await service.chat_completion(service_request)

        logger.info(f"Chat completion created successfully, ID: {response.id}")
        return ChatCompletionAPIResponse(**response.dict())

    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat completion endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="聊天补全服务内部错误"
        )


@router.post(
    "/chat/completions/stream",
    summary="创建流式聊天补全",
    description="使用 DashScope API 创建流式聊天补全响应",
    status_code=status.HTTP_200_OK
)
async def create_stream_chat_completion(
    request: ChatCompletionAPIRequest,
    service: DashScopeServiceDep
):
    """创建流式聊天补全."""
    try:
        logger.info(f"Creating stream chat completion with model: {request.model}")

        # 转换为服务层请求格式
        service_request = ChatRequest(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True  # 强制流式
        )

        # 定义流式响应生成器
        async def generate_stream():
            try:
                async for chunk in service.stream_chat_completion(service_request):
                    # 转换为 SSE 格式
                    chunk_data = chunk.dict()
                    yield f"data: {chunk_data}\\n\\n"

                # 发送结束标记
                yield "data: [DONE]\\n\\n"

            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                error_data = {
                    "error": {
                        "message": str(e),
                        "type": "stream_error"
                    }
                }
                yield f"data: {error_data}\\n\\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )

    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Unexpected error in stream chat completion endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="流式聊天补全服务内部错误"
        )


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="获取支持的模型列表",
    description="获取 DashScope 支持的所有模型及其能力",
    status_code=status.HTTP_200_OK
)
async def get_models(
    service: DashScopeServiceDep
) -> ModelsResponse:
    """获取支持的模型列表."""
    try:
        logger.info("Fetching supported models list")
        models = service.get_supported_models()
        return ModelsResponse(models=models)

    except Exception as e:
        logger.error(f"Failed to fetch models list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型列表失败"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="DashScope 服务健康检查",
    description="检查 DashScope API 连接和服务状态",
    status_code=status.HTTP_200_OK
)
async def health_check(
    service: DashScopeServiceDep
) -> HealthCheckResponse:
    """DashScope 服务健康检查."""
    try:
        logger.info("Performing DashScope health check")
        health = await service.health_check()

        # 根据健康状态设置适当的 HTTP 状态码
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health
            )

        return HealthCheckResponse(**health)

    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            service="dashscope",
            error=str(e)
        )


@router.get(
    "/test",
    summary="DashScope 服务连接测试",
    description="测试 DashScope API 连接（需要健康的服务）",
    status_code=status.HTTP_200_OK
)
async def test_connection(
    service: HealthyDashScopeServiceDep
) -> dict:
    """测试 DashScope API 连接。

    此端点要求服务必须是健康状态，否则会返回 503 错误。
    """
    try:
        logger.info("Testing DashScope API connection")

        # 执行一个简单的测试请求
        test_request = ChatRequest(
            messages=["Hello"],
            model="qwen-turbo",
            temperature=0.1,
            max_tokens=10
        )

        response = await service.chat_completion(test_request)

        return {
            "status": "success",
            "message": "DashScope API 连接测试成功",
            "test_response_id": response.id,
            "model": response.model
        }

    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DashScope API 连接测试失败: {str(e)}"
        )