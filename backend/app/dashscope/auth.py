"""DashScope API authentication module."""

import os
from typing import Optional

from .config import DashScopeSettings


class DashScopeAuth:
    """Handle DashScope API authentication."""

    def __init__(self, settings: Optional[DashScopeSettings] = None) -> None:
        """Initialize authentication with settings."""
        self.settings = settings or DashScopeSettings()
        self._api_key: Optional[str] = None
        self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Validate and set API key from settings or environment."""
        api_key = self.settings.api_key or os.getenv("DASHSCOPE_API_KEY")

        if not api_key:
            raise ValueError(
                "DashScope API key not found. Please set DASHSCOPE_API_KEY environment variable "
                "or configure it in settings."
            )

        api_key = api_key.strip()
        if len(api_key) < 10:
            raise ValueError("Invalid DashScope API key format")

        self._api_key = api_key

    @property
    def api_key(self) -> str:
        """Get the validated API key."""
        if not self._api_key:
            raise ValueError("API key not initialized")
        return self._api_key

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def is_authenticated(self) -> bool:
        """Check if authentication is properly configured."""
        try:
            return bool(self._api_key and len(self._api_key) >= 10)
        except Exception:
            return False

    def refresh_api_key(self) -> None:
        """Refresh API key from environment or settings."""
        self._api_key = None
        self._validate_api_key()