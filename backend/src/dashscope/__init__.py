"""DashScope API integration package.

This package provides comprehensive integration with Alibaba's DashScope API
for Qwen model access, including request/response models, configuration
management, and support for async operations and streaming.
"""

from .config import DashScopeConfig, dashscope_config, get_dashscope_config
from .models import (
    APIResponse,
    BatchRequest,
    BatchResponse,
    Choice,
    DashScopeError,
    DashScopeRequest,
    DashScopeResponse,
    DashScopeStreamResponse,
    FinishReason,
    GenerationParameters,
    Message,
    MessageRole,
    QwenModel,
    RateLimitInfo,
    StreamChoice,
    StreamDelta,
    Usage,
)

__all__ = [
    # Configuration
    "DashScopeConfig",
    "dashscope_config",
    "get_dashscope_config",
    # Models
    "APIResponse",
    "BatchRequest",
    "BatchResponse",
    "Choice",
    "DashScopeError",
    "DashScopeRequest",
    "DashScopeResponse",
    "DashScopeStreamResponse",
    "FinishReason",
    "GenerationParameters",
    "Message",
    "MessageRole",
    "QwenModel",
    "RateLimitInfo",
    "StreamChoice",
    "StreamDelta",
    "Usage",
]

__version__ = "0.1.0"