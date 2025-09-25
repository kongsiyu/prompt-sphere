"""用户服务测试

测试用户管理服务的所有功能
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.user import UserService, get_user_service
from app.services.base import ValidationError, ConflictError, NotFoundError, ServiceError
from database.models.user import User


@pytest.fixture
async def user_service():
    """用户服务实例"""
    service = UserService()
    yield service


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "测试用户",
        "role": "user"
    }


@pytest.fixture
def sample_user_dict():
    """示例用户字典数据"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "full_name": "测试用户",
        "role": "user",
        "is_active": True,
        "email_verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_login_at": None,
        "login_attempts": 0,
        "locked_until": None,
        "preferences": {
            "theme": "light",
            "language": "zh-CN",
            "notifications": {"email": True, "push": False}
        }
    }


class TestUserServiceCreation:
    """测试用户创建功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_create_user_success(self, mock_get_session, mock_user_repo, user_service, sample_user_data):
        """测试成功创建用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户不存在
        mock_repo_instance.find_by_email.return_value = None

        # 模拟创建用户
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = sample_user_data["email"]
        mock_user.to_dict.return_value = {"id": "test-user-id", "email": sample_user_data["email"]}
        mock_repo_instance.create_user.return_value = mock_user

        # 执行测试
        result = await user_service.create_user(**sample_user_data)

        # 验证结果
        assert result is not None
        assert result["email"] == sample_user_data["email"]

        # 验证调用
        mock_repo_instance.find_by_email.assert_called_once_with(sample_user_data["email"])
        mock_repo_instance.create_user.assert_called_once()

    async def test_create_user_invalid_email(self, user_service):
        """测试创建用户时邮箱格式无效"""
        invalid_data = {
            "email": "invalid-email",
            "password": "TestPass123",
            "full_name": "测试用户",
            "role": "user"
        }

        with pytest.raises(ValidationError):
            await user_service.create_user(**invalid_data)

    async def test_create_user_invalid_password(self, user_service):
        """测试创建用户时密码格式无效"""
        invalid_data = {
            "email": "test@example.com",
            "password": "123",  # 太短
            "full_name": "测试用户",
            "role": "user"
        }

        with pytest.raises(ValidationError):
            await user_service.create_user(**invalid_data)

    async def test_create_user_invalid_role(self, user_service):
        """测试创建用户时角色无效"""
        invalid_data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "full_name": "测试用户",
            "role": "invalid_role"
        }

        with pytest.raises(ValidationError):
            await user_service.create_user(**invalid_data)

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_create_user_already_exists(self, mock_get_session, mock_user_repo, user_service, sample_user_data):
        """测试创建已存在的用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户已存在
        existing_user = MagicMock()
        mock_repo_instance.find_by_email.return_value = existing_user

        # 执行测试，期望抛出冲突异常
        with pytest.raises(ConflictError):
            await user_service.create_user(**sample_user_data)


class TestUserServiceRetrieval:
    """测试用户获取功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_get_user_success(self, mock_get_session, mock_user_repo, user_service, sample_user_dict):
        """测试成功获取用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户存在
        mock_user = MagicMock()
        mock_user.to_dict.return_value = sample_user_dict
        mock_repo_instance.get_by_id.return_value = mock_user

        # 执行测试
        result = await user_service.get_user("test-user-id")

        # 验证结果
        assert result is not None
        assert result["id"] == sample_user_dict["id"]
        assert result["email"] == sample_user_dict["email"]

        # 验证调用
        mock_repo_instance.get_by_id.assert_called_once_with("test-user-id")

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_get_user_not_found(self, mock_get_session, mock_user_repo, user_service):
        """测试获取不存在的用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户不存在
        mock_repo_instance.get_by_id.return_value = None

        # 执行测试
        result = await user_service.get_user("nonexistent-user")

        # 验证结果
        assert result is None

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_get_user_by_email_success(self, mock_get_session, mock_user_repo, user_service, sample_user_dict):
        """测试通过邮箱成功获取用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户存在
        mock_user = MagicMock()
        mock_user.to_dict.return_value = sample_user_dict
        mock_repo_instance.find_by_email.return_value = mock_user

        # 执行测试
        result = await user_service.get_user_by_email("test@example.com")

        # 验证结果
        assert result is not None
        assert result["email"] == sample_user_dict["email"]

        # 验证调用
        mock_repo_instance.find_by_email.assert_called_once_with("test@example.com")


class TestUserServiceUpdate:
    """测试用户更新功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_update_user_success(self, mock_get_session, mock_user_repo, user_service, sample_user_dict):
        """测试成功更新用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户存在
        mock_user = MagicMock()
        mock_user.to_dict.return_value = sample_user_dict
        mock_repo_instance.get_by_id.return_value = mock_user

        # 执行测试
        update_data = {"full_name": "新名称", "role": "admin"}
        result = await user_service.update_user("test-user-id", **update_data)

        # 验证结果
        assert result is not None

        # 验证调用
        mock_repo_instance.get_by_id.assert_called_once_with("test-user-id")

    async def test_update_user_not_found(self, user_service):
        """测试更新不存在的用户"""
        with patch('app.services.user.UserRepository') as mock_user_repo, \
             patch('app.services.user.get_session') as mock_get_session:

            # 设置模拟
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None

            mock_repo_instance = AsyncMock()
            mock_user_repo.return_value = mock_repo_instance

            # 模拟用户不存在
            mock_repo_instance.get_by_id.return_value = None

            # 执行测试，期望抛出未找到异常
            with pytest.raises(NotFoundError):
                await user_service.update_user("nonexistent-user", full_name="新名称")

    async def test_update_user_invalid_role(self, user_service):
        """测试更新用户时提供无效角色"""
        with patch('app.services.user.UserRepository') as mock_user_repo, \
             patch('app.services.user.get_session') as mock_get_session:

            # 设置模拟
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None

            mock_repo_instance = AsyncMock()
            mock_user_repo.return_value = mock_repo_instance

            # 模拟用户存在
            mock_user = MagicMock()
            mock_repo_instance.get_by_id.return_value = mock_user

            # 执行测试，期望抛出验证异常
            with pytest.raises(ValidationError):
                await user_service.update_user("test-user-id", role="invalid_role")


class TestUserServiceAuthentication:
    """测试用户身份验证功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_authenticate_user_success(self, mock_get_session, mock_user_repo, user_service, sample_user_dict):
        """测试成功认证用户"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟认证成功
        mock_user = MagicMock()
        mock_user.to_dict.return_value = sample_user_dict
        mock_repo_instance.authenticate.return_value = mock_user
        mock_repo_instance.update_last_login.return_value = True

        # 执行测试
        result = await user_service.authenticate_user("test@example.com", "TestPass123")

        # 验证结果
        assert result is not None
        assert result["email"] == sample_user_dict["email"]

        # 验证调用
        mock_repo_instance.authenticate.assert_called_once_with("test@example.com", "TestPass123")
        mock_repo_instance.update_last_login.assert_called_once()

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_authenticate_user_failed(self, mock_get_session, mock_user_repo, user_service):
        """测试认证失败"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟认证失败
        mock_repo_instance.authenticate.return_value = None

        # 执行测试
        result = await user_service.authenticate_user("test@example.com", "WrongPass")

        # 验证结果
        assert result is None

        # 验证调用
        mock_repo_instance.authenticate.assert_called_once_with("test@example.com", "WrongPass")


class TestUserServicePasswordChange:
    """测试密码修改功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_change_password_success(self, mock_get_session, mock_user_repo, user_service):
        """测试成功修改密码"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟密码修改成功
        mock_repo_instance.update_password.return_value = True

        # 执行测试
        result = await user_service.change_password("test-user-id", "NewPassword123")

        # 验证结果
        assert result is True

        # 验证调用
        mock_repo_instance.update_password.assert_called_once_with("test-user-id", "NewPassword123")

    async def test_change_password_invalid_password(self, user_service):
        """测试修改密码时提供无效密码"""
        # 执行测试，期望抛出验证异常
        with pytest.raises(ValidationError):
            await user_service.change_password("test-user-id", "123")  # 密码太短

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_change_password_user_not_found(self, mock_get_session, mock_user_repo, user_service):
        """测试修改不存在用户的密码"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户不存在
        mock_repo_instance.update_password.return_value = False

        # 执行测试，期望抛出未找到异常
        with pytest.raises(NotFoundError):
            await user_service.change_password("nonexistent-user", "NewPassword123")


class TestUserServiceList:
    """测试用户列表功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_list_users_success(self, mock_get_session, mock_user_repo, user_service, sample_user_dict):
        """测试成功获取用户列表"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟用户列表
        mock_user = MagicMock()
        mock_user.to_dict.return_value = sample_user_dict
        mock_repo_instance.get_active_users.return_value = [mock_user, mock_user]

        # 模拟统计信息
        mock_repo_instance.get_user_statistics.return_value = {
            "active_users": 2,
            "total_users": 2
        }

        # 执行测试
        result = await user_service.list_users(limit=10, offset=0)

        # 验证结果
        assert result is not None
        assert "users" in result
        assert "total" in result
        assert len(result["users"]) == 2
        assert result["total"] == 2

        # 验证调用
        mock_repo_instance.get_active_users.assert_called_once_with(
            limit=10, offset=0, order_by="created_at", order_desc=True
        )


class TestUserServiceStatistics:
    """测试用户统计功能"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_get_user_statistics_success(self, mock_get_session, mock_user_repo, user_service):
        """测试成功获取用户统计"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟统计数据
        expected_stats = {
            "total_users": 100,
            "active_users": 80,
            "inactive_users": 20,
            "users_by_role": {"admin": 5, "user": 70, "viewer": 25},
            "recent_users": 10
        }
        mock_repo_instance.get_user_statistics.return_value = expected_stats

        # 执行测试
        result = await user_service.get_user_statistics()

        # 验证结果
        assert result == expected_stats

        # 验证调用
        mock_repo_instance.get_user_statistics.assert_called_once()


class TestUserServiceHealthCheck:
    """测试用户服务健康检查"""

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_health_check_healthy(self, mock_get_session, mock_user_repo, user_service):
        """测试健康状态检查 - 健康"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟健康的服务
        mock_repo_instance.get_user_statistics.return_value = {"total_users": 100}

        # 模拟缓存健康
        with patch.object(user_service, 'cache') as mock_cache_prop:
            mock_cache = AsyncMock()
            mock_cache_prop.return_value = mock_cache

            # 执行测试
            result = await user_service.health_check()

            # 验证结果
            assert result["status"] == "healthy"
            assert result["database_connection"] is True
            assert result["user_count"] == 100

    @patch('app.services.user.UserRepository')
    @patch('app.services.user.get_session')
    async def test_health_check_unhealthy(self, mock_get_session, mock_user_repo, user_service):
        """测试健康状态检查 - 不健康"""
        # 设置模拟
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_user_repo.return_value = mock_repo_instance

        # 模拟数据库错误
        mock_repo_instance.get_user_statistics.side_effect = Exception("数据库连接失败")

        # 执行测试
        result = await user_service.health_check()

        # 验证结果
        assert result["status"] == "unhealthy"
        assert result["database_connection"] is False
        assert "error" in result


class TestUserServiceSingleton:
    """测试用户服务单例模式"""

    def test_get_user_service_singleton(self):
        """测试获取用户服务实例是单例"""
        service1 = get_user_service()
        service2 = get_user_service()

        assert service1 is service2
        assert isinstance(service1, UserService)