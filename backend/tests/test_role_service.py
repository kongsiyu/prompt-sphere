"""角色服务测试

测试角色和权限管理服务的所有功能
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.role import RoleService, Role, Permission, get_role_service, has_permission, get_user_all_permissions
from app.services.base import ValidationError, ConflictError, NotFoundError, ServiceError


@pytest.fixture
async def role_service():
    """角色服务实例"""
    service = RoleService()
    yield service


class TestRoleServiceCreation:
    """测试角色创建功能"""

    async def test_create_role_success(self, role_service):
        """测试成功创建角色"""
        # 准备测试数据
        role_name = "test_role"
        display_name = "测试角色"
        description = "这是一个测试角色"
        permissions = [Permission.USER_READ.value, Permission.PROMPT_READ.value]

        # 执行测试
        result = await role_service.create_role(
            name=role_name,
            display_name=display_name,
            description=description,
            permissions=permissions
        )

        # 验证结果
        assert result is not None
        assert result["name"] == role_name
        assert result["display_name"] == display_name
        assert result["description"] == description
        assert set(result["permissions"]) == set(permissions)
        assert result["is_system"] is False

        # 验证角色已存储
        stored_role = await role_service.get_role(role_name)
        assert stored_role is not None
        assert stored_role["name"] == role_name

    async def test_create_role_with_inheritance(self, role_service):
        """测试创建带继承的角色"""
        # 创建父角色
        parent_role = "parent_role"
        await role_service.create_role(
            name=parent_role,
            display_name="父角色",
            description="父角色描述",
            permissions=[Permission.USER_READ.value]
        )

        # 创建子角色，继承父角色
        child_role = "child_role"
        result = await role_service.create_role(
            name=child_role,
            display_name="子角色",
            description="子角色描述",
            permissions=[Permission.PROMPT_READ.value],
            inherit_from=[parent_role]
        )

        # 验证子角色包含了父角色的权限
        assert result is not None
        assert Permission.USER_READ.value in result["permissions"]
        assert Permission.PROMPT_READ.value in result["permissions"]

    async def test_create_role_invalid_name(self, role_service):
        """测试创建角色时名称无效"""
        # 空名称
        with pytest.raises(ValidationError):
            await role_service.create_role(
                name="",
                display_name="测试",
                description="描述",
                permissions=[]
            )

        # 包含无效字符的名称
        with pytest.raises(ValidationError):
            await role_service.create_role(
                name="invalid@role#name",
                display_name="测试",
                description="描述",
                permissions=[]
            )

    async def test_create_role_already_exists(self, role_service):
        """测试创建已存在的角色"""
        role_name = "duplicate_role"

        # 第一次创建成功
        await role_service.create_role(
            name=role_name,
            display_name="测试角色",
            description="描述",
            permissions=[]
        )

        # 第二次创建应该失败
        with pytest.raises(ConflictError):
            await role_service.create_role(
                name=role_name,
                display_name="另一个测试角色",
                description="另一个描述",
                permissions=[]
            )

    async def test_create_role_invalid_permission(self, role_service):
        """测试创建角色时权限无效"""
        with pytest.raises(ValidationError):
            await role_service.create_role(
                name="test_role",
                display_name="测试角色",
                description="描述",
                permissions=["invalid_permission"]
            )

    async def test_create_role_nonexistent_parent(self, role_service):
        """测试创建角色时父角色不存在"""
        with pytest.raises(ValidationError):
            await role_service.create_role(
                name="test_role",
                display_name="测试角色",
                description="描述",
                permissions=[],
                inherit_from=["nonexistent_parent"]
            )


class TestRoleServiceRetrieval:
    """测试角色获取功能"""

    async def test_get_role_success(self, role_service):
        """测试成功获取角色"""
        # 测试获取系统内置角色
        result = await role_service.get_role("admin")

        assert result is not None
        assert result["name"] == "admin"
        assert result["display_name"] == "系统管理员"
        assert result["is_system"] is True
        assert len(result["permissions"]) > 0

    async def test_get_role_not_found(self, role_service):
        """测试获取不存在的角色"""
        result = await role_service.get_role("nonexistent_role")
        assert result is None

    async def test_get_role_caching(self, role_service):
        """测试角色获取的缓存功能"""
        # 第一次获取
        result1 = await role_service.get_role("user")
        assert result1 is not None

        # 第二次获取应该使用缓存
        with patch.object(role_service, 'cache_get') as mock_cache_get:
            mock_cache_get.return_value = result1
            result2 = await role_service.get_role("user")
            assert result2 == result1


class TestRoleServiceUpdate:
    """测试角色更新功能"""

    async def test_update_role_success(self, role_service):
        """测试成功更新角色"""
        # 先创建一个角色
        role_name = "updatable_role"
        await role_service.create_role(
            name=role_name,
            display_name="原始名称",
            description="原始描述",
            permissions=[Permission.USER_READ.value]
        )

        # 更新角色
        new_display_name = "更新后的名称"
        new_description = "更新后的描述"
        new_permissions = [Permission.USER_READ.value, Permission.PROMPT_READ.value]

        result = await role_service.update_role(
            role_name=role_name,
            display_name=new_display_name,
            description=new_description,
            permissions=new_permissions
        )

        # 验证更新结果
        assert result is not None
        assert result["display_name"] == new_display_name
        assert result["description"] == new_description
        assert set(result["permissions"]) == set(new_permissions)

    async def test_update_role_not_found(self, role_service):
        """测试更新不存在的角色"""
        with pytest.raises(NotFoundError):
            await role_service.update_role(
                role_name="nonexistent_role",
                display_name="新名称"
            )

    async def test_update_system_role(self, role_service):
        """测试更新系统内置角色"""
        with pytest.raises(ServiceError):
            await role_service.update_role(
                role_name="admin",
                display_name="新的管理员名称"
            )

    async def test_update_role_invalid_permission(self, role_service):
        """测试更新角色时提供无效权限"""
        # 先创建一个角色
        role_name = "test_role"
        await role_service.create_role(
            name=role_name,
            display_name="测试角色",
            description="描述",
            permissions=[]
        )

        # 尝试更新为无效权限
        with pytest.raises(ValidationError):
            await role_service.update_role(
                role_name=role_name,
                permissions=["invalid_permission"]
            )


class TestRoleServiceDeletion:
    """测试角色删除功能"""

    async def test_delete_role_success(self, role_service):
        """测试成功删除角色"""
        # 先创建一个角色
        role_name = "deletable_role"
        await role_service.create_role(
            name=role_name,
            display_name="可删除角色",
            description="描述",
            permissions=[]
        )

        # 验证角色存在
        role = await role_service.get_role(role_name)
        assert role is not None

        # 删除角色
        result = await role_service.delete_role(role_name)
        assert result is True

        # 验证角色已删除
        role = await role_service.get_role(role_name)
        assert role is None

    async def test_delete_role_not_found(self, role_service):
        """测试删除不存在的角色"""
        with pytest.raises(NotFoundError):
            await role_service.delete_role("nonexistent_role")

    async def test_delete_system_role(self, role_service):
        """测试删除系统内置角色"""
        with pytest.raises(ServiceError):
            await role_service.delete_role("admin")


class TestRoleServiceList:
    """测试角色列表功能"""

    async def test_list_roles_all(self, role_service):
        """测试获取所有角色列表"""
        result = await role_service.list_roles(include_system=True)

        assert isinstance(result, list)
        assert len(result) >= 3  # 至少包含admin, user, viewer三个系统角色

        # 验证系统角色存在
        role_names = [role["name"] for role in result]
        assert "admin" in role_names
        assert "user" in role_names
        assert "viewer" in role_names

    async def test_list_roles_exclude_system(self, role_service):
        """测试获取角色列表（不包含系统角色）"""
        # 先创建一个自定义角色
        await role_service.create_role(
            name="custom_role",
            display_name="自定义角色",
            description="描述",
            permissions=[]
        )

        result = await role_service.list_roles(include_system=False)

        assert isinstance(result, list)
        # 验证不包含系统角色
        role_names = [role["name"] for role in result]
        assert "admin" not in role_names
        assert "user" not in role_names
        assert "viewer" not in role_names
        assert "custom_role" in role_names


class TestRoleServicePermissionCheck:
    """测试权限检查功能"""

    async def test_check_permission_success(self, role_service):
        """测试权限检查成功"""
        # 检查管理员角色的权限
        result = await role_service.check_permission("admin", Permission.USER_CREATE.value)
        assert result is True

        # 检查普通用户角色的权限
        result = await role_service.check_permission("user", Permission.PROMPT_READ.value)
        assert result is True

        # 检查访客角色没有的权限
        result = await role_service.check_permission("viewer", Permission.USER_CREATE.value)
        assert result is False

    async def test_check_permission_nonexistent_role(self, role_service):
        """测试检查不存在角色的权限"""
        result = await role_service.check_permission("nonexistent_role", Permission.USER_READ.value)
        assert result is False

    async def test_check_permission_invalid_permission(self, role_service):
        """测试检查无效权限"""
        result = await role_service.check_permission("admin", "invalid_permission")
        assert result is False

    async def test_check_permission_with_inheritance(self, role_service):
        """测试带继承的权限检查"""
        # 普通用户角色应该继承访客权限
        result = await role_service.check_permission("user", Permission.TEMPLATE_READ.value)
        assert result is True  # 用户应该有模板读取权限


class TestRoleServiceUserPermissions:
    """测试用户权限功能"""

    async def test_get_user_permissions_single_role(self, role_service):
        """测试获取单一角色用户的权限"""
        permissions = await role_service.get_user_permissions(["viewer"])

        assert isinstance(permissions, set)
        assert len(permissions) > 0
        assert Permission.USER_READ.value in permissions
        assert Permission.PROMPT_READ.value in permissions

    async def test_get_user_permissions_multiple_roles(self, role_service):
        """测试获取多角色用户的权限"""
        permissions = await role_service.get_user_permissions(["user", "viewer"])

        assert isinstance(permissions, set)
        assert len(permissions) > 0

        # 应该包含两个角色的所有权限
        user_specific_permissions = {Permission.PROMPT_CREATE.value, Permission.TEMPLATE_CREATE.value}
        viewer_permissions = {Permission.USER_READ.value, Permission.PROMPT_READ.value}

        assert user_specific_permissions.issubset(permissions)
        assert viewer_permissions.issubset(permissions)

    async def test_get_user_permissions_nonexistent_role(self, role_service):
        """测试获取不存在角色用户的权限"""
        permissions = await role_service.get_user_permissions(["nonexistent_role"])

        assert isinstance(permissions, set)
        assert len(permissions) == 0


class TestRoleServiceValidation:
    """测试角色验证功能"""

    async def test_validate_role_assignment_admin(self, role_service):
        """测试管理员角色分配验证"""
        # 管理员可以分配任何角色
        assert await role_service.validate_role_assignment("admin", "user") is True
        assert await role_service.validate_role_assignment("admin", "admin") is True
        assert await role_service.validate_role_assignment("admin", "viewer") is True

    async def test_validate_role_assignment_user(self, role_service):
        """测试普通用户角色分配验证"""
        # 普通用户不能分配管理员角色
        assert await role_service.validate_role_assignment("user", "admin") is False

        # 普通用户可以分配同级或更低级角色
        assert await role_service.validate_role_assignment("user", "user") is True
        assert await role_service.validate_role_assignment("user", "viewer") is True

    async def test_validate_role_assignment_viewer(self, role_service):
        """测试访客角色分配验证"""
        # 访客不能分配管理员或用户角色
        assert await role_service.validate_role_assignment("viewer", "admin") is False
        assert await role_service.validate_role_assignment("viewer", "user") is False

        # 访客可以分配同级角色
        assert await role_service.validate_role_assignment("viewer", "viewer") is True


class TestRoleServiceStatistics:
    """测试角色统计功能"""

    async def test_get_role_statistics(self, role_service):
        """测试获取角色统计信息"""
        # 先创建一个自定义角色
        await role_service.create_role(
            name="custom_role",
            display_name="自定义角色",
            description="描述",
            permissions=[Permission.USER_READ.value, Permission.PROMPT_READ.value]
        )

        result = await role_service.get_role_statistics()

        assert isinstance(result, dict)
        assert "total_roles" in result
        assert "system_roles" in result
        assert "custom_roles" in result
        assert "total_permissions" in result
        assert "permission_usage" in result
        assert "most_used_permissions" in result

        # 验证统计数据
        assert result["total_roles"] >= 4  # 至少3个系统角色 + 1个自定义角色
        assert result["system_roles"] == 3  # admin, user, viewer
        assert result["custom_roles"] >= 1
        assert result["total_permissions"] == len(Permission)


class TestRoleServiceHealthCheck:
    """测试角色服务健康检查"""

    async def test_health_check_healthy(self, role_service):
        """测试健康状态检查 - 健康"""
        # 模拟缓存健康
        with patch.object(role_service, 'cache') as mock_cache_prop:
            mock_cache = AsyncMock()
            mock_cache_prop.return_value = mock_cache

            result = await role_service.health_check()

            assert result["status"] == "healthy"
            assert result["total_roles"] >= 3
            assert result["system_roles"] == 3

    async def test_health_check_missing_system_role(self, role_service):
        """测试健康状态检查 - 系统角色缺失"""
        # 删除一个系统角色（模拟异常情况）
        original_roles = role_service._roles.copy()
        del role_service._roles["admin"]

        try:
            result = await role_service.health_check()
            assert result["status"] == "unhealthy"
            assert "error" in result
        finally:
            # 恢复原始状态
            role_service._roles = original_roles


class TestRoleServiceSingleton:
    """测试角色服务单例模式"""

    def test_get_role_service_singleton(self):
        """测试获取角色服务实例是单例"""
        service1 = get_role_service()
        service2 = get_role_service()

        assert service1 is service2
        assert isinstance(service1, RoleService)


class TestRoleClass:
    """测试Role类"""

    def test_role_creation(self):
        """测试Role类创建"""
        permissions = {Permission.USER_READ, Permission.PROMPT_READ}
        role = Role(
            name="test_role",
            display_name="测试角色",
            description="测试描述",
            permissions=permissions
        )

        assert role.name == "test_role"
        assert role.display_name == "测试角色"
        assert role.description == "测试描述"
        assert role.permissions == permissions
        assert role.is_system is False

    def test_role_has_permission(self):
        """测试角色权限检查"""
        permissions = {Permission.USER_READ, Permission.PROMPT_READ}
        role = Role("test", "测试", "描述", permissions)

        assert role.has_permission(Permission.USER_READ) is True
        assert role.has_permission(Permission.PROMPT_READ) is True
        assert role.has_permission(Permission.USER_CREATE) is False

    def test_role_add_permission(self):
        """测试添加权限"""
        permissions = {Permission.USER_READ}
        role = Role("test", "测试", "描述", permissions)

        role.add_permission(Permission.PROMPT_READ)
        assert Permission.PROMPT_READ in role.permissions

    def test_role_add_permission_system_role(self):
        """测试系统角色不能添加权限"""
        permissions = {Permission.USER_READ}
        role = Role("test", "测试", "描述", permissions)
        role.is_system = True

        with pytest.raises(ServiceError):
            role.add_permission(Permission.PROMPT_READ)

    def test_role_remove_permission(self):
        """测试移除权限"""
        permissions = {Permission.USER_READ, Permission.PROMPT_READ}
        role = Role("test", "测试", "描述", permissions)

        role.remove_permission(Permission.PROMPT_READ)
        assert Permission.PROMPT_READ not in role.permissions

    def test_role_remove_permission_system_role(self):
        """测试系统角色不能移除权限"""
        permissions = {Permission.USER_READ, Permission.PROMPT_READ}
        role = Role("test", "测试", "描述", permissions)
        role.is_system = True

        with pytest.raises(ServiceError):
            role.remove_permission(Permission.PROMPT_READ)

    def test_role_to_dict(self):
        """测试角色转为字典"""
        permissions = {Permission.USER_READ, Permission.PROMPT_READ}
        role = Role("test", "测试", "描述", permissions)

        result = role.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["display_name"] == "测试"
        assert result["description"] == "描述"
        assert set(result["permissions"]) == {p.value for p in permissions}
        assert result["is_system"] is False


class TestPermissionHelperFunctions:
    """测试权限辅助函数"""

    async def test_has_permission_function(self):
        """测试has_permission函数"""
        # 管理员角色应该有所有权限
        result = await has_permission(["admin"], Permission.USER_CREATE.value)
        assert result is True

        # 访客角色应该没有创建用户权限
        result = await has_permission(["viewer"], Permission.USER_CREATE.value)
        assert result is False

        # 多角色权限检查
        result = await has_permission(["user", "viewer"], Permission.PROMPT_CREATE.value)
        assert result is True

    async def test_get_user_all_permissions_function(self):
        """测试get_user_all_permissions函数"""
        # 获取管理员的所有权限
        permissions = await get_user_all_permissions(["admin"])
        assert isinstance(permissions, set)
        assert len(permissions) == len(Permission)  # 管理员应该有所有权限

        # 获取访客的权限
        permissions = await get_user_all_permissions(["viewer"])
        assert isinstance(permissions, set)
        assert len(permissions) > 0
        assert Permission.USER_READ.value in permissions

        # 获取多角色的权限
        permissions = await get_user_all_permissions(["user", "viewer"])
        assert isinstance(permissions, set)
        assert Permission.USER_READ.value in permissions
        assert Permission.PROMPT_CREATE.value in permissions