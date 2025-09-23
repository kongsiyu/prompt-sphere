"""DashScope API client implementation."""

import asyncio
import logging
from typing import Any, AsyncGenerator, Optional

import dashscope
from dashscope import Generation

from .auth import DashScopeAuth
from .config import DashScopeSettings
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    QwenModel,
    StreamChoice,
    StreamResponse,
    Usage,
)

logger = logging.getLogger(__name__)


class DashScopeClient:
    """Async DashScope API client for Qwen models."""

    def __init__(self, settings: Optional[DashScopeSettings] = None) -> None:
        """Initialize the DashScope client."""
        self.settings = settings or DashScopeSettings()
        self.auth = DashScopeAuth(self.settings)

        # Set global API key for dashscope SDK
        dashscope.api_key = self.auth.api_key

        logger.info("DashScope client initialized successfully")

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Create a chat completion using DashScope API."""
        try:
            logger.debug(f"Creating chat completion with model: {request.model.value}")

            # Convert our request format to DashScope format
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]

            # Prepare parameters
            params = {}
            if request.parameters:
                params.update({
                    "temperature": request.parameters.temperature,
                    "top_p": request.parameters.top_p,
                    "max_tokens": request.parameters.max_tokens,
                    "stop": request.parameters.stop,
                })

            # Make API call in thread pool to avoid blocking
            response = await asyncio.to_thread(
                Generation.call,
                model=request.model.value,
                messages=messages,
                **params
            )

            # Convert response to our format
            return self._convert_response(response, request.model)

        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise self._convert_exception(e)

    async def stream_chat_completion(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamResponse, None]:
        """Create a streaming chat completion."""
        try:
            logger.debug(f"Creating streaming chat completion with model: {request.model.value}")

            # Convert our request format to DashScope format
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]

            # Prepare parameters with streaming enabled
            params = {"stream": True}
            if request.parameters:
                params.update({
                    "temperature": request.parameters.temperature,
                    "top_p": request.parameters.top_p,
                    "max_tokens": request.parameters.max_tokens,
                    "stop": request.parameters.stop,
                })

            # Make streaming API call in thread pool
            def _make_stream_call():
                return Generation.call(
                    model=request.model.value,
                    messages=messages,
                    **params
                )

            responses = await asyncio.to_thread(_make_stream_call)

            # Yield converted stream responses
            for response in responses:
                yield self._convert_stream_response(response, request.model)

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {str(e)}")
            raise self._convert_exception(e)

    def _convert_response(
        self, response: Any, model: QwenModel
    ) -> ChatCompletionResponse:
        """Convert DashScope response to our format."""
        try:
            # Extract response data
            output = response.output
            usage_data = response.usage

            # Convert choices
            choices = []
            if hasattr(output, 'choices') and output.choices:
                for idx, choice_data in enumerate(output.choices):
                    message = ChatMessage(
                        role="assistant",
                        content=choice_data.message.content
                    )
                    choice = Choice(
                        index=idx,
                        message=message,
                        finish_reason=choice_data.finish_reason
                    )
                    choices.append(choice)
            else:
                # Single response format
                message = ChatMessage(
                    role="assistant",
                    content=output.text
                )
                choice = Choice(
                    index=0,
                    message=message,
                    finish_reason=output.finish_reason
                )
                choices.append(choice)

            # Convert usage
            usage = Usage(
                prompt_tokens=usage_data.input_tokens,
                completion_tokens=usage_data.output_tokens,
                total_tokens=usage_data.total_tokens
            )

            return ChatCompletionResponse(
                id=response.request_id,
                model=model,
                choices=choices,
                usage=usage,
                created=0  # DashScope doesn't provide timestamp
            )

        except Exception as e:
            logger.error(f"Failed to convert response: {str(e)}")
            raise ValueError(f"Invalid response format from DashScope: {str(e)}")

    def _convert_stream_response(
        self, response: Any, model: QwenModel
    ) -> StreamResponse:
        """Convert DashScope stream response to our format."""
        try:
            output = response.output

            # Convert stream choices
            choices = []
            if hasattr(output, 'choices') and output.choices:
                for idx, choice_data in enumerate(output.choices):
                    choice = StreamChoice(
                        index=idx,
                        delta={"content": choice_data.message.content},
                        finish_reason=choice_data.finish_reason
                    )
                    choices.append(choice)
            else:
                # Single response format
                choice = StreamChoice(
                    index=0,
                    delta={"content": output.text},
                    finish_reason=output.finish_reason
                )
                choices.append(choice)

            return StreamResponse(
                id=response.request_id,
                model=model,
                choices=choices,
                created=0  # DashScope doesn't provide timestamp
            )

        except Exception as e:
            logger.error(f"Failed to convert stream response: {str(e)}")
            raise ValueError(f"Invalid stream response format from DashScope: {str(e)}")

    def _convert_exception(self, e: Exception) -> Exception:
        """Convert DashScope exceptions to our format."""
        # TODO: Implement proper exception mapping in Stream C
        # For now, re-raise the original exception
        return e

    async def health_check(self) -> bool:
        """Check if the DashScope API is accessible."""
        try:
            # Simple test request to verify connectivity
            test_request = ChatCompletionRequest(
                model=QwenModel.QWEN_TURBO,
                messages=[ChatMessage(role="user", content="Hello")]
            )

            response = await self.chat_completion(test_request)
            return bool(response.choices)

        except Exception as e:
            logger.warning(f"DashScope health check failed: {str(e)}")
            return False