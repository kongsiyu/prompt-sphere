"""Pydantic models for DashScope API requests and responses."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# Enums for Model Variants and Parameters
class QwenModel(str, Enum):
    """Supported Qwen model variants."""

    TURBO = "qwen-turbo"
    PLUS = "qwen-plus"
    MAX = "qwen-max"
    VLIT = "qwen-vl-plus"  # Vision-Language model


class MessageRole(str, Enum):
    """Message roles in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(str, Enum):
    """Possible finish reasons for completions."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"
    NULL = "null"  # DashScope sometimes returns 'null' as string


# Request Models
class Message(BaseModel):
    """A single message in the conversation."""

    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class ModelParameters(BaseModel):
    """Model parameters for different Qwen variants."""

    # Common parameters
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness in output generation"
    )

    top_p: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Controls diversity via nucleus sampling"
    )

    top_k: Optional[int] = Field(
        default=50,
        ge=1,
        le=100,
        description="Controls diversity by limiting token choices"
    )

    max_tokens: Optional[int] = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum number of tokens to generate"
    )

    presence_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token presence"
    )

    frequency_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token frequency"
    )

    repetition_penalty: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Penalty for repetition"
    )

    # Stopping criteria
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Stop sequences for generation"
    )

    # Streaming
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )

    # Model-specific parameters
    enable_search: Optional[bool] = Field(
        default=False,
        description="Enable web search for Qwen-Max (only available for certain models)"
    )


class QwenTurboParameters(ModelParameters):
    """Parameters specific to Qwen-Turbo model."""

    max_tokens: Optional[int] = Field(
        default=1500,
        ge=1,
        le=2048,
        description="Maximum tokens for Qwen-Turbo"
    )


class QwenPlusParameters(ModelParameters):
    """Parameters specific to Qwen-Plus model."""

    max_tokens: Optional[int] = Field(
        default=4096,
        ge=1,
        le=6144,
        description="Maximum tokens for Qwen-Plus"
    )


class QwenMaxParameters(ModelParameters):
    """Parameters specific to Qwen-Max model."""

    max_tokens: Optional[int] = Field(
        default=6144,
        ge=1,
        le=8192,
        description="Maximum tokens for Qwen-Max"
    )

    enable_search: Optional[bool] = Field(
        default=False,
        description="Enable web search capability for Qwen-Max"
    )


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion API."""

    model: QwenModel = Field(..., description="The model to use for completion")
    messages: List[Message] = Field(..., min_length=1, description="List of messages in the conversation")
    parameters: Optional[ModelParameters] = Field(default=None, description="Model parameters")

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v):
        """Validate messages list."""
        if not v:
            raise ValueError("Messages list cannot be empty")

        # Check for valid role sequence
        roles = [msg.role for msg in v]

        # First message should typically be system or user
        if roles[0] not in [MessageRole.SYSTEM, MessageRole.USER]:
            raise ValueError("First message should be system or user role")

        return v


# Response Models
class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")


class Choice(BaseModel):
    """A single choice in the completion response."""

    index: int = Field(..., description="Index of this choice")
    message: Message = Field(..., description="The generated message")
    finish_reason: FinishReason = Field(..., description="Reason why generation finished")


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion API."""

    id: str = Field(..., description="Unique identifier for the completion")
    model: QwenModel = Field(..., description="Model used for the completion")
    choices: List[Choice] = Field(..., description="List of completion choices")
    usage: Usage = Field(..., description="Token usage information")
    created: int = Field(..., description="Unix timestamp of creation")

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, v):
        """Validate choices list."""
        if not v:
            raise ValueError("Choices list cannot be empty")
        return v


# Streaming Response Models
class StreamChoice(BaseModel):
    """A single choice in streaming response."""

    index: int = Field(..., description="Index of this choice")
    delta: Dict[str, Any] = Field(..., description="Delta content for this chunk")
    finish_reason: Optional[FinishReason] = Field(default=None, description="Reason why generation finished")


class StreamResponse(BaseModel):
    """Streaming response chunk."""

    id: str = Field(..., description="Unique identifier for the completion")
    model: QwenModel = Field(..., description="Model used for the completion")
    choices: List[StreamChoice] = Field(..., description="List of streaming choices")
    created: int = Field(..., description="Unix timestamp of creation")


# Error Models
class DashScopeError(BaseModel):
    """Error response from DashScope API."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    param: Optional[str] = Field(default=None, description="Parameter that caused the error")


class ErrorResponse(BaseModel):
    """Complete error response wrapper."""

    error: DashScopeError = Field(..., description="Error details")


# Model Configuration
def get_model_parameters(model: QwenModel) -> type[ModelParameters]:
    """Get the appropriate parameter class for a model."""

    parameter_mapping = {
        QwenModel.TURBO: QwenTurboParameters,
        QwenModel.PLUS: QwenPlusParameters,
        QwenModel.MAX: QwenMaxParameters,
        QwenModel.VLIT: ModelParameters,  # Use base parameters for VL model
    }

    return parameter_mapping.get(model, ModelParameters)


def create_default_parameters(model: QwenModel) -> ModelParameters:
    """Create default parameters for a specific model."""

    parameter_class = get_model_parameters(model)
    return parameter_class()


# Model Limits and Capabilities
MODEL_LIMITS = {
    QwenModel.TURBO: {
        "max_tokens": 2048,
        "context_length": 8192,
        "supports_search": False,
        "supports_vision": False,
    },
    QwenModel.PLUS: {
        "max_tokens": 6144,
        "context_length": 32768,
        "supports_search": False,
        "supports_vision": False,
    },
    QwenModel.MAX: {
        "max_tokens": 8192,
        "context_length": 32768,
        "supports_search": True,
        "supports_vision": False,
    },
    QwenModel.VLIT: {
        "max_tokens": 2048,
        "context_length": 8192,
        "supports_search": False,
        "supports_vision": True,
    },
}


def get_model_limits(model: QwenModel) -> Dict[str, Any]:
    """Get limits and capabilities for a specific model."""
    return MODEL_LIMITS.get(model, MODEL_LIMITS[QwenModel.TURBO])