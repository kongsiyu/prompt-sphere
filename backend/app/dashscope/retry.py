"""Retry logic with exponential backoff for DashScope API."""

import asyncio
import logging
import random
from typing import Any, Callable, Optional, Type, Union

from .config import DashScopeSettings
from .exceptions import (
    DashScopeError,
    DashScopeRateLimitError,
    DashScopeServiceUnavailableError,
    DashScopeTimeoutError,
)

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None
    ) -> None:
        """Initialize retry configuration."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        # Default retryable exceptions
        if retryable_exceptions is None:
            retryable_exceptions = (
                DashScopeRateLimitError,
                DashScopeServiceUnavailableError,
                DashScopeTimeoutError,
                ConnectionError,
                TimeoutError,
            )
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        if attempt <= 0:
            return 0.0

        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter to avoid thundering herd
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)

    def is_retryable(self, exception: Exception) -> bool:
        """Check if an exception should trigger a retry."""
        return isinstance(exception, self.retryable_exceptions)


async def with_retry(
    func: Callable,
    *args,
    retry_config: Optional[RetryConfig] = None,
    settings: Optional[DashScopeSettings] = None,
    **kwargs
) -> Any:
    """Execute a function with retry logic and exponential backoff."""
    if retry_config is None:
        if settings is None:
            settings = DashScopeSettings()
        retry_config = RetryConfig(
            max_retries=settings.max_retries,
            base_delay=settings.retry_delay
        )

    last_exception: Optional[Exception] = None

    for attempt in range(retry_config.max_retries + 1):
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            # Check if this is the last attempt
            if attempt >= retry_config.max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {retry_config.max_retries + 1} attempts: {e}"
                )
                raise

            # Check if exception is retryable
            if not retry_config.is_retryable(e):
                logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                raise

            # Handle rate limit errors specially
            if isinstance(e, DashScopeRateLimitError) and e.retry_after:
                delay = e.retry_after
                logger.warning(
                    f"Rate limited on attempt {attempt + 1} for {func.__name__}, "
                    f"waiting {delay}s as suggested by API"
                )
            else:
                delay = retry_config.calculate_delay(attempt + 1)
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {e}, "
                    f"retrying in {delay:.2f}s"
                )

            if delay > 0:
                await asyncio.sleep(delay)

    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected end of retry loop")


class AsyncRetryDecorator:
    """Decorator for adding retry logic to async functions."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None
    ) -> None:
        """Initialize retry decorator."""
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions
        )

    def __call__(self, func: Callable) -> Callable:
        """Apply retry logic to the function."""
        if not asyncio.iscoroutinefunction(func):
            raise ValueError("AsyncRetryDecorator can only be used with async functions")

        async def wrapper(*args, **kwargs):
            return await with_retry(
                func,
                *args,
                retry_config=self.retry_config,
                **kwargs
            )

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__

        return wrapper


# Convenience decorator with default settings
def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable:
    """Decorator for retrying DashScope API calls on failure."""
    return AsyncRetryDecorator(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )