"""DashScope API configuration settings."""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class DashScopeSettings(BaseSettings):
    """DashScope API configuration settings."""

    # API Configuration
    api_key: Optional[str] = Field(
        default=None,
        description="DashScope API key for authentication",
        alias="DASHSCOPE_API_KEY"
    )

    base_url: str = Field(
        default="https://dashscope.aliyuncs.com",
        description="DashScope API base URL",
        alias="DASHSCOPE_BASE_URL"
    )

    # Model Configuration
    default_model: str = Field(
        default="qwen-turbo",
        description="Default Qwen model to use",
        alias="DASHSCOPE_DEFAULT_MODEL"
    )

    # Request Configuration
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds",
        alias="DASHSCOPE_TIMEOUT"
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
        alias="DASHSCOPE_MAX_RETRIES"
    )

    retry_delay: float = Field(
        default=1.0,
        description="Initial delay between retries in seconds",
        alias="DASHSCOPE_RETRY_DELAY"
    )

    # Rate Limiting
    requests_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute for rate limiting",
        alias="DASHSCOPE_REQUESTS_PER_MINUTE"
    )

    requests_per_day: int = Field(
        default=1000,
        description="Maximum requests per day for rate limiting",
        alias="DASHSCOPE_REQUESTS_PER_DAY"
    )

    # Streaming Configuration
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses",
        alias="DASHSCOPE_ENABLE_STREAMING"
    )

    stream_chunk_size: int = Field(
        default=1024,
        description="Size of streaming response chunks in bytes",
        alias="DASHSCOPE_STREAM_CHUNK_SIZE"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        return v

    @field_validator("retry_delay")
    @classmethod
    def validate_retry_delay(cls, v):
        """Validate retry delay value."""
        if v < 0:
            raise ValueError("Retry delay cannot be negative")
        return v

    @field_validator("requests_per_minute", "requests_per_day")
    @classmethod
    def validate_rate_limits(cls, v):
        """Validate rate limit values."""
        if v <= 0:
            raise ValueError("Rate limits must be positive")
        return v

    @field_validator("stream_chunk_size")
    @classmethod
    def validate_stream_chunk_size(cls, v):
        """Validate stream chunk size."""
        if v <= 0:
            raise ValueError("Stream chunk size must be positive")
        return v

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"