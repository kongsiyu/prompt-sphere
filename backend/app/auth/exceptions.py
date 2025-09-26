"""OAuth 2.0和DingTalk认证相关异常类定义

此模块定义了OAuth 2.0认证流程中可能出现的各种异常类型，
包括授权失败、令牌无效、用户信息获取失败等场景。
"""

from typing import Optional


class AuthenticationError(Exception):
    """认证基础异常类"""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class OAuthError(AuthenticationError):
    """OAuth 2.0相关异常"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        error_description: Optional[str] = None,
        error_uri: Optional[str] = None,
    ):
        super().__init__(message, error_code)
        self.error_description = error_description
        self.error_uri = error_uri


class InvalidStateError(OAuthError):
    """OAuth状态参数验证失败异常"""

    def __init__(self, message: str = "无效的OAuth状态参数"):
        super().__init__(message, "invalid_state")


class InvalidGrantError(OAuthError):
    """授权码验证失败异常"""

    def __init__(self, message: str = "无效的授权码"):
        super().__init__(message, "invalid_grant")


class AccessDeniedError(OAuthError):
    """用户拒绝授权异常"""

    def __init__(self, message: str = "用户拒绝授权"):
        super().__init__(message, "access_denied")


class TokenExpiredError(AuthenticationError):
    """令牌过期异常"""

    def __init__(self, message: str = "访问令牌已过期"):
        super().__init__(message, "token_expired")


class TokenInvalidError(AuthenticationError):
    """令牌无效异常"""

    def __init__(self, message: str = "无效的访问令牌"):
        super().__init__(message, "invalid_token")


class UserInfoError(AuthenticationError):
    """用户信息获取失败异常"""

    def __init__(self, message: str = "获取用户信息失败"):
        super().__init__(message, "user_info_error")


class DingTalkAPIError(AuthenticationError):
    """DingTalk API调用异常"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        sub_code: Optional[str] = None,
        sub_msg: Optional[str] = None,
    ):
        super().__init__(message, error_code)
        self.sub_code = sub_code
        self.sub_msg = sub_msg


class ConfigurationError(AuthenticationError):
    """OAuth配置错误异常"""

    def __init__(self, message: str = "OAuth配置不正确"):
        super().__init__(message, "configuration_error")


class HTTPError(AuthenticationError):
    """HTTP请求异常"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message, "http_error")
        self.status_code = status_code