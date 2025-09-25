"""安全头中间件实现

该模块提供HTTP安全头设置功能，包括：
- CSRF保护
- XSS保护
- 内容类型嗅探保护
- 点击劫持保护
- HSTS安全传输
- 内容安全策略(CSP)
- 引用者策略
"""

import logging
import secrets
import hashlib
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()


class CSRFError(HTTPException):
    """CSRF保护异常"""

    def __init__(self, detail: str = "CSRF token validation failed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    def __init__(
        self,
        app,
        # XSS保护
        enable_xss_protection: bool = True,
        xss_protection_mode: str = "1; mode=block",

        # 内容类型嗅探保护
        enable_content_type_options: bool = True,
        content_type_options: str = "nosniff",

        # 点击劫持保护
        enable_frame_options: bool = True,
        frame_options: str = "DENY",

        # HSTS
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1年
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,

        # CSP内容安全策略
        enable_csp: bool = True,
        csp_policy: Optional[str] = None,
        csp_report_only: bool = False,

        # 引用者策略
        enable_referrer_policy: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",

        # 权限策略
        enable_permissions_policy: bool = True,
        permissions_policy: Optional[str] = None,

        # 其他安全头
        enable_cross_origin_embedder_policy: bool = True,
        cross_origin_embedder_policy: str = "require-corp",

        enable_cross_origin_opener_policy: bool = True,
        cross_origin_opener_policy: str = "same-origin",

        enable_cross_origin_resource_policy: bool = True,
        cross_origin_resource_policy: str = "same-origin",

        # CSRF保护
        enable_csrf_protection: bool = True,
        csrf_cookie_name: str = "csrf_token",
        csrf_header_name: str = "X-CSRF-Token",
        csrf_token_expiry: int = 3600,  # 1小时
        csrf_safe_methods: List[str] = None,
        csrf_exempt_paths: List[str] = None,

        # 自定义头
        custom_headers: Optional[Dict[str, str]] = None,

        # 开发模式设置
        debug_mode: bool = False
    ):
        super().__init__(app)

        # XSS保护设置
        self.enable_xss_protection = enable_xss_protection
        self.xss_protection_mode = xss_protection_mode

        # 内容类型嗅探保护
        self.enable_content_type_options = enable_content_type_options
        self.content_type_options = content_type_options

        # 点击劫持保护
        self.enable_frame_options = enable_frame_options
        self.frame_options = frame_options

        # HSTS设置
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload

        # CSP设置
        self.enable_csp = enable_csp
        self.csp_policy = csp_policy or self._default_csp_policy(debug_mode)
        self.csp_report_only = csp_report_only

        # 引用者策略
        self.enable_referrer_policy = enable_referrer_policy
        self.referrer_policy = referrer_policy

        # 权限策略
        self.enable_permissions_policy = enable_permissions_policy
        self.permissions_policy = permissions_policy or self._default_permissions_policy()

        # 其他CORP策略
        self.enable_cross_origin_embedder_policy = enable_cross_origin_embedder_policy
        self.cross_origin_embedder_policy = cross_origin_embedder_policy

        self.enable_cross_origin_opener_policy = enable_cross_origin_opener_policy
        self.cross_origin_opener_policy = cross_origin_opener_policy

        self.enable_cross_origin_resource_policy = enable_cross_origin_resource_policy
        self.cross_origin_resource_policy = cross_origin_resource_policy

        # CSRF保护设置
        self.enable_csrf_protection = enable_csrf_protection
        self.csrf_cookie_name = csrf_cookie_name
        self.csrf_header_name = csrf_header_name
        self.csrf_token_expiry = csrf_token_expiry
        self.csrf_safe_methods = csrf_safe_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
        self.csrf_exempt_paths = set(csrf_exempt_paths or [
            "/api/health",
            "/api/v1/auth/callback",  # OAuth回调通常不需要CSRF保护
            "/docs",
            "/redoc",
            "/openapi.json"
        ])

        # 自定义头
        self.custom_headers = custom_headers or {}

        # 开发模式
        self.debug_mode = debug_mode

    def _default_csp_policy(self, debug_mode: bool) -> str:
        """生成默认的CSP策略"""
        if debug_mode:
            # 开发模式下的宽松策略
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:;"
            )
        else:
            # 生产模式下的严格策略
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

    def _default_permissions_policy(self) -> str:
        """生成默认的权限策略"""
        return (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主处理函数"""
        try:
            # CSRF保护检查
            if self.enable_csrf_protection:
                await self._check_csrf_protection(request)

            # 处理请求
            response = await call_next(request)

            # 添加安全头
            self._add_security_headers(response, request)

            return response

        except CSRFError:
            raise
        except Exception as e:
            logger.error(f"Security headers middleware error: {e}")
            # 即使中间件出错，也继续处理请求
            response = await call_next(request)
            self._add_security_headers(response, request)
            return response

    async def _check_csrf_protection(self, request: Request) -> None:
        """检查CSRF保护"""
        # 跳过安全方法
        if request.method in self.csrf_safe_methods:
            return

        # 跳过免除路径
        if request.url.path in self.csrf_exempt_paths:
            return

        # 跳过某些内容类型（如API调用）
        content_type = request.headers.get("content-type", "").lower()
        if content_type.startswith("application/json"):
            # JSON请求通常通过其他方式保护（如JWT）
            return

        # 获取CSRF令牌
        csrf_token = None

        # 首先从头部获取
        csrf_token = request.headers.get(self.csrf_header_name)

        # 如果头部没有，从表单数据获取
        if not csrf_token and content_type.startswith("application/x-www-form-urlencoded"):
            form_data = await request.form()
            csrf_token = form_data.get("csrf_token")

        # 如果还没有，从cookie获取并验证
        if not csrf_token:
            csrf_token = request.cookies.get(self.csrf_cookie_name)

        if not csrf_token:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            raise CSRFError("缺少CSRF令牌")

        # 验证CSRF令牌
        if not await self._verify_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token for {request.method} {request.url.path}")
            raise CSRFError("无效的CSRF令牌")

    async def _verify_csrf_token(self, token: str) -> bool:
        """验证CSRF令牌"""
        try:
            redis_client = await get_redis_client()

            # 检查令牌是否存在且有效
            token_data = await redis_client.get(f"csrf_token:{token}")
            return token_data is not None

        except Exception as e:
            logger.error(f"CSRF token verification failed: {e}")
            return False

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """添加安全头到响应"""
        # X-XSS-Protection
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = self.xss_protection_mode

        # X-Content-Type-Options
        if self.enable_content_type_options:
            response.headers["X-Content-Type-Options"] = self.content_type_options

        # X-Frame-Options
        if self.enable_frame_options:
            response.headers["X-Frame-Options"] = self.frame_options

        # Strict-Transport-Security (仅在HTTPS下)
        if self.enable_hsts and request.url.scheme == "https":
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content-Security-Policy
        if self.enable_csp:
            csp_header = "Content-Security-Policy-Report-Only" if self.csp_report_only else "Content-Security-Policy"
            response.headers[csp_header] = self.csp_policy

        # Referrer-Policy
        if self.enable_referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy
        if self.enable_permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy

        # Cross-Origin-Embedder-Policy
        if self.enable_cross_origin_embedder_policy:
            response.headers["Cross-Origin-Embedder-Policy"] = self.cross_origin_embedder_policy

        # Cross-Origin-Opener-Policy
        if self.enable_cross_origin_opener_policy:
            response.headers["Cross-Origin-Opener-Policy"] = self.cross_origin_opener_policy

        # Cross-Origin-Resource-Policy
        if self.enable_cross_origin_resource_policy:
            response.headers["Cross-Origin-Resource-Policy"] = self.cross_origin_resource_policy

        # 自定义头
        for header_name, header_value in self.custom_headers.items():
            response.headers[header_name] = header_value

        # 添加服务器信息隐藏
        if "Server" in response.headers:
            del response.headers["Server"]

        # 添加安全相关的meta头
        response.headers["X-Powered-By"] = "AI-Prompt-Generator"


class CSRFProtection:
    """CSRF保护工具类"""

    def __init__(self, token_expiry: int = 3600):
        self.token_expiry = token_expiry

    async def generate_csrf_token(self, session_id: Optional[str] = None) -> str:
        """生成CSRF令牌"""
        try:
            # 生成随机令牌
            token = secrets.token_urlsafe(32)

            # 如果提供了会话ID，将其包含在令牌中
            if session_id:
                token_data = f"{token}:{session_id}:{datetime.utcnow().isoformat()}"
                token = hashlib.sha256(token_data.encode()).hexdigest()

            # 存储到Redis
            redis_client = await get_redis_client()
            await redis_client.setex(
                f"csrf_token:{token}",
                self.token_expiry,
                datetime.utcnow().isoformat()
            )

            logger.debug(f"Generated CSRF token: {token[:8]}...")
            return token

        except Exception as e:
            logger.error(f"Failed to generate CSRF token: {e}")
            raise

    async def validate_csrf_token(self, token: str) -> bool:
        """验证CSRF令牌"""
        try:
            redis_client = await get_redis_client()

            # 检查令牌是否存在
            token_data = await redis_client.get(f"csrf_token:{token}")
            if not token_data:
                return False

            logger.debug(f"Validated CSRF token: {token[:8]}...")
            return True

        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False

    async def revoke_csrf_token(self, token: str) -> bool:
        """撤销CSRF令牌"""
        try:
            redis_client = await get_redis_client()
            result = await redis_client.delete(f"csrf_token:{token}")

            if result:
                logger.debug(f"Revoked CSRF token: {token[:8]}...")

            return result > 0

        except Exception as e:
            logger.error(f"Failed to revoke CSRF token: {e}")
            return False


# 全局CSRF保护实例
csrf_protection = CSRFProtection()


# 工具函数
def create_security_headers_middleware(
    debug_mode: bool = False,
    strict_csp: bool = True,
    enable_csrf: bool = True
) -> SecurityHeadersMiddleware:
    """创建适合不同环境的安全头中间件"""

    if debug_mode:
        # 开发环境：宽松的安全策略
        return SecurityHeadersMiddleware(
            app=None,  # 将在添加到app时设置
            enable_csrf_protection=False,  # 开发时可能不需要
            csp_report_only=True,  # 仅报告模式
            frame_options="SAMEORIGIN",  # 允许同源嵌套
            debug_mode=True
        )
    else:
        # 生产环境：严格的安全策略
        csp_policy = None
        if strict_csp:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        return SecurityHeadersMiddleware(
            app=None,
            enable_csrf_protection=enable_csrf,
            csp_policy=csp_policy,
            csp_report_only=False,
            frame_options="DENY",
            enable_hsts=True,
            hsts_preload=True,
            debug_mode=False
        )


# FastAPI依赖项：获取CSRF令牌
async def get_csrf_token(request: Request) -> str:
    """FastAPI依赖项：生成并返回CSRF令牌"""
    session_id = getattr(request.state, 'session_id', None)
    return await csrf_protection.generate_csrf_token(session_id)


# FastAPI依赖项：验证CSRF令牌
async def validate_csrf_token(request: Request) -> bool:
    """FastAPI依赖项：验证CSRF令牌"""
    csrf_token = request.headers.get("X-CSRF-Token")
    if not csrf_token:
        raise CSRFError("缺少CSRF令牌")

    is_valid = await csrf_protection.validate_csrf_token(csrf_token)
    if not is_valid:
        raise CSRFError("无效的CSRF令牌")

    return True