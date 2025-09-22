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

    # External APIs
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key", alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key", alias="ANTHROPIC_API_KEY")

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