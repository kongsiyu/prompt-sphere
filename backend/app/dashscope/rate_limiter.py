"""Rate limiting for DashScope API requests."""

import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict, deque

from .config import DashScopeSettings
from .exceptions import DashScopeRateLimitError


class RateLimiter:
    """Async rate limiter for DashScope API requests."""

    def __init__(self, settings: Optional[DashScopeSettings] = None) -> None:
        """Initialize rate limiter."""
        self.settings = settings or DashScopeSettings()

        # Track requests per minute and per day
        self._minute_requests: deque = deque()
        self._daily_requests: deque = deque()

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Current limits
        self.requests_per_minute = self.settings.requests_per_minute
        self.requests_per_day = self.settings.requests_per_day

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()

            # Clean old requests
            self._clean_old_requests(now)

            # Check minute limit
            if len(self._minute_requests) >= self.requests_per_minute:
                # Calculate wait time until oldest request expires
                oldest_minute_request = self._minute_requests[0]
                wait_time = 60 - (now - oldest_minute_request)
                if wait_time > 0:
                    raise DashScopeRateLimitError(
                        f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                        retry_after=int(wait_time) + 1
                    )

            # Check daily limit
            if len(self._daily_requests) >= self.requests_per_day:
                # Calculate wait time until oldest request expires
                oldest_daily_request = self._daily_requests[0]
                wait_time = 86400 - (now - oldest_daily_request)  # 24 hours
                if wait_time > 0:
                    raise DashScopeRateLimitError(
                        f"Rate limit exceeded: {self.requests_per_day} requests per day",
                        retry_after=int(wait_time) + 1
                    )

            # Record this request
            self._minute_requests.append(now)
            self._daily_requests.append(now)

    def _clean_old_requests(self, now: float) -> None:
        """Remove requests older than the time window."""
        # Remove requests older than 1 minute
        while self._minute_requests and now - self._minute_requests[0] >= 60:
            self._minute_requests.popleft()

        # Remove requests older than 1 day
        while self._daily_requests and now - self._daily_requests[0] >= 86400:
            self._daily_requests.popleft()

    async def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded, instead of raising error."""
        try:
            await self.acquire()
        except DashScopeRateLimitError as e:
            if e.retry_after:
                await asyncio.sleep(e.retry_after)
                await self.acquire()  # Try again after waiting
            else:
                raise

    def get_remaining_requests(self) -> Dict[str, int]:
        """Get number of remaining requests for current time windows."""
        now = time.time()
        self._clean_old_requests(now)

        return {
            "minute": max(0, self.requests_per_minute - len(self._minute_requests)),
            "day": max(0, self.requests_per_day - len(self._daily_requests))
        }

    def reset(self) -> None:
        """Reset all rate limiting counters."""
        self._minute_requests.clear()
        self._daily_requests.clear()


class RequestQueue:
    """Queue for managing concurrent DashScope API requests."""

    def __init__(self, max_concurrent: int = 5) -> None:
        """Initialize request queue."""
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def __aenter__(self):
        """Async context manager entry."""
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.semaphore.release()

    def get_active_requests(self) -> int:
        """Get number of currently active requests."""
        return self.max_concurrent - self.semaphore._value


# Global instances
_rate_limiter: Optional[RateLimiter] = None
_request_queue: Optional[RequestQueue] = None


def get_rate_limiter(settings: Optional[DashScopeSettings] = None) -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings)
    return _rate_limiter


def get_request_queue(max_concurrent: int = 5) -> RequestQueue:
    """Get or create global request queue instance."""
    global _request_queue
    if _request_queue is None:
        _request_queue = RequestQueue(max_concurrent)
    return _request_queue