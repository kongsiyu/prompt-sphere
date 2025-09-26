"""会话服务测试

测试会话管理服务的所有功能
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.session import SessionService, SessionData, get_session_service
from app.services.base import ValidationError, ServiceError


@pytest.fixture
async def session_service():
    """会话服务实例"""
    service = SessionService()
    yield service


@pytest.fixture
def sample_session_data():
    """示例会话数据"""
    now = datetime.now(timezone.utc)
    return {
        "session_id": "test-session-id",
        "user_id": "test-user-id",
        "username": "testuser",
        "roles": ["user"],
        "created_at": now,
        "last_accessed": now,
        "expires_at": now + timedelta(hours=24),
        "ip_address": "192.168.1.1",
        "user_agent": "TestAgent/1.0"
    }


@pytest.fixture
def sample_jwt_tokens():
    """示例JWT令牌"""
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
        "expires_in": 900,
        "access_jti": "access-jti-123",
        "refresh_jti": "refresh-jti-456"
    }


class TestSessionServiceCreation:
    """测试会话创建功能"""

    @patch('app.services.session.get_jwt_handler')
    @patch('app.services.session.get_redis_client')
    async def test_create_session_success(self, mock_redis_client, mock_jwt_handler, session_service, sample_jwt_tokens):
        """测试成功创建会话"""
        # 设置JWT处理器模拟
        mock_jwt = AsyncMock()
        mock_jwt.generate_tokens.return_value = sample_jwt_tokens
        mock_jwt_handler.return_value = mock_jwt

        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 执行测试
        result = await session_service.create_session(
            user_id="test-user-id",
            username="testuser",
            roles=["user"],
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0"
        )

        # 验证结果
        assert result is not None
        assert "session_id" in result
        assert result["user_id"] == "test-user-id"
        assert result["username"] == "testuser"
        assert result["roles"] == ["user"]
        assert result["access_token"] == sample_jwt_tokens["access_token"]
        assert result["refresh_token"] == sample_jwt_tokens["refresh_token"]

        # 验证调用
        mock_jwt.generate_tokens.assert_called_once_with("test-user-id", "testuser", ["user"])
        mock_redis.set.assert_called()
        mock_redis.sadd.assert_called()

    async def test_create_session_invalid_input(self, session_service):
        """测试创建会话时输入无效"""
        # 缺少必要参数
        with pytest.raises(ValidationError):
            await session_service.create_session(
                user_id="",  # 空用户ID
                username="testuser",
                roles=["user"]
            )

        # 角色不是列表
        with pytest.raises(ValidationError):
            await session_service.create_session(
                user_id="test-user-id",
                username="testuser",
                roles="user"  # 应该是列表
            )

    @patch('app.services.session.get_jwt_handler')
    @patch('app.services.session.get_redis_client')
    async def test_create_session_jwt_error(self, mock_redis_client, mock_jwt_handler, session_service):
        """测试JWT生成错误时的处理"""
        # 设置JWT处理器抛出异常
        mock_jwt = AsyncMock()
        mock_jwt.generate_tokens.side_effect = Exception("JWT生成失败")
        mock_jwt_handler.return_value = mock_jwt

        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 执行测试，期望抛出服务异常
        with pytest.raises(ServiceError):
            await session_service.create_session(
                user_id="test-user-id",
                username="testuser",
                roles=["user"]
            )


class TestSessionServiceRetrieval:
    """测试会话获取功能"""

    @patch('app.services.session.get_redis_client')
    async def test_get_session_success(self, mock_redis_client, session_service, sample_session_data):
        """测试成功获取会话"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟Redis返回会话数据
        session_json = json.dumps({
            **sample_session_data,
            "created_at": sample_session_data["created_at"].isoformat(),
            "last_accessed": sample_session_data["last_accessed"].isoformat(),
            "expires_at": sample_session_data["expires_at"].isoformat()
        })
        mock_redis.get.return_value = session_json.encode()

        # 执行测试
        result = await session_service.get_session("test-session-id")

        # 验证结果
        assert result is not None
        assert isinstance(result, SessionData)
        assert result.session_id == "test-session-id"
        assert result.user_id == "test-user-id"
        assert result.username == "testuser"
        assert not result.is_expired()

        # 验证调用
        mock_redis.get.assert_called_once_with("session:test-session-id")

    @patch('app.services.session.get_redis_client')
    async def test_get_session_not_found(self, mock_redis_client, session_service):
        """测试获取不存在的会话"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟Redis返回空
        mock_redis.get.return_value = None

        # 执行测试
        result = await session_service.get_session("nonexistent-session")

        # 验证结果
        assert result is None

        # 验证调用
        mock_redis.get.assert_called_once_with("session:nonexistent-session")

    @patch('app.services.session.get_redis_client')
    async def test_get_session_expired(self, mock_redis_client, session_service, sample_session_data):
        """测试获取已过期的会话"""
        # 设置过期时间为过去
        sample_session_data["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)

        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟Redis返回过期会话数据
        session_json = json.dumps({
            **sample_session_data,
            "created_at": sample_session_data["created_at"].isoformat(),
            "last_accessed": sample_session_data["last_accessed"].isoformat(),
            "expires_at": sample_session_data["expires_at"].isoformat()
        })
        mock_redis.get.return_value = session_json.encode()

        # 执行测试
        result = await session_service.get_session("expired-session")

        # 验证结果
        assert result is None

        # 验证会话被清理
        mock_redis.delete.assert_called()


class TestSessionServiceValidation:
    """测试会话验证功能"""

    @patch('app.services.session.SessionService.get_session')
    @patch('app.services.session.SessionService._update_session')
    async def test_validate_session_success(self, mock_update_session, mock_get_session, session_service, sample_session_data):
        """测试成功验证会话"""
        # 模拟获取到有效会话
        session_data = SessionData(**sample_session_data)
        mock_get_session.return_value = session_data
        mock_update_session.return_value = None

        # 执行测试
        result = await session_service.validate_session("test-session-id")

        # 验证结果
        assert result is not None
        assert result["session_id"] == "test-session-id"
        assert result["user_id"] == "test-user-id"
        assert result["username"] == "testuser"
        assert result["roles"] == ["user"]

        # 验证调用
        mock_get_session.assert_called_once_with("test-session-id")
        mock_update_session.assert_called_once()

    @patch('app.services.session.SessionService.get_session')
    async def test_validate_session_not_found(self, mock_get_session, session_service):
        """测试验证不存在的会话"""
        # 模拟会话不存在
        mock_get_session.return_value = None

        # 执行测试
        result = await session_service.validate_session("nonexistent-session")

        # 验证结果
        assert result is None

        # 验证调用
        mock_get_session.assert_called_once_with("nonexistent-session")


class TestSessionServiceExtension:
    """测试会话延期功能"""

    @patch('app.services.session.SessionService.get_session')
    @patch('app.services.session.SessionService._update_session')
    async def test_extend_session_success(self, mock_update_session, mock_get_session, session_service, sample_session_data):
        """测试成功延长会话"""
        # 模拟获取到有效会话
        session_data = SessionData(**sample_session_data)
        mock_get_session.return_value = session_data
        mock_update_session.return_value = None

        # 执行测试
        result = await session_service.extend_session("test-session-id", hours=48)

        # 验证结果
        assert result is True

        # 验证调用
        mock_get_session.assert_called_once_with("test-session-id")
        mock_update_session.assert_called_once()

    @patch('app.services.session.SessionService.get_session')
    async def test_extend_session_not_found(self, mock_get_session, session_service):
        """测试延长不存在的会话"""
        # 模拟会话不存在
        mock_get_session.return_value = None

        # 执行测试
        result = await session_service.extend_session("nonexistent-session")

        # 验证结果
        assert result is False

        # 验证调用
        mock_get_session.assert_called_once_with("nonexistent-session")


class TestSessionServiceDestruction:
    """测试会话销毁功能"""

    @patch('app.services.session.SessionService.get_session')
    @patch('app.services.session.SessionService._cleanup_session')
    async def test_destroy_session_success(self, mock_cleanup_session, mock_get_session, session_service, sample_session_data):
        """测试成功销毁会话"""
        # 模拟获取到会话
        session_data = SessionData(**sample_session_data)
        mock_get_session.return_value = session_data
        mock_cleanup_session.return_value = None

        # 执行测试
        result = await session_service.destroy_session("test-session-id")

        # 验证结果
        assert result is True

        # 验证调用
        mock_get_session.assert_called_once_with("test-session-id")
        mock_cleanup_session.assert_called_once_with("test-session-id")

    @patch('app.services.session.SessionService.get_session')
    @patch('app.services.session.SessionService._cleanup_session')
    async def test_destroy_session_not_found(self, mock_cleanup_session, mock_get_session, session_service):
        """测试销毁不存在的会话"""
        # 模拟会话不存在
        mock_get_session.return_value = None
        mock_cleanup_session.return_value = None

        # 执行测试
        result = await session_service.destroy_session("nonexistent-session")

        # 验证结果
        assert result is True  # 销毁操作即使会话不存在也返回成功

        # 验证调用
        mock_get_session.assert_called_once_with("nonexistent-session")
        mock_cleanup_session.assert_called_once_with("nonexistent-session")


class TestSessionServiceUserSessionManagement:
    """测试用户会话管理功能"""

    @patch('app.services.session.get_redis_client')
    @patch('app.services.session.SessionService._cleanup_session')
    async def test_destroy_user_sessions_success(self, mock_cleanup_session, mock_redis_client, session_service):
        """测试成功销毁用户的所有会话"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟用户有多个会话
        session_ids = [b"session-1", b"session-2", b"session-3"]
        mock_redis.smembers.return_value = session_ids
        mock_cleanup_session.return_value = None

        # 执行测试
        result = await session_service.destroy_user_sessions("test-user-id")

        # 验证结果
        assert result == 3  # 销毁了3个会话

        # 验证调用
        mock_redis.smembers.assert_called_once_with("user_sessions:test-user-id")
        assert mock_cleanup_session.call_count == 3
        mock_redis.delete.assert_called_once_with("user_sessions:test-user-id")

    @patch('app.services.session.get_redis_client')
    @patch('app.services.session.SessionService._cleanup_session')
    async def test_destroy_user_sessions_except_current(self, mock_cleanup_session, mock_redis_client, session_service):
        """测试销毁用户的所有会话，但保留当前会话"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟用户有多个会话
        session_ids = [b"session-1", b"session-2", b"current-session"]
        mock_redis.smembers.return_value = session_ids
        mock_cleanup_session.return_value = None

        # 执行测试，保留当前会话
        result = await session_service.destroy_user_sessions("test-user-id", except_session_id="current-session")

        # 验证结果
        assert result == 2  # 销毁了2个会话（保留了1个）

        # 验证调用
        assert mock_cleanup_session.call_count == 2
        mock_redis.sadd.assert_called_with("user_sessions:test-user-id", "current-session")


class TestSessionServiceTokenRefresh:
    """测试令牌刷新功能"""

    @patch('app.services.session.get_jwt_handler')
    @patch('app.services.session.get_redis_client')
    async def test_refresh_tokens_success(self, mock_redis_client, mock_jwt_handler, session_service):
        """测试成功刷新令牌"""
        # 设置JWT处理器模拟
        mock_jwt = AsyncMock()

        # 模拟JWT负载
        from app.auth.jwt import JWTPayload
        mock_payload = JWTPayload(
            sub="test-user-id",
            exp=int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti="refresh-jti-456",
            scope="refresh",
            user_id="test-user-id",
            username="testuser",
            roles=["user"]
        )
        mock_jwt.verify_token.return_value = mock_payload

        # 模拟刷新令牌成功
        new_tokens = {
            "access_token": "new-access-token",
            "token_type": "bearer",
            "expires_in": 900,
            "access_jti": "new-access-jti"
        }
        mock_jwt.refresh_access_token.return_value = new_tokens
        mock_jwt_handler.return_value = mock_jwt

        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟Redis返回刷新令牌数据
        refresh_data = {
            "session_id": "test-session-id",
            "user_id": "test-user-id",
            "username": "testuser",
            "roles": ["user"]
        }
        mock_redis.get.return_value = json.dumps(refresh_data).encode()

        # 执行测试
        result = await session_service.refresh_tokens("test-refresh-token")

        # 验证结果
        assert result is not None
        assert result["access_token"] == new_tokens["access_token"]
        assert result["user_id"] == "test-user-id"
        assert result["username"] == "testuser"
        assert result["roles"] == ["user"]

        # 验证调用
        mock_jwt.verify_token.assert_called_once_with("test-refresh-token")
        mock_jwt.refresh_access_token.assert_called_once_with("test-refresh-token")
        mock_redis.get.assert_called_once()

    @patch('app.services.session.get_jwt_handler')
    async def test_refresh_tokens_invalid_token(self, mock_jwt_handler, session_service):
        """测试刷新无效令牌"""
        # 设置JWT处理器模拟
        mock_jwt = AsyncMock()
        mock_jwt.verify_token.return_value = None  # 无效令牌
        mock_jwt_handler.return_value = mock_jwt

        # 执行测试
        result = await session_service.refresh_tokens("invalid-refresh-token")

        # 验证结果
        assert result is None

        # 验证调用
        mock_jwt.verify_token.assert_called_once_with("invalid-refresh-token")


class TestSessionServiceCleanup:
    """测试会话清理功能"""

    @patch('app.services.session.get_redis_client')
    async def test_cleanup_expired_sessions_success(self, mock_redis_client, session_service):
        """测试成功清理过期会话"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟扫描结果
        mock_redis.redis.scan.side_effect = [
            (0, [b"session:expired-1", b"session:valid-1"]),  # 第一次扫描
        ]

        # 模拟get_session的行为
        with patch.object(session_service, 'get_session') as mock_get_session:
            # 第一个会话过期（返回None），第二个有效（返回会话对象）
            mock_get_session.side_effect = [None, MagicMock()]

        with patch.object(session_service, '_cleanup_session') as mock_cleanup:
            mock_cleanup.return_value = None

            # 执行测试
            result = await session_service.cleanup_expired_sessions()

            # 验证结果
            assert result is not None
            assert "cleaned_sessions" in result
            assert result["cleaned_sessions"] >= 0

            # 验证调用
            mock_redis.redis.scan.assert_called()


class TestSessionServiceStatistics:
    """测试会话统计功能"""

    @patch('app.services.session.get_redis_client')
    @patch('app.services.session.SessionService.get_session')
    async def test_get_session_statistics_success(self, mock_get_session, mock_redis_client, session_service, sample_session_data):
        """测试成功获取会话统计"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # 模拟扫描会话
        mock_redis.redis.scan.side_effect = [
            (0, [b"session:1", b"session:2"]),  # 会话扫描
            (0, [b"refresh_token:1", b"refresh_token:2"])  # 刷新令牌扫描
        ]

        # 模拟会话数据
        session_data = SessionData(**sample_session_data)
        mock_get_session.side_effect = [session_data, session_data]

        # 执行测试
        result = await session_service.get_session_statistics()

        # 验证结果
        assert result is not None
        assert "total_sessions" in result
        assert "active_sessions" in result
        assert "unique_users" in result
        assert "refresh_tokens" in result

        # 验证调用
        mock_redis.redis.scan.assert_called()


class TestSessionServiceHealthCheck:
    """测试会话服务健康检查"""

    @patch('app.services.session.get_redis_client')
    @patch('app.services.session.get_jwt_handler')
    @patch('app.services.session.SessionService.get_session_statistics')
    async def test_health_check_healthy(self, mock_get_stats, mock_jwt_handler, mock_redis_client, session_service, sample_jwt_tokens):
        """测试健康状态检查 - 健康"""
        # 设置Redis客户端模拟
        mock_redis = AsyncMock()
        mock_redis.redis.ping.return_value = True
        mock_redis_client.return_value = mock_redis

        # 设置JWT处理器模拟
        mock_jwt = AsyncMock()
        mock_jwt.generate_tokens.return_value = sample_jwt_tokens
        mock_jwt_handler.return_value = mock_jwt

        # 设置统计模拟
        mock_get_stats.return_value = {"active_sessions": 10}

        # 执行测试
        result = await session_service.health_check()

        # 验证结果
        assert result["status"] == "healthy"
        assert result["redis_connection"] is True
        assert result["jwt_handler_status"] is True
        assert result["active_sessions"] == 10

        # 验证调用
        mock_redis.redis.ping.assert_called_once()
        mock_jwt.generate_tokens.assert_called_once()

    @patch('app.services.session.get_redis_client')
    async def test_health_check_unhealthy(self, mock_redis_client, session_service):
        """测试健康状态检查 - 不健康"""
        # 设置Redis客户端抛出异常
        mock_redis = AsyncMock()
        mock_redis.redis.ping.side_effect = Exception("Redis连接失败")
        mock_redis_client.return_value = mock_redis

        # 执行测试
        result = await session_service.health_check()

        # 验证结果
        assert result["status"] == "unhealthy"
        assert result["redis_connection"] is False
        assert "error" in result


class TestSessionServiceSingleton:
    """测试会话服务单例模式"""

    def test_get_session_service_singleton(self):
        """测试获取会话服务实例是单例"""
        service1 = get_session_service()
        service2 = get_session_service()

        assert service1 is service2
        assert isinstance(service1, SessionService)


class TestSessionData:
    """测试SessionData类"""

    def test_session_data_creation(self, sample_session_data):
        """测试SessionData创建"""
        session = SessionData(**sample_session_data)

        assert session.session_id == sample_session_data["session_id"]
        assert session.user_id == sample_session_data["user_id"]
        assert session.username == sample_session_data["username"]
        assert session.roles == sample_session_data["roles"]

    def test_session_data_to_dict(self, sample_session_data):
        """测试SessionData转为字典"""
        session = SessionData(**sample_session_data)
        result = session.to_dict()

        assert isinstance(result, dict)
        assert result["session_id"] == sample_session_data["session_id"]
        assert result["user_id"] == sample_session_data["user_id"]

    def test_session_data_from_dict(self, sample_session_data):
        """测试从字典创建SessionData"""
        # 转换时间为字符串格式
        dict_data = {
            **sample_session_data,
            "created_at": sample_session_data["created_at"].isoformat(),
            "last_accessed": sample_session_data["last_accessed"].isoformat(),
            "expires_at": sample_session_data["expires_at"].isoformat()
        }

        session = SessionData.from_dict(dict_data)

        assert session.session_id == sample_session_data["session_id"]
        assert session.user_id == sample_session_data["user_id"]

    def test_session_data_is_expired(self, sample_session_data):
        """测试会话过期检查"""
        # 测试未过期会话
        session = SessionData(**sample_session_data)
        assert not session.is_expired()

        # 测试过期会话
        sample_session_data["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_session = SessionData(**sample_session_data)
        assert expired_session.is_expired()

    def test_session_data_extend_expiration(self, sample_session_data):
        """测试会话延期"""
        session = SessionData(**sample_session_data)
        original_expires = session.expires_at

        session.extend_expiration(hours=48)

        assert session.expires_at > original_expires
        # 验证延长了大约48小时（允许小的时间差）
        time_diff = session.expires_at - original_expires
        assert 47.9 <= time_diff.total_seconds() / 3600 <= 48.1