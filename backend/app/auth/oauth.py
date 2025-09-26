"""OAuth 2.0客户端基础实现

此模块提供了OAuth 2.0授权码流程的基础实现，包括：
- 生成授权URL
- 处理授权码回调
- 令牌交换和刷新
- 状态验证防CSRF攻击
- HTTP客户端封装
"""

import secrets
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import httpx
from pydantic import BaseModel

from .exceptions import (
    AccessDeniedError,
    ConfigurationError,
    HTTPError,
    InvalidGrantError,
    InvalidStateError,
    OAuthError,
    TokenExpiredError,
    TokenInvalidError,
    UserInfoError,
)


class TokenResponse(BaseModel):
    """OAuth令牌响应模型"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息基础模型"""

    id: str
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class OAuthClient(ABC):
    """OAuth 2.0客户端基础抽象类"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化OAuth客户端

        Args:
            client_id: OAuth应用客户端ID
            client_secret: OAuth应用客户端密钥
            redirect_uri: 授权回调地址
            scope: 请求的权限范围
            timeout: HTTP请求超时时间（秒）
        """
        if not client_id:
            raise ConfigurationError("client_id不能为空")
        if not client_secret:
            raise ConfigurationError("client_secret不能为空")
        if not redirect_uri:
            raise ConfigurationError("redirect_uri不能为空")

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.timeout = timeout

        # HTTP客户端配置
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "AI-Prompt-Generator/1.0"},
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def close(self):
        """关闭HTTP客户端连接"""
        if self._client:
            await self._client.aclose()

    @property
    @abstractmethod
    def authorize_url(self) -> str:
        """OAuth授权端点URL"""
        pass

    @property
    @abstractmethod
    def token_url(self) -> str:
        """OAuth令牌端点URL"""
        pass

    @property
    @abstractmethod
    def user_info_url(self) -> str:
        """用户信息端点URL"""
        pass

    def generate_state(self) -> str:
        """生成随机状态参数防止CSRF攻击

        Returns:
            32字符的随机字符串
        """
        return secrets.token_urlsafe(32)

    def build_authorize_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """构建OAuth授权URL

        Args:
            state: 可选的状态参数，如果不提供会自动生成

        Returns:
            包含授权URL和状态参数的元组
        """
        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
        }

        if self.scope:
            params["scope"] = self.scope

        # 允许子类添加额外参数
        params.update(self._get_additional_auth_params())

        query_string = urllib.parse.urlencode(params)
        full_url = f"{self.authorize_url}?{query_string}"

        return full_url, state

    def _get_additional_auth_params(self) -> Dict[str, str]:
        """子类可重写此方法添加额外的授权参数"""
        return {}

    async def exchange_code_for_token(
        self, code: str, state: str, expected_state: str
    ) -> TokenResponse:
        """使用授权码交换访问令牌

        Args:
            code: OAuth授权码
            state: 回调中的状态参数
            expected_state: 期望的状态参数

        Returns:
            令牌响应对象

        Raises:
            InvalidStateError: 状态参数不匹配
            InvalidGrantError: 授权码无效
            OAuthError: 其他OAuth错误
        """
        # 验证状态参数
        if state != expected_state:
            raise InvalidStateError(f"状态参数不匹配: 期望 {expected_state}, 实际 {state}")

        # 构建令牌交换请求
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        # 允许子类添加额外参数
        data.update(self._get_additional_token_params())

        try:
            response = await self._client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get("error", "invalid_request")
                error_desc = error_data.get("error_description", "令牌交换失败")

                if error_code == "invalid_grant":
                    raise InvalidGrantError(error_desc)
                elif error_code == "access_denied":
                    raise AccessDeniedError(error_desc)
                else:
                    raise OAuthError(error_desc, error_code)

            if not response.is_success:
                raise HTTPError(
                    f"令牌交换请求失败: {response.status_code}", response.status_code
                )

            token_data = response.json()
            return self._parse_token_response(token_data)

        except httpx.TimeoutException:
            raise HTTPError("令牌交换请求超时")
        except httpx.RequestError as e:
            raise HTTPError(f"令牌交换请求失败: {str(e)}")

    def _get_additional_token_params(self) -> Dict[str, str]:
        """子类可重写此方法添加额外的令牌交换参数"""
        return {}

    @abstractmethod
    def _parse_token_response(self, token_data: Dict[str, Any]) -> TokenResponse:
        """解析令牌响应数据，子类必须实现"""
        pass

    async def get_user_info(self, access_token: str) -> UserInfo:
        """使用访问令牌获取用户信息

        Args:
            access_token: OAuth访问令牌

        Returns:
            用户信息对象

        Raises:
            TokenInvalidError: 令牌无效
            TokenExpiredError: 令牌过期
            UserInfoError: 获取用户信息失败
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = await self._client.get(self.user_info_url, headers=headers)

            if response.status_code == 401:
                raise TokenInvalidError("访问令牌无效或已过期")
            elif response.status_code == 403:
                raise TokenExpiredError("访问令牌已过期")
            elif not response.is_success:
                raise HTTPError(
                    f"获取用户信息失败: {response.status_code}", response.status_code
                )

            user_data = response.json()
            return self._parse_user_info(user_data)

        except httpx.TimeoutException:
            raise UserInfoError("获取用户信息请求超时")
        except httpx.RequestError as e:
            raise UserInfoError(f"获取用户信息请求失败: {str(e)}")

    @abstractmethod
    def _parse_user_info(self, user_data: Dict[str, Any]) -> UserInfo:
        """解析用户信息响应数据，子类必须实现"""
        pass

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """使用刷新令牌获取新的访问令牌

        Args:
            refresh_token: OAuth刷新令牌

        Returns:
            新的令牌响应对象

        Raises:
            TokenInvalidError: 刷新令牌无效
            OAuthError: 其他OAuth错误
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:
            response = await self._client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get("error", "invalid_request")
                error_desc = error_data.get("error_description", "刷新令牌失败")

                if error_code == "invalid_grant":
                    raise TokenInvalidError("无效的刷新令牌")
                else:
                    raise OAuthError(error_desc, error_code)

            if not response.is_success:
                raise HTTPError(
                    f"刷新令牌请求失败: {response.status_code}", response.status_code
                )

            token_data = response.json()
            return self._parse_token_response(token_data)

        except httpx.TimeoutException:
            raise HTTPError("刷新令牌请求超时")
        except httpx.RequestError as e:
            raise HTTPError(f"刷新令牌请求失败: {str(e)}")

    def handle_error_callback(self, error: str, error_description: Optional[str] = None):
        """处理OAuth错误回调

        Args:
            error: 错误代码
            error_description: 错误描述

        Raises:
            相应的OAuth异常
        """
        if error == "access_denied":
            raise AccessDeniedError(error_description or "用户拒绝授权")
        elif error == "invalid_request":
            raise OAuthError(error_description or "请求参数无效", error)
        elif error == "invalid_client":
            raise ConfigurationError(error_description or "客户端配置无效")
        else:
            raise OAuthError(error_description or f"OAuth错误: {error}", error)