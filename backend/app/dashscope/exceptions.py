"""Custom exceptions for DashScope API integration."""

from typing import Optional, Dict, Any


class DashScopeError(Exception):
    """Base exception for DashScope API errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ) -> None:
        """Initialize DashScope error."""
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def __str__(self) -> str:
        """String representation of the error."""
        if self.code:
            return f"DashScope API Error [{self.code}]: {self.message}"
        return f"DashScope API Error: {self.message}"


class DashScopeAPIError(DashScopeError):
    """Exception raised for DashScope API-related errors."""
    pass


class DashScopeAuthenticationError(DashScopeError):
    """Exception raised for authentication-related errors."""
    pass


class DashScopeRateLimitError(DashScopeError):
    """Exception raised when API rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ) -> None:
        """Initialize rate limit error."""
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class DashScopeTimeoutError(DashScopeError):
    """Exception raised when API requests timeout."""
    pass


class DashScopeValidationError(DashScopeError):
    """Exception raised for request validation errors."""
    pass


class DashScopeServiceUnavailableError(DashScopeError):
    """Exception raised when DashScope service is unavailable."""
    pass


class DashScopeQuotaExceededError(DashScopeError):
    """Exception raised when API quota is exceeded."""
    pass


def map_dashscope_error(error: Exception, response_data: Optional[Dict[str, Any]] = None) -> DashScopeError:
    """Map DashScope SDK errors to our custom exceptions."""
    if response_data is None:
        response_data = {}

    error_message = str(error)
    error_code = response_data.get("code")
    status_code = response_data.get("status")

    # Map specific error codes to custom exceptions
    if error_code == "InvalidApiKey" or "authentication" in error_message.lower():
        return DashScopeAuthenticationError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code
        )

    if error_code == "RateLimitExceeded" or "rate limit" in error_message.lower():
        retry_after = response_data.get("retry_after")
        return DashScopeRateLimitError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code,
            retry_after=retry_after
        )

    if error_code == "RequestTimeout" or "timeout" in error_message.lower():
        return DashScopeTimeoutError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code
        )

    if error_code == "ValidationError" or "validation" in error_message.lower():
        return DashScopeValidationError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code
        )

    if error_code == "ServiceUnavailable" or status_code in [502, 503, 504]:
        return DashScopeServiceUnavailableError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code
        )

    if error_code == "QuotaExceeded" or "quota" in error_message.lower():
        return DashScopeQuotaExceededError(
            message=error_message,
            code=error_code,
            details=response_data,
            status_code=status_code
        )

    # Default to generic API error
    return DashScopeAPIError(
        message=error_message,
        code=error_code,
        details=response_data,
        status_code=status_code
    )