"""Application configuration settings."""

from functools import lru_cache
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = Field(default="AI Prompt Generator API", description="Application name", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", description="Application version", alias="APP_VERSION")
    debug: bool = Field(default=False, description="Debug mode", alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host", alias="HOST")
    port: int = Field(default=8000, description="Server port", alias="PORT")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix", alias="API_V1_PREFIX")

    # CORS
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins (comma-separated)",
        alias="BACKEND_CORS_ORIGINS"
    )

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens",
        alias="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database
    database_url: str = Field(
        default="mysql+aiomysql://root:password@localhost:3306/prompt_sphere",
        description="Database connection URL",
        alias="DATABASE_URL"
    )
    database_host: str = Field(default="localhost", description="Database host", alias="DB_HOST")
    database_port: int = Field(default=3306, description="Database port", alias="DB_PORT")
    database_user: str = Field(default="root", description="Database user", alias="DB_USER")
    database_password: str = Field(default="password", description="Database password", alias="DB_PASSWORD")
    database_name: str = Field(default="prompt_sphere", description="Database name", alias="DB_NAME")
    database_pool_size: int = Field(default=10, description="Database connection pool size", alias="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections", alias="DB_MAX_OVERFLOW")

    # External APIs
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key", alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key", alias="ANTHROPIC_API_KEY")

    # DashScope API
    dashscope_api_key: Optional[str] = Field(
        default=None,
        description="DashScope API key for Qwen models",
        alias="DASHSCOPE_API_KEY"
    )
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com",
        description="DashScope API base URL",
        alias="DASHSCOPE_BASE_URL"
    )
    dashscope_default_model: str = Field(
        default="qwen-turbo",
        description="Default Qwen model to use",
        alias="DASHSCOPE_DEFAULT_MODEL"
    )
    dashscope_timeout: int = Field(
        default=60,
        description="DashScope request timeout in seconds",
        alias="DASHSCOPE_TIMEOUT"
    )
    dashscope_max_retries: int = Field(
        default=3,
        description="Maximum retries for DashScope requests",
        alias="DASHSCOPE_MAX_RETRIES"
    )
    dashscope_enable_streaming: bool = Field(
        default=True,
        description="Enable DashScope streaming responses",
        alias="DASHSCOPE_ENABLE_STREAMING"
    )

    # Redis Configuration
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (redis://localhost:6379/0)",
        alias="REDIS_URL"
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host",
        alias="REDIS_HOST"
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port",
        alias="REDIS_PORT"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password",
        alias="REDIS_PASSWORD"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database number",
        alias="REDIS_DB"
    )
    redis_pool_size: int = Field(
        default=10,
        description="Redis connection pool size",
        alias="REDIS_POOL_SIZE"
    )
    redis_timeout: int = Field(
        default=30,
        description="Redis connection timeout in seconds",
        alias="REDIS_TIMEOUT"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from string."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()