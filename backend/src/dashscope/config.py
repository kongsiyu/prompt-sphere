"""Configuration management for DashScope API integration."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class RetryConfig(BaseSettings):
    """Configuration for retry logic."""

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of retries")
    base_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Base delay in seconds")
    max_delay: float = Field(default=60.0, ge=1.0, le=300.0, description="Maximum delay in seconds")
    exponential_base: float = Field(default=2.0, ge=1.1, le=10.0, description="Exponential backoff base")
    jitter: bool = Field(default=True, description="Add random jitter to delays")

    @validator('max_delay')
    def validate_max_delay(cls, v, values):
        """Ensure max_delay is greater than base_delay."""
        if 'base_delay' in values and v < values['base_delay']:
            raise ValueError("max_delay must be greater than or equal to base_delay")
        return v

    class Config:
        """Pydantic config."""
        env_prefix = "DASHSCOPE_RETRY_"


class RateLimitConfig(BaseSettings):
    """Configuration for rate limiting."""

    requests_per_minute: int = Field(
        default=300,
        ge=1,
        le=10000,
        description="Maximum requests per minute"
    )
    tokens_per_minute: int = Field(
        default=200000,
        ge=1000,
        le=2000000,
        description="Maximum tokens per minute"
    )
    concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent requests"
    )
    queue_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Maximum time to wait in queue (seconds)"
    )
    enable_queue: bool = Field(default=True, description="Enable request queueing")

    class Config:
        """Pydantic config."""
        env_prefix = "DASHSCOPE_RATE_LIMIT_"


class TimeoutConfig(BaseSettings):
    """Configuration for request timeouts."""

    connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Connection timeout in seconds"
    )
    read_timeout: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Read timeout in seconds"
    )
    write_timeout: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Write timeout in seconds"
    )
    pool_timeout: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Connection pool timeout in seconds"
    )

    class Config:
        """Pydantic config."""
        env_prefix = "DASHSCOPE_TIMEOUT_"


class ModelConfig(BaseSettings):
    """Configuration for model-specific settings."""

    default_model: str = Field(default="qwen-turbo", description="Default model to use")
    max_tokens_turbo: int = Field(default=1500, ge=1, le=6000, description="Max tokens for qwen-turbo")
    max_tokens_plus: int = Field(default=6000, ge=1, le=6000, description="Max tokens for qwen-plus")
    max_tokens_max: int = Field(default=6000, ge=1, le=6000, description="Max tokens for qwen-max")
    max_tokens_long: int = Field(default=28000, ge=1, le=28000, description="Max tokens for qwen-long")

    default_temperature: float = Field(default=0.85, ge=0.0, le=2.0, description="Default temperature")
    default_top_p: float = Field(default=0.8, ge=0.0, le=1.0, description="Default top_p")
    default_repetition_penalty: float = Field(
        default=1.1,
        ge=1.0,
        le=1.5,
        description="Default repetition penalty"
    )

    @validator('default_model')
    def validate_default_model(cls, v):
        """Validate default model is supported."""
        supported_models = {"qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"}
        if v not in supported_models:
            raise ValueError(f"Default model must be one of: {supported_models}")
        return v

    def get_max_tokens_for_model(self, model: str) -> int:
        """Get maximum tokens for a specific model."""
        model_limits = {
            "qwen-turbo": self.max_tokens_turbo,
            "qwen-plus": self.max_tokens_plus,
            "qwen-max": self.max_tokens_max,
            "qwen-long": self.max_tokens_long,
        }
        return model_limits.get(model, self.max_tokens_turbo)

    class Config:
        """Pydantic config."""
        env_prefix = "DASHSCOPE_MODEL_"


class LoggingConfig(BaseSettings):
    """Configuration for logging."""

    log_level: str = Field(default="INFO", description="Logging level")
    log_requests: bool = Field(default=True, description="Log API requests")
    log_responses: bool = Field(default=False, description="Log API responses (sensitive)")
    log_errors: bool = Field(default=True, description="Log API errors")
    log_performance: bool = Field(default=True, description="Log performance metrics")
    mask_api_key: bool = Field(default=True, description="Mask API key in logs")

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    class Config:
        """Pydantic config."""
        env_prefix = "DASHSCOPE_LOG_"


class DashScopeConfig(BaseSettings):
    """Main configuration for DashScope integration."""

    # API Configuration
    api_key: Optional[str] = Field(
        default=None,
        description="DashScope API key",
        alias="DASHSCOPE_API_KEY"
    )
    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        description="DashScope API base URL",
        alias="DASHSCOPE_BASE_URL"
    )

    # Feature flags
    enable_streaming: bool = Field(default=True, description="Enable streaming support")
    enable_async: bool = Field(default=True, description="Enable async operations")
    enable_batch: bool = Field(default=True, description="Enable batch processing")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring and metrics")

    # Environment
    environment: str = Field(default="production", description="Environment (development/staging/production)")

    # Sub-configurations
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Rate limit configuration")
    timeout: TimeoutConfig = Field(default_factory=TimeoutConfig, description="Timeout configuration")
    model: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")

    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if v is None:
            return v
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("API key must be a non-empty string")
        if len(v) < 10:
            raise ValueError("API key appears to be too short")
        return v.strip()

    @validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = {"development", "staging", "production"}
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def get_masked_api_key(self) -> str:
        """Get masked API key for logging."""
        if not self.api_key:
            return "None"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}{'*' * (len(self.api_key) - 8)}{self.api_key[-4:]}"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        env_prefix = "DASHSCOPE_"


@lru_cache()
def get_dashscope_config() -> DashScopeConfig:
    """Get cached DashScope configuration instance."""
    return DashScopeConfig()


# Global configuration instance
dashscope_config = get_dashscope_config()