"""认证中间件和依赖注入"""
import logging
from typing import Optional, List, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.tokens import get_token_manager
from app.auth.jwt import JWTPayload
from app.models.tokens import UserSession, TokenScope

logger = logging.getLogger(__name__)

# HTTP Bearer安全方案
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> Optional[JWTPayload]:
    """获取当前用户的JWT负载（可选）"""
    if not credentials:
        return None

    try:
        token_manager = await get_token_manager()
        payload = await token_manager.verify_token(credentials.credentials)

        if payload and request:
            # 记录访问日志（可选）
            logger.debug(f"User {payload.user_id} accessed {request.url.path}")

        return payload

    except Exception as e:
        logger.error(f"Failed to verify token: {e}")
        return None


async def get_current_user_required(
    payload: Optional[JWTPayload] = Depends(get_current_user_payload)
) -> JWTPayload:
    """获取当前用户的JWT负载（必需）"""
    if not payload:
        raise AuthenticationError("访问此资源需要有效的访问令牌")

    if payload.scope != "access":
        raise AuthenticationError("令牌类型无效")

    return payload


async def get_current_user_session(
    payload: JWTPayload = Depends(get_current_user_required),
    request: Request = None
) -> UserSession:
    """获取当前用户会话信息"""
    try:
        # 获取客户端信息
        client_info = {}
        if request:
            client_info = {
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "")
            }

        session = UserSession(
            session_id=payload.jti,
            user_id=payload.user_id,
            username=payload.username,
            roles=payload.roles,
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )

        return session

    except Exception as e:
        logger.error(f"Failed to create user session: {e}")
        raise AuthenticationError("无法创建用户会话")


def require_roles(required_roles: List[str]):
    """要求特定角色的依赖注入装饰器"""
    async def check_roles(
        payload: JWTPayload = Depends(get_current_user_required)
    ) -> JWTPayload:
        """检查用户是否具有所需角色"""
        user_roles = set(payload.roles or [])
        required_roles_set = set(required_roles)

        # 管理员角色可以访问所有资源
        if "admin" in user_roles:
            return payload

        # 检查是否有任何所需角色
        if not user_roles.intersection(required_roles_set):
            raise AuthorizationError(
                f"访问此资源需要以下角色之一: {', '.join(required_roles)}"
            )

        return payload

    return check_roles


def require_any_role(roles: List[str]):
    """要求任意一个角色"""
    return require_roles(roles)


def require_all_roles(required_roles: List[str]):
    """要求所有指定的角色"""
    async def check_all_roles(
        payload: JWTPayload = Depends(get_current_user_required)
    ) -> JWTPayload:
        """检查用户是否具有所有所需角色"""
        user_roles = set(payload.roles or [])
        required_roles_set = set(required_roles)

        # 管理员角色可以访问所有资源
        if "admin" in user_roles:
            return payload

        # 检查是否拥有所有所需角色
        if not required_roles_set.issubset(user_roles):
            missing_roles = required_roles_set - user_roles
            raise AuthorizationError(
                f"访问此资源需要以下所有角色: {', '.join(required_roles)}，"
                f"缺少: {', '.join(missing_roles)}"
            )

        return payload

    return check_all_roles


def require_admin():
    """要求管理员角色"""
    return require_roles(["admin"])


def require_user():
    """要求普通用户角色"""
    return require_roles(["user", "admin"])


def require_api_access():
    """要求API访问权限"""
    return require_roles(["api_user", "admin"])


class PermissionChecker:
    """权限检查器"""

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        payload: JWTPayload = Depends(get_current_user_required)
    ) -> JWTPayload:
        """检查用户权限"""
        # 这里可以根据用户角色查询数据库获取具体权限
        # 目前简化为基于角色的权限检查

        user_roles = payload.roles or []

        # 管理员拥有所有权限
        if "admin" in user_roles:
            return payload

        # 根据角色映射权限（简化实现）
        role_permissions = {
            "user": ["read", "write"],
            "editor": ["read", "write", "edit"],
            "moderator": ["read", "write", "edit", "moderate"],
            "api_user": ["api:read", "api:write"]
        }

        user_permissions = set()
        for role in user_roles:
            user_permissions.update(role_permissions.get(role, []))

        # 检查权限
        required_permissions_set = set(self.required_permissions)
        if not user_permissions.intersection(required_permissions_set):
            raise AuthorizationError(
                f"访问此资源需要以下权限之一: {', '.join(self.required_permissions)}"
            )

        return payload


def require_permissions(permissions: List[str]):
    """要求特定权限"""
    return PermissionChecker(permissions)


async def optional_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[JWTPayload]:
    """可选的身份验证 - 如果提供了令牌则验证，否则返回None"""
    if not credentials:
        return None

    try:
        token_manager = await get_token_manager()
        return await token_manager.verify_token(credentials.credentials)
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


class RateLimitChecker:
    """速率限制检查器"""

    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 3600,  # 1小时
        per_user: bool = True
    ):
        self.max_requests = max_requests
        self.time_window = time_window
        self.per_user = per_user

    async def __call__(
        self,
        request: Request,
        payload: Optional[JWTPayload] = Depends(optional_authentication)
    ) -> None:
        """检查速率限制"""
        try:
            # 确定限制键
            if self.per_user and payload:
                limit_key = f"rate_limit:user:{payload.user_id}"
            else:
                client_ip = request.client.host if request.client else "unknown"
                limit_key = f"rate_limit:ip:{client_ip}"

            # 使用令牌管理器的Redis连接检查速率限制
            token_manager = await get_token_manager()
            redis = await token_manager._get_redis()

            # 获取当前计数
            current_count = await redis.get(limit_key)
            if current_count is None:
                # 首次访问，设置计数器
                await redis.setex(limit_key, self.time_window, 1)
                return

            current_count = int(current_count)
            if current_count >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"速率限制：每{self.time_window}秒最多{self.max_requests}个请求"
                )

            # 增加计数器
            await redis.incr(limit_key)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 速率限制检查失败时不阻止请求


def rate_limit(max_requests: int = 100, time_window: int = 3600, per_user: bool = True):
    """速率限制装饰器"""
    return RateLimitChecker(max_requests, time_window, per_user)


# 预定义的常用依赖项
CurrentUser = Depends(get_current_user_required)
CurrentUserOptional = Depends(get_current_user_payload)
CurrentUserSession = Depends(get_current_user_session)
RequireAdmin = Depends(require_admin())
RequireUser = Depends(require_user())
RequireApiAccess = Depends(require_api_access())

# 速率限制预设
AuthRateLimit = Depends(rate_limit(max_requests=10, time_window=900, per_user=False))  # 认证端点
ApiRateLimit = Depends(rate_limit(max_requests=1000, time_window=3600, per_user=True))  # API端点
AdminRateLimit = Depends(rate_limit(max_requests=500, time_window=3600, per_user=True))  # 管理端点