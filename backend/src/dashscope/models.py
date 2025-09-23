"""Pydantic models for DashScope API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class QwenModel(str, Enum):
    """Available Qwen model variants."""

    QWEN_TURBO = "qwen-turbo"
    QWEN_PLUS = "qwen-plus"
    QWEN_MAX = "qwen-max"
    QWEN_LONG = "qwen-long"


class MessageRole(str, Enum):
    """Message roles for conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(str, Enum):
    """Possible finish reasons for generation."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    NULL = "null"


class Message(BaseModel):
    """A single message in the conversation."""

    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class GenerationParameters(BaseModel):
    """Parameters for text generation."""

    max_tokens: Optional[int] = Field(
        default=1500,
        ge=1,
        le=6000,
        description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.85,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for randomness"
    )
    top_p: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Top-k sampling parameter"
    )
    repetition_penalty: Optional[float] = Field(
        default=1.1,
        ge=1.0,
        le=1.5,
        description="Penalty for repetition"
    )
    presence_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Penalty for token presence"
    )
    frequency_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Penalty for token frequency"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Stop sequences for generation"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible outputs"
    )

    @validator('stop')
    def validate_stop_sequences(cls, v):
        """Validate stop sequences."""
        if v is None:
            return v
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            if len(v) > 4:
                raise ValueError("Maximum 4 stop sequences allowed")
            return v
        raise ValueError("Stop must be string or list of strings")


class DashScopeRequest(BaseModel):
    """Request model for DashScope API calls."""

    model: QwenModel = Field(..., description="The Qwen model to use")
    messages: List[Message] = Field(..., description="List of conversation messages")
    parameters: Optional[GenerationParameters] = Field(
        default_factory=GenerationParameters,
        description="Generation parameters"
    )
    stream: bool = Field(default=False, description="Whether to stream the response")

    class Config:
        """Pydantic config."""
        use_enum_values = True

    @validator('messages')
    def validate_messages(cls, v):
        """Validate message list."""
        if not v:
            raise ValueError("At least one message is required")

        # Check for valid role sequence
        roles = [msg.role for msg in v]
        if roles[0] != MessageRole.SYSTEM and roles[0] != MessageRole.USER:
            raise ValueError("First message must be system or user")

        return v


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")


class Choice(BaseModel):
    """A single choice from the model response."""

    index: int = Field(..., description="Index of this choice")
    message: Message = Field(..., description="The generated message")
    finish_reason: FinishReason = Field(..., description="Reason why generation finished")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class DashScopeResponse(BaseModel):
    """Response model for DashScope API calls."""

    id: str = Field(..., description="Unique identifier for the response")
    model: str = Field(..., description="Model used for generation")
    created: int = Field(..., description="Unix timestamp of creation")
    choices: List[Choice] = Field(..., description="List of generated choices")
    usage: Usage = Field(..., description="Token usage information")
    object: str = Field(default="chat.completion", description="Object type")

    @property
    def content(self) -> str:
        """Get the content of the first choice."""
        if self.choices:
            return self.choices[0].message.content
        return ""

    @property
    def finish_reason(self) -> FinishReason:
        """Get the finish reason of the first choice."""
        if self.choices:
            return self.choices[0].finish_reason
        return FinishReason.NULL


class StreamDelta(BaseModel):
    """Delta object for streaming responses."""

    role: Optional[MessageRole] = Field(default=None, description="Role if this is the first delta")
    content: Optional[str] = Field(default=None, description="Content delta")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class StreamChoice(BaseModel):
    """A single choice in a streaming response."""

    index: int = Field(..., description="Index of this choice")
    delta: StreamDelta = Field(..., description="The delta content")
    finish_reason: Optional[FinishReason] = Field(default=None, description="Finish reason if completed")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class DashScopeStreamResponse(BaseModel):
    """Response model for streaming DashScope API calls."""

    id: str = Field(..., description="Unique identifier for the response")
    model: str = Field(..., description="Model used for generation")
    created: int = Field(..., description="Unix timestamp of creation")
    choices: List[StreamChoice] = Field(..., description="List of streaming choices")
    object: str = Field(default="chat.completion.chunk", description="Object type")

    @property
    def content_delta(self) -> str:
        """Get the content delta of the first choice."""
        if self.choices and self.choices[0].delta.content:
            return self.choices[0].delta.content
        return ""

    @property
    def is_finished(self) -> bool:
        """Check if the stream is finished."""
        if self.choices:
            return self.choices[0].finish_reason is not None
        return False


class DashScopeError(BaseModel):
    """Error response from DashScope API."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(default=None, description="Request ID for debugging")


class RateLimitInfo(BaseModel):
    """Rate limit information from API headers."""

    limit: Optional[int] = Field(default=None, description="Request limit per window")
    remaining: Optional[int] = Field(default=None, description="Remaining requests in window")
    reset: Optional[datetime] = Field(default=None, description="Time when limit resets")
    retry_after: Optional[int] = Field(default=None, description="Seconds to wait before retry")


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Union[DashScopeResponse, DashScopeStreamResponse]] = Field(
        default=None, description="Response data if successful"
    )
    error: Optional[DashScopeError] = Field(default=None, description="Error information if failed")
    rate_limit: Optional[RateLimitInfo] = Field(default=None, description="Rate limit information")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    latency_ms: Optional[float] = Field(default=None, description="Request latency in milliseconds")


class BatchRequest(BaseModel):
    """Request model for batch processing."""

    requests: List[DashScopeRequest] = Field(..., description="List of requests to process")
    batch_id: Optional[str] = Field(default=None, description="Optional batch identifier")
    max_concurrent: int = Field(default=5, ge=1, le=10, description="Maximum concurrent requests")

    @validator('requests')
    def validate_batch_size(cls, v):
        """Validate batch size."""
        if len(v) > 100:
            raise ValueError("Maximum batch size is 100 requests")
        return v


class BatchResponse(BaseModel):
    """Response model for batch processing."""

    batch_id: str = Field(..., description="Batch identifier")
    responses: List[APIResponse] = Field(..., description="List of individual responses")
    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    total_tokens: int = Field(..., description="Total tokens used across all requests")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")