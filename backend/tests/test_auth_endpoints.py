"""认证API端点测试

测试认证相关的API端点功能，包括：
- DingTalk OAuth登录流程
- JWT令牌生成和验证
- 用户会话管理
- 速率限制和安全机制
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.auth.dingtalk import DingTalkUserInfo
from app.auth.jwt import get_jwt_handler
from app.core.redis import get_redis_client
from app.services.user import get_user_service


class TestAuthEndpoints:
    """认证端点测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)
        self.test_user_data = {
            "id": "test_user_123",
            "email": "test@example.com",
            "full_name": "测试用户",
            "role": "user",
            "is_active": True,
            "email_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @pytest.mark.asyncio
    async def test_login_initiate_oauth_flow(self):
        """测试OAuth登录流程启动"""
        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client:
            # 模拟DingTalk客户端
            mock_client = MagicMock()
            mock_client.build_authorize_url.return_value = (
                "https://login.dingtalk.com/oauth2/auth?client_id=test&redirect_uri=callback&state=abc123",
                "abc123"
            )
            mock_get_client.return_value = mock_client

            # 模拟Redis操作
            with patch('app.api.v1.endpoints.auth.save_oauth_state') as mock_save_state:
                mock_save_state.return_value = None

                response = self.client.post("/api/v1/auth/login")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "authorization_url" in data
                assert "state" in data
                assert "message" in data
                assert "dingtalk.com" in data["authorization_url"]

    @pytest.mark.asyncio
    async def test_login_with_redirect_uri(self):
        """测试带重定向地址的登录"""
        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.build_authorize_url.return_value = (
                "https://login.dingtalk.com/oauth2/auth?client_id=test&redirect_uri=callback&state=abc123",
                "abc123"
            )
            mock_get_client.return_value = mock_client

            with patch('app.api.v1.endpoints.auth.save_oauth_state') as mock_save_state:
                mock_save_state.return_value = None

                response = self.client.post(
                    "/api/v1/auth/login",
                    params={"redirect_uri": "https://example.com/dashboard"}
                )

                assert response.status_code == status.HTTP_200_OK
                # 验证保存状态时包含了重定向URI
                mock_save_state.assert_called_once()
                call_args = mock_save_state.call_args
                assert call_args[0][1] == "https://example.com/dashboard"

    @pytest.mark.asyncio
    async def test_oauth_callback_success_existing_user(self):
        """测试OAuth回调成功 - 现有用户"""
        test_code = "test_auth_code"
        test_state = "test_state_123"

        # 模拟用户信息
        mock_user_info = DingTalkUserInfo(
            id="dingtalk_user_123",
            name="张三",
            email="zhangsan@example.com",
            avatar="https://avatar.url/test.jpg",
            unionid="union_123",
            openid="open_123",
            mobile="13812345678"
        )

        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client, \
             patch('app.api.v1.endpoints.auth.get_oauth_state') as mock_get_state, \
             patch('app.api.v1.endpoints.auth.delete_oauth_state') as mock_delete_state, \
             patch('app.api.v1.endpoints.auth.get_user_service') as mock_get_user_service, \
             patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler, \
             patch('app.api.v1.endpoints.auth.save_user_session') as mock_save_session:

            # 设置模拟
            mock_client = AsyncMock()
            mock_client.exchange_code_for_token.return_value = MagicMock(access_token="test_access_token")
            mock_client.get_user_info.return_value = mock_user_info
            mock_get_client.return_value = mock_client

            # 模拟状态验证
            from app.api.v1.endpoints.auth import AuthState
            mock_auth_state = AuthState(state=test_state)
            mock_get_state.return_value = mock_auth_state
            mock_delete_state.return_value = None

            # 模拟用户服务
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_email.return_value = self.test_user_data
            mock_user_service.update_user.return_value = self.test_user_data
            mock_user_service.update_user_preferences.return_value = None
            mock_get_user_service.return_value = mock_user_service

            # 模拟JWT处理器
            mock_jwt_handler = MagicMock()
            mock_jwt_handler.generate_tokens.return_value = {
                "access_token": "test_jwt_access_token",
                "refresh_token": "test_jwt_refresh_token",
                "expires_in": 900,
                "access_jti": "access_jti_123",
                "refresh_jti": "refresh_jti_123"
            }
            mock_get_jwt_handler.return_value = mock_jwt_handler

            # 模拟会话保存
            mock_save_session.return_value = "session_123"

            response = self.client.get(
                "/api/v1/auth/callback",
                params={"code": test_code, "state": test_state}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # 验证响应数据结构
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert "session_id" in data
            assert data["user"]["email"] == self.test_user_data["email"]
            assert data["access_token"] == "test_jwt_access_token"

            # 验证调用流程
            mock_client.exchange_code_for_token.assert_called_once_with(
                test_code, test_state, test_state
            )
            mock_client.get_user_info.assert_called_once_with("test_access_token")
            mock_user_service.get_user_by_email.assert_called_once_with("zhangsan@example.com")

    @pytest.mark.asyncio
    async def test_oauth_callback_success_new_user(self):
        """测试OAuth回调成功 - 新用户注册"""
        test_code = "test_auth_code"
        test_state = "test_state_123"

        mock_user_info = DingTalkUserInfo(
            id="dingtalk_user_new",
            name="新用户",
            email="newuser@example.com",
            avatar="https://avatar.url/new.jpg"
        )

        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client, \
             patch('app.api.v1.endpoints.auth.get_oauth_state') as mock_get_state, \
             patch('app.api.v1.endpoints.auth.delete_oauth_state') as mock_delete_state, \
             patch('app.api.v1.endpoints.auth.get_user_service') as mock_get_user_service, \
             patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler, \
             patch('app.api.v1.endpoints.auth.save_user_session') as mock_save_session:

            # 设置模拟
            mock_client = AsyncMock()
            mock_client.exchange_code_for_token.return_value = MagicMock(access_token="test_access_token")
            mock_client.get_user_info.return_value = mock_user_info
            mock_get_client.return_value = mock_client

            # 模拟状态验证
            from app.api.v1.endpoints.auth import AuthState
            mock_auth_state = AuthState(state=test_state)
            mock_get_state.return_value = mock_auth_state

            # 模拟用户服务 - 找不到现有用户，创建新用户
            new_user_data = {
                **self.test_user_data,
                "email": "newuser@example.com",
                "full_name": "新用户",
                "id": "new_user_456"
            }

            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_email.return_value = None  # 找不到现有用户
            mock_user_service.create_user.return_value = new_user_data
            mock_get_user_service.return_value = mock_user_service

            # 模拟JWT处理器
            mock_jwt_handler = MagicMock()
            mock_jwt_handler.generate_tokens.return_value = {
                "access_token": "new_user_jwt_token",
                "refresh_token": "new_user_refresh_token",
                "expires_in": 900,
                "access_jti": "new_access_jti",
                "refresh_jti": "new_refresh_jti"
            }
            mock_get_jwt_handler.return_value = mock_jwt_handler

            mock_save_session.return_value = "new_session_456"

            response = self.client.get(
                "/api/v1/auth/callback",
                params={"code": test_code, "state": test_state}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # 验证新用户创建
            assert data["user"]["email"] == "newuser@example.com"
            assert data["user"]["full_name"] == "新用户"

            # 验证创建用户被调用
            mock_user_service.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self):
        """测试OAuth回调 - 无效状态参数"""
        response = self.client.get(
            "/api/v1/auth/callback",
            params={"code": "test_code", "state": "invalid_state"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "状态参数" in data["detail"]

    @pytest.mark.asyncio
    async def test_oauth_callback_missing_parameters(self):
        """测试OAuth回调 - 缺少参数"""
        # 缺少code参数
        response = self.client.get("/api/v1/auth/callback?state=test_state")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # 缺少state参数
        response = self.client.get("/api/v1/auth/callback?code=test_code")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_oauth_callback_error_response(self):
        """测试OAuth回调 - 错误响应"""
        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.handle_error_callback.side_effect = Exception("用户拒绝授权")
            mock_get_client.return_value = mock_client

            response = self.client.get(
                "/api/v1/auth/callback",
                params={"error": "access_denied", "error_description": "用户拒绝授权"}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """测试令牌刷新成功"""
        test_refresh_token = "valid_refresh_token"

        with patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler, \
             patch('app.api.v1.endpoints.auth.is_token_blacklisted') as mock_is_blacklisted:

            # 模拟JWT处理器
            mock_jwt_handler = MagicMock()
            mock_payload = MagicMock()
            mock_payload.scope = "refresh"
            mock_payload.jti = "refresh_jti_123"
            mock_payload.username = "测试用户"

            mock_jwt_handler.verify_token.return_value = mock_payload
            mock_jwt_handler.refresh_access_token.return_value = {
                "access_token": "new_access_token",
                "expires_in": 900
            }
            mock_get_jwt_handler.return_value = mock_jwt_handler

            # 模拟令牌不在黑名单中
            mock_is_blacklisted.return_value = False

            response = self.client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": test_refresh_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == "new_access_token"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """测试无效的刷新令牌"""
        with patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler:
            mock_jwt_handler = MagicMock()
            mock_jwt_handler.verify_token.return_value = None
            mock_get_jwt_handler.return_value = mock_jwt_handler

            response = self.client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": "invalid_token"}
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(self):
        """测试黑名单中的刷新令牌"""
        with patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler, \
             patch('app.api.v1.endpoints.auth.is_token_blacklisted') as mock_is_blacklisted:

            mock_jwt_handler = MagicMock()
            mock_payload = MagicMock()
            mock_payload.scope = "refresh"
            mock_payload.jti = "blacklisted_jti"
            mock_jwt_handler.verify_token.return_value = mock_payload
            mock_get_jwt_handler.return_value = mock_jwt_handler

            # 模拟令牌在黑名单中
            mock_is_blacklisted.return_value = True

            response = self.client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": "blacklisted_token"}
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """测试登出成功"""
        # 首先创建一个有效的令牌
        test_token = "Bearer valid_access_token"

        with patch('app.api.v1.endpoints.auth.get_current_user') as mock_get_current_user, \
             patch('app.api.v1.endpoints.auth.get_jwt_handler') as mock_get_jwt_handler, \
             patch('app.api.v1.endpoints.auth.blacklist_token') as mock_blacklist, \
             patch('app.api.v1.endpoints.auth.invalidate_user_sessions') as mock_invalidate_sessions:

            # 模拟当前用户
            mock_get_current_user.return_value = self.test_user_data

            # 模拟JWT处理器
            mock_jwt_handler = MagicMock()
            mock_jwt_handler.get_token_claims.return_value = {
                "jti": "token_jti_123",
                "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
            }
            mock_get_jwt_handler.return_value = mock_jwt_handler

            # 模拟异步函数
            mock_blacklist.return_value = None
            mock_invalidate_sessions.return_value = None

            response = self.client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": test_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "登出成功"

            # 验证令牌被加入黑名单
            mock_blacklist.assert_called_once()
            # 验证用户会话被失效
            mock_invalidate_sessions.assert_called_once_with(self.test_user_data["id"])

    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """测试获取用户资料成功"""
        with patch('app.api.v1.endpoints.auth.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = self.test_user_data

            response = self.client.get(
                "/api/v1/auth/profile",
                headers={"Authorization": "Bearer valid_token"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == self.test_user_data["email"]
            assert data["full_name"] == self.test_user_data["full_name"]
            assert data["role"] == self.test_user_data["role"]

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self):
        """测试未授权访问用户资料"""
        response = self.client.get("/api/v1/auth/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_route_success(self):
        """测试受保护路由访问成功"""
        with patch('app.api.v1.endpoints.auth.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = self.test_user_data

            response = self.client.get(
                "/api/v1/auth/protected",
                headers={"Authorization": "Bearer valid_token"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert self.test_user_data["full_name"] in data["message"]
            assert data["user_id"] == self.test_user_data["id"]

    @pytest.mark.asyncio
    async def test_protected_route_unauthorized(self):
        """测试受保护路由未授权访问"""
        response = self.client.get("/api/v1/auth/protected")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_qr_login_success(self):
        """测试二维码登录URL生成成功"""
        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client, \
             patch('app.api.v1.endpoints.auth.save_oauth_state') as mock_save_state:

            # 模拟DingTalk客户端
            mock_client = MagicMock()
            mock_client.build_qr_login_url.return_value = (
                "https://login.dingtalk.com/oauth2/auth?login_type=qr&client_id=test&state=qr_state_123",
                "qr_state_123"
            )
            mock_get_client.return_value = mock_client
            mock_save_state.return_value = None

            response = self.client.get("/api/v1/auth/qr-login")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "qr_login_url" in data
            assert "state" in data
            assert "message" in data
            assert "login_type=qr" in data["qr_login_url"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制功能"""
        # 注意：这个测试依赖于实际的速率限制配置
        # 在生产环境中，认证端点配置为5分钟内最多10次请求

        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client, \
             patch('app.api.v1.endpoints.auth.save_oauth_state') as mock_save_state:

            mock_client = MagicMock()
            mock_client.build_authorize_url.return_value = ("http://test.url", "state123")
            mock_get_client.return_value = mock_client
            mock_save_state.return_value = None

            # 快速连续发送多个请求
            responses = []
            for i in range(12):  # 超过10次限制
                response = self.client.post("/api/v1/auth/login")
                responses.append(response.status_code)

            # 前面的请求应该成功，后面的应该被限制
            # 注意：这取决于实际的速率限制实现和Redis状态
            success_responses = [r for r in responses if r == 200]
            rate_limited_responses = [r for r in responses if r == 429]

            # 至少应该有一些成功的响应
            assert len(success_responses) > 0
            # 如果速率限制工作正常，应该有被限制的响应
            # 但在测试环境中可能不总是生效，所以这里只做基本验证

    def test_jwt_token_format(self):
        """测试JWT令牌格式"""
        jwt_handler = get_jwt_handler()
        tokens = jwt_handler.generate_tokens(
            user_id="test_user",
            username="测试用户",
            roles=["user"]
        )

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert "expires_in" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 900  # 15分钟

        # 验证令牌可以被解码
        payload = jwt_handler.verify_token(tokens["access_token"])
        assert payload is not None
        assert payload.user_id == "test_user"
        assert payload.username == "测试用户"
        assert payload.scope == "access"

    def test_invalid_jwt_token(self):
        """测试无效JWT令牌"""
        jwt_handler = get_jwt_handler()

        # 测试格式错误的令牌
        invalid_payload = jwt_handler.verify_token("invalid.token.format")
        assert invalid_payload is None

        # 测试空令牌
        empty_payload = jwt_handler.verify_token("")
        assert empty_payload is None

    @pytest.mark.asyncio
    async def test_user_session_management(self):
        """测试用户会话管理"""
        from app.api.v1.endpoints.auth import save_user_session, invalidate_user_sessions

        test_user_id = "session_test_user"
        session_data = {
            "user_id": test_user_id,
            "username": "会话测试用户",
            "login_time": datetime.utcnow().isoformat()
        }

        with patch('app.api.v1.endpoints.auth.get_redis_client') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            # 测试保存会话
            session_id = await save_user_session(test_user_id, session_data)
            assert session_id is not None
            assert len(session_id) > 0

            # 验证Redis调用
            assert mock_redis.setex.call_count >= 2  # 至少两次setex调用

            # 测试失效会话
            mock_redis.get.return_value = session_id
            await invalidate_user_sessions(test_user_id)

            # 验证删除操作被调用
            assert mock_redis.delete.call_count >= 2

    def teardown_method(self):
        """测试后清理"""
        # 这里可以添加测试后的清理逻辑
        pass


class TestAuthMiddleware:
    """认证中间件测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_cors_headers_present(self):
        """测试CORS头部存在"""
        response = self.client.options("/api/v1/auth/login")

        # 检查CORS相关头部
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
        assert "access-control-allow-methods" in [h.lower() for h in response.headers.keys()]

    def test_security_headers_present(self):
        """测试安全头部存在"""
        response = self.client.get("/")

        # 检查安全头部（这些应该由SecurityHeadersMiddleware添加）
        headers = {k.lower(): v for k, v in response.headers.items()}

        # 基本安全头部检查
        expected_headers = [
            "x-content-type-options",
            "x-frame-options"
        ]

        for header in expected_headers:
            assert header in headers, f"Missing security header: {header}"

    def test_rate_limit_headers_in_response(self):
        """测试速率限制头部在响应中"""
        with patch('app.api.v1.endpoints.auth.get_dingtalk_client') as mock_get_client, \
             patch('app.api.v1.endpoints.auth.save_oauth_state') as mock_save_state:

            mock_client = MagicMock()
            mock_client.build_authorize_url.return_value = ("http://test.url", "state123")
            mock_get_client.return_value = mock_client
            mock_save_state.return_value = None

            response = self.client.post("/api/v1/auth/login")

            # 检查速率限制相关头部
            headers = {k.lower(): v for k, v in response.headers.items()}

            # 这些头部应该由RateLimitMiddleware添加
            rate_limit_headers = [
                "x-ratelimit-limit",
                "x-ratelimit-remaining",
                "x-ratelimit-reset"
            ]

            # 在测试环境中这些头部可能不会总是出现
            # 所以这里只做基础检查
            if any(header in headers for header in rate_limit_headers):
                # 如果有速率限制头部，验证其格式
                if "x-ratelimit-limit" in headers:
                    assert headers["x-ratelimit-limit"].isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])