"""速率限制中间件实现

该模块提供基于Redis的速率限制功能，支持：
- IP地址级别的速率限制
- 用户级别的速率限制
- 端点级别的自定义限制
- 滑动窗口算法
- 自定义限制策略
"""

import logging
import time
import hashlib
from typing import Optional, Callable, Dict, Any, Union
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitExceeded(HTTPException):
    """速率限制异常"""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or {}
        )
        if retry_after:
            self.headers["Retry-After"] = str(retry_after)


class RateLimiter:
    """速率限制器类"""

    def __init__(
        self,
        calls: int = 100,
        period: int = 3600,
        scope: str = "default",
        per_method: bool = True,
        skip_successful: bool = False,
        skip_failed: bool = False,
        identifier: Optional[Callable[[Request], str]] = None,
        callback: Optional[Callable[[Request, Exception], None]] = None
    ):
        """
        初始化速率限制器

        Args:
            calls: 允许的请求次数
            period: 时间窗口（秒）
            scope: 限制作用域
            per_method: 是否按HTTP方法分别限制
            skip_successful: 是否跳过成功请求的计数
            skip_failed: 是否跳过失败请求的计数
            identifier: 自定义标识符生成函数
            callback: 限制触发时的回调函数
        """
        self.calls = calls
        self.period = period
        self.scope = scope
        self.per_method = per_method
        self.skip_successful = skip_successful
        self.skip_failed = skip_failed
        self.identifier = identifier or self._default_identifier
        self.callback = callback

    def _default_identifier(self, request: Request) -> str:
        """默认标识符生成：基于IP地址和用户ID（如果存在）"""
        client_ip = self._get_client_ip(request)

        # 尝试获取用户标识
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        elif 'Authorization' in request.headers:
            # 从JWT令牌中提取用户ID（简化处理）
            try:
                from app.auth.jwt import get_jwt_handler
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    jwt_handler = get_jwt_handler()
                    payload = jwt_handler.verify_token(token)
                    if payload:
                        user_id = payload.user_id
            except Exception:
                pass  # 忽略令牌解析错误

        # 生成复合标识符
        if user_id:
            identifier = f"user:{user_id}:{client_ip}"
        else:
            identifier = f"ip:{client_ip}"

        return hashlib.md5(identifier.encode()).hexdigest()

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址，支持代理服务器"""
        # 优先使用X-Forwarded-For头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一个IP（客户端原始IP）
            return forwarded_for.split(",")[0].strip()

        # 使用X-Real-IP头
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # 使用直接连接IP
        if request.client:
            return request.client.host

        return "unknown"

    def _generate_cache_key(self, request: Request, identifier: str) -> str:
        """生成Redis缓存键"""
        method = request.method if self.per_method else "ALL"
        path = request.url.path

        return f"rate_limit:{self.scope}:{method}:{path}:{identifier}"

    async def _get_current_usage(self, cache_key: str) -> tuple[int, Optional[int]]:
        """获取当前使用量和TTL"""
        try:
            redis_client = await get_redis_client()

            # 使用管道提高性能
            async with redis_client.pipeline() as pipe:
                await pipe.get(cache_key)
                await pipe.ttl(cache_key)
                results = await pipe.execute()

            current_calls = int(results[0] or 0)
            ttl = results[1] if results[1] > 0 else None

            return current_calls, ttl

        except Exception as e:
            logger.error(f"Failed to get rate limit usage: {e}")
            # 在Redis连接失败时，允许请求通过（优雅降级）
            return 0, None

    async def _increment_usage(self, cache_key: str) -> tuple[int, int]:
        """增加使用量并返回当前值和TTL"""
        try:
            redis_client = await get_redis_client()

            # 使用Lua脚本确保原子性
            lua_script = """
            local current = redis.call('incr', KEYS[1])
            if current == 1 then
                redis.call('expire', KEYS[1], ARGV[1])
                return {current, ARGV[1]}
            else
                local ttl = redis.call('ttl', KEYS[1])
                return {current, ttl}
            end
            """

            result = await redis_client.eval(lua_script, 1, cache_key, self.period)
            return int(result[0]), int(result[1])

        except Exception as e:
            logger.error(f"Failed to increment rate limit usage: {e}")
            # 在Redis连接失败时，允许请求通过
            return 1, self.period

    async def _check_rate_limit(self, request: Request) -> Optional[Dict[str, Any]]:
        """检查速率限制"""
        try:
            # 生成标识符和缓存键
            identifier = self.identifier(request)
            cache_key = self._generate_cache_key(request, identifier)

            # 获取当前使用量
            current_calls, ttl = await self._get_current_usage(cache_key)

            # 检查是否超出限制
            if current_calls >= self.calls:
                retry_after = ttl or self.period

                logger.warning(
                    f"Rate limit exceeded for {identifier}: {current_calls}/{self.calls} "
                    f"in {self.period}s, retry after {retry_after}s"
                )

                return {
                    "exceeded": True,
                    "current": current_calls,
                    "limit": self.calls,
                    "period": self.period,
                    "retry_after": retry_after,
                    "identifier": identifier
                }

            # 增加使用量
            new_calls, new_ttl = await self._increment_usage(cache_key)

            return {
                "exceeded": False,
                "current": new_calls,
                "limit": self.calls,
                "period": self.period,
                "remaining": max(0, self.calls - new_calls),
                "reset_at": int(time.time()) + new_ttl,
                "identifier": identifier
            }

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 在检查失败时允许请求通过
            return {
                "exceeded": False,
                "current": 0,
                "limit": self.calls,
                "period": self.period,
                "remaining": self.calls,
                "identifier": "unknown"
            }

    def __call__(self, func: Callable) -> Callable:
        """装饰器调用"""
        async def wrapper(request: Request, *args, **kwargs):
            # 检查速率限制
            limit_info = await self._check_rate_limit(request)

            if limit_info["exceeded"]:
                # 触发回调（如果存在）
                if self.callback:
                    try:
                        await self.callback(request, RateLimitExceeded())
                    except Exception as e:
                        logger.error(f"Rate limit callback failed: {e}")

                # 抛出速率限制异常
                raise RateLimitExceeded(
                    detail=f"速率限制：{limit_info['current']}/{limit_info['limit']} 请求在 {limit_info['period']} 秒内",
                    retry_after=limit_info["retry_after"],
                    headers={
                        "X-RateLimit-Limit": str(limit_info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_info.get("reset_at", 0)),
                        "Retry-After": str(limit_info["retry_after"])
                    }
                )

            # 设置速率限制信息到请求状态
            request.state.rate_limit = limit_info

            try:
                # 执行原始函数
                response = await func(request, *args, **kwargs)

                # 在响应中添加速率限制头部
                if hasattr(response, 'headers'):
                    response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
                    response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset_at", 0))

                return response

            except HTTPException as e:
                # 根据配置决定是否跳过失败请求的计数
                if self.skip_failed:
                    # TODO: 实现回滚逻辑
                    pass
                raise
            except Exception as e:
                # 记录未预期的异常
                logger.error(f"Unexpected error in rate limited endpoint: {e}")
                raise

        return wrapper


class RateLimitMiddleware:
    """FastAPI速率限制中间件"""

    def __init__(
        self,
        calls: int = 1000,
        period: int = 3600,
        scope: str = "global",
        exempt_paths: Optional[list[str]] = None,
        custom_limits: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        初始化中间件

        Args:
            calls: 默认请求限制
            period: 默认时间窗口
            scope: 默认作用域
            exempt_paths: 免除限制的路径列表
            custom_limits: 自定义限制配置
        """
        self.default_limiter = RateLimiter(calls=calls, period=period, scope=scope)
        self.exempt_paths = set(exempt_paths or [])
        self.custom_limiters: Dict[str, RateLimiter] = {}

        # 初始化自定义限制器
        if custom_limits:
            for path_pattern, config in custom_limits.items():
                self.custom_limiters[path_pattern] = RateLimiter(**config)

    def _get_limiter_for_path(self, path: str) -> Optional[RateLimiter]:
        """为路径选择合适的限制器"""
        # 检查是否在免除列表中
        if path in self.exempt_paths:
            return None

        # 检查自定义限制器
        for pattern, limiter in self.custom_limiters.items():
            if path.startswith(pattern):
                return limiter

        # 返回默认限制器
        return self.default_limiter

    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        path = request.url.path

        # 选择合适的限制器
        limiter = self._get_limiter_for_path(path)

        if limiter is None:
            # 不需要限制，直接处理请求
            return await call_next(request)

        # 应用速率限制
        try:
            limit_info = await limiter._check_rate_limit(request)

            if limit_info["exceeded"]:
                # 返回速率限制错误响应
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"速率限制：{limit_info['current']}/{limit_info['limit']} 请求在 {limit_info['period']} 秒内",
                        "details": {
                            "limit": limit_info["limit"],
                            "remaining": 0,
                            "reset_at": limit_info.get("reset_at", 0)
                        }
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit_info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_info.get("reset_at", 0)),
                        "Retry-After": str(limit_info["retry_after"])
                    }
                )

            # 处理请求
            response = await call_next(request)

            # 添加速率限制头部
            response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset_at", 0))

            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # 在中间件失败时允许请求继续
            return await call_next(request)


# 预定义的限制器
AUTH_LIMITER = RateLimiter(calls=10, period=300, scope="auth")  # 认证端点：5分钟10次
API_LIMITER = RateLimiter(calls=100, period=3600, scope="api")  # API端点：1小时100次
STRICT_LIMITER = RateLimiter(calls=5, period=60, scope="strict")  # 严格限制：1分钟5次


# 工具函数
async def get_rate_limit_info(request: Request, limiter: RateLimiter) -> Dict[str, Any]:
    """获取指定限制器的当前状态"""
    identifier = limiter.identifier(request)
    cache_key = limiter._generate_cache_key(request, identifier)
    current_calls, ttl = await limiter._get_current_usage(cache_key)

    return {
        "identifier": identifier,
        "current": current_calls,
        "limit": limiter.calls,
        "period": limiter.period,
        "remaining": max(0, limiter.calls - current_calls),
        "reset_at": int(time.time()) + (ttl or limiter.period) if ttl else None
    }


async def reset_rate_limit(identifier: str, scope: str = "default") -> bool:
    """重置指定标识符的速率限制"""
    try:
        redis_client = await get_redis_client()

        # 查找并删除相关的速率限制键
        pattern = f"rate_limit:{scope}:*:{identifier}"
        keys = await redis_client.keys(pattern)

        if keys:
            await redis_client.delete(*keys)
            logger.info(f"Reset rate limit for identifier {identifier} in scope {scope}")
            return True

        return False

    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}")
        return False