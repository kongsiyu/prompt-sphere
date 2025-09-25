"""认证模块初始化

此模块提供OAuth 2.0和DingTalk认证功能的统一入口，包括：
- OAuth客户端类导出
- 认证异常类导出
- 工厂函数和便捷方法
"""

from .dingtalk import DingTalkOAuthClient, DingTalkUserInfo
from .exceptions import (
    AccessDeniedError,
    AuthenticationError,
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
from .oauth import OAuthClient, TokenResponse, UserInfo

__all__ = [
    # OAuth客户端类
    "OAuthClient",
    "DingTalkOAuthClient",
    # 数据模型
    "TokenResponse",
    "UserInfo",
    "DingTalkUserInfo",
    # 异常类
    "AuthenticationError",
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
]


def create_dingtalk_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    corp_id: str = None,
    **kwargs
) -> DingTalkOAuthClient:
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
    return DingTalkOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        corp_id=corp_id,
        **kwargs
    )