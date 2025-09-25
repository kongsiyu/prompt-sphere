"""认证模块初始化

此模块提供完整的身份验证和授权功能，包括：
- JWT令牌管理
- OAuth 2.0和DingTalk认证
- 认证中间件和依赖注入
- 安全配置和密钥管理
"""

# JWT和令牌管理
from .jwt import JWTHandler, JWTPayload, get_jwt_handler
from .tokens import TokenManager, get_token_manager

# 认证中间件和依赖注入
from .middleware import (
    get_current_user_payload,
    get_current_user_required,
    get_current_user_session,
    require_roles,
    require_any_role,
    require_all_roles,
    require_admin,
    require_user,
    require_api_access,
    require_permissions,
    optional_authentication,
    rate_limit,
    AuthenticationError,
    AuthorizationError,
    # 预定义依赖项
    CurrentUser,
    CurrentUserOptional,
    CurrentUserSession,
    RequireAdmin,
    RequireUser,
    RequireApiAccess,
    AuthRateLimit,
    ApiRateLimit,
    AdminRateLimit,
)

# OAuth功能（如果存在）
try:
    from .dingtalk import DingTalkOAuthClient, DingTalkUserInfo
    from .oauth import OAuthClient, TokenResponse, UserInfo
    from .exceptions import (
        AccessDeniedError,
        ConfigurationError,
        DingTalkAPIError,
        HTTPError,
        InvalidGrantError,
        InvalidStateError,
        OAuthError,
        TokenExpiredError,
        TokenInvalidError,
        UserInfoError,
    )
    _OAUTH_AVAILABLE = True
except ImportError:
    _OAUTH_AVAILABLE = False

__all__ = [
    # JWT和令牌管理
    "JWTHandler",
    "JWTPayload",
    "get_jwt_handler",
    "TokenManager",
    "get_token_manager",

    # 认证中间件
    "get_current_user_payload",
    "get_current_user_required",
    "get_current_user_session",
    "require_roles",
    "require_any_role",
    "require_all_roles",
    "require_admin",
    "require_user",
    "require_api_access",
    "require_permissions",
    "optional_authentication",
    "rate_limit",
    "AuthenticationError",
    "AuthorizationError",

    # 预定义依赖项
    "CurrentUser",
    "CurrentUserOptional",
    "CurrentUserSession",
    "RequireAdmin",
    "RequireUser",
    "RequireApiAccess",
    "AuthRateLimit",
    "ApiRateLimit",
    "AdminRateLimit",
]

# 如果OAuth功能可用，添加到导出列表
if _OAUTH_AVAILABLE:
    __all__.extend([
        # OAuth客户端类
        "OAuthClient",
        "DingTalkOAuthClient",
        # 数据模型
        "TokenResponse",
        "UserInfo",
        "DingTalkUserInfo",
        # 异常类
        "OAuthError",
        "InvalidStateError",
        "InvalidGrantError",
        "AccessDeniedError",
        "TokenExpiredError",
        "TokenInvalidError",
        "UserInfoError",
        "DingTalkAPIError",
        "ConfigurationError",
        "HTTPError",
    ])


def create_dingtalk_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    corp_id: str = None,
    **kwargs
):
    """创建DingTalk OAuth客户端的工厂函数

    Args:
        client_id: DingTalk应用的AppKey
        client_secret: DingTalk应用的AppSecret
        redirect_uri: 授权回调地址
        corp_id: 企业ID（可选）
        **kwargs: 其他参数传递给DingTalkOAuthClient

    Returns:
        配置好的DingTalkOAuthClient实例
    """
    if not _OAUTH_AVAILABLE:
        raise ImportError("OAuth功能不可用，请检查相关依赖项")

    return DingTalkOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        corp_id=corp_id,
        **kwargs
    )