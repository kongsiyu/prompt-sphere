"""DingTalk OAuth 2.0客户端实现

此模块专门实现DingTalk的OAuth 2.0授权流程，包括：
- DingTalk特定的API端点配置
- 扫码登录和密码登录支持
- DingTalk用户信息格式解析
- 企业内应用和第三方应用支持
"""

from typing import Any, Dict, Optional

from .exceptions import DingTalkAPIError, UserInfoError
from .oauth import OAuthClient, TokenResponse, UserInfo


class DingTalkUserInfo(UserInfo):
    """DingTalk用户信息扩展模型"""

    unionid: Optional[str] = None
    openid: Optional[str] = None
    mobile: Optional[str] = None
    corp_id: Optional[str] = None
    dept_id_list: Optional[list] = None


class DingTalkOAuthClient(OAuthClient):
    """DingTalk OAuth 2.0客户端实现"""

    # DingTalk OAuth 2.0 端点URLs
    AUTHORIZE_URL = "https://login.dingtalk.com/oauth2/auth"
    TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
    USER_INFO_URL = "https://api.dingtalk.com/v1.0/contact/users/me"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        corp_id: Optional[str] = None,
        prompt: str = "consent",
        scope: str = "openid",
        timeout: int = 30,
    ):
        """初始化DingTalk OAuth客户端

        Args:
            client_id: DingTalk应用的AppKey
            client_secret: DingTalk应用的AppSecret
            redirect_uri: 授权回调地址
            corp_id: 企业ID（可选，用于企业内应用）
            prompt: 授权提示类型，默认为'consent'
            scope: 权限范围，默认为'openid'
            timeout: HTTP请求超时时间
        """
        super().__init__(client_id, client_secret, redirect_uri, scope, timeout)
        self.corp_id = corp_id
        self.prompt = prompt

    @property
    def authorize_url(self) -> str:
        """DingTalk OAuth授权端点"""
        return self.AUTHORIZE_URL

    @property
    def token_url(self) -> str:
        """DingTalk令牌交换端点"""
        return self.TOKEN_URL

    @property
    def user_info_url(self) -> str:
        """DingTalk用户信息端点"""
        return self.USER_INFO_URL

    def _get_additional_auth_params(self) -> Dict[str, str]:
        """添加DingTalk特有的授权参数"""
        params = {
            "prompt": self.prompt,
        }

        # 如果是企业内应用，添加企业ID
        if self.corp_id:
            params["corpId"] = self.corp_id

        return params

    def _parse_token_response(self, token_data: Dict[str, Any]) -> TokenResponse:
        """解析DingTalk令牌响应

        DingTalk的响应格式:
        {
            "accessToken": "...",
            "refreshToken": "...",
            "expireIn": 7200,
            "corpId": "..."
        }
        """
        if "accessToken" not in token_data:
            raise DingTalkAPIError(
                "令牌响应中缺少accessToken字段",
                error_code="invalid_response",
            )

        return TokenResponse(
            access_token=token_data["accessToken"],
            token_type="Bearer",
            expires_in=token_data.get("expireIn"),
            refresh_token=token_data.get("refreshToken"),
            scope=self.scope,
        )

    async def get_user_info(self, access_token: str) -> DingTalkUserInfo:
        """获取DingTalk用户信息

        Args:
            access_token: DingTalk访问令牌

        Returns:
            DingTalk用户信息对象
        """
        # DingTalk使用x-acs-dingtalk-access-token头部
        headers = {"x-acs-dingtalk-access-token": access_token}

        try:
            response = await self._client.get(self.user_info_url, headers=headers)

            if not response.is_success:
                error_text = response.text
                raise UserInfoError(
                    f"获取DingTalk用户信息失败: {response.status_code} - {error_text}"
                )

            user_data = response.json()
            return self._parse_user_info(user_data)

        except Exception as e:
            if isinstance(e, (UserInfoError, DingTalkAPIError)):
                raise
            raise UserInfoError(f"获取DingTalk用户信息时发生错误: {str(e)}")

    def _parse_user_info(self, user_data: Dict[str, Any]) -> DingTalkUserInfo:
        """解析DingTalk用户信息响应

        DingTalk用户信息响应格式:
        {
            "nick": "张三",
            "avatarUrl": "https://...",
            "mobile": "13812345678",
            "openId": "...",
            "unionId": "...",
            "email": "zhangsan@example.com",
            "stateCode": "86"
        }
        """
        # 检查是否有错误响应
        if "errcode" in user_data and user_data["errcode"] != 0:
            error_msg = user_data.get("errmsg", "未知错误")
            raise DingTalkAPIError(
                f"DingTalk API错误: {error_msg}",
                error_code=str(user_data["errcode"]),
            )

        # 提取基础用户信息
        nick = user_data.get("nick", "")
        open_id = user_data.get("openId", "")
        union_id = user_data.get("unionId", "")

        # 使用unionId作为主要用户标识，openId作为备选
        user_id = union_id or open_id
        if not user_id:
            raise UserInfoError("DingTalk用户信息中缺少有效的用户标识")

        return DingTalkUserInfo(
            id=user_id,
            name=nick,
            email=user_data.get("email"),
            avatar=user_data.get("avatarUrl"),
            unionid=union_id,
            openid=open_id,
            mobile=user_data.get("mobile"),
            extra={
                "state_code": user_data.get("stateCode"),
                "raw_data": user_data,
            },
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """刷新DingTalk访问令牌

        DingTalk使用特殊的刷新令牌端点和参数格式
        """
        refresh_url = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"

        data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "refreshToken": refresh_token,
            "grantType": "refresh_token",
        }

        try:
            response = await self._client.post(
                refresh_url,
                json=data,  # DingTalk期望JSON格式
                headers={"Content-Type": "application/json"},
            )

            if not response.is_success:
                error_text = response.text
                raise DingTalkAPIError(
                    f"刷新DingTalk令牌失败: {response.status_code} - {error_text}"
                )

            token_data = response.json()

            # 检查API错误响应
            if "errcode" in token_data and token_data["errcode"] != 0:
                error_msg = token_data.get("errmsg", "未知错误")
                raise DingTalkAPIError(
                    f"DingTalk刷新令牌API错误: {error_msg}",
                    error_code=str(token_data["errcode"]),
                )

            return self._parse_token_response(token_data)

        except Exception as e:
            if isinstance(e, DingTalkAPIError):
                raise
            raise DingTalkAPIError(f"刷新DingTalk令牌时发生错误: {str(e)}")

    async def get_corp_info(self, access_token: str) -> Dict[str, Any]:
        """获取企业信息（可选功能）

        Args:
            access_token: DingTalk访问令牌

        Returns:
            企业信息字典
        """
        if not self.corp_id:
            raise DingTalkAPIError("获取企业信息需要提供corp_id")

        corp_info_url = "https://api.dingtalk.com/v1.0/contact/orginfos"
        headers = {"x-acs-dingtalk-access-token": access_token}

        try:
            response = await self._client.get(corp_info_url, headers=headers)

            if not response.is_success:
                error_text = response.text
                raise DingTalkAPIError(
                    f"获取企业信息失败: {response.status_code} - {error_text}"
                )

            corp_data = response.json()

            # 检查API错误响应
            if "errcode" in corp_data and corp_data["errcode"] != 0:
                error_msg = corp_data.get("errmsg", "未知错误")
                raise DingTalkAPIError(
                    f"获取企业信息API错误: {error_msg}",
                    error_code=str(corp_data["errcode"]),
                )

            return corp_data

        except Exception as e:
            if isinstance(e, DingTalkAPIError):
                raise
            raise DingTalkAPIError(f"获取企业信息时发生错误: {str(e)}")

    def build_qr_login_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """构建DingTalk扫码登录URL

        Returns:
            包含二维码登录URL和状态参数的元组
        """
        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
            "prompt": "consent",
            "login_type": "qr",  # DingTalk扫码登录特有参数
        }

        if self.corp_id:
            params["corpId"] = self.corp_id

        import urllib.parse

        query_string = urllib.parse.urlencode(params)
        qr_url = f"{self.AUTHORIZE_URL}?{query_string}"

        return qr_url, state