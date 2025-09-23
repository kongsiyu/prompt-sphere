"""DashScope API integration package."""

from .client import DashScopeClient
from .config import DashScopeSettings
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    DashScopeError,
    ErrorResponse,
    Message,
    MessageRole,
    ModelParameters,
    QwenMaxParameters,
    QwenModel,
    QwenPlusParameters,
    QwenTurboParameters,
    StreamResponse,
    Usage,
    create_default_parameters,
    get_model_limits,
    get_model_parameters,
)

__all__ = [
    # Client
    "DashScopeClient",
    # Configuration
    "DashScopeSettings",
    # Models and Enums
    "QwenModel",
    "MessageRole",
    "Message",
    "ModelParameters",
    "QwenTurboParameters",
    "QwenPlusParameters",
    "QwenMaxParameters",
    # Request/Response Models
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "StreamResponse",
    "Usage",
    # Error Models
    "DashScopeError",
    "ErrorResponse",
    # Utility Functions
    "get_model_parameters",
    "create_default_parameters",
    "get_model_limits",
]
