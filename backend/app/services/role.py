"""角色和权限管理服务

提供基于角色的访问控制（RBAC）功能
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.core.config import get_settings

from .base import BaseService, ConflictError, NotFoundError, ServiceError, ValidationError

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """系统权限枚举"""
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    USER_MANAGE_ROLES = "user:manage_roles"

    # 提示词管理权限
    PROMPT_CREATE = "prompt:create"
    PROMPT_READ = "prompt:read"
    PROMPT_UPDATE = "prompt:update"
    PROMPT_DELETE = "prompt:delete"
    PROMPT_LIST = "prompt:list"
    PROMPT_PUBLISH = "prompt:publish"

    # 模板管理权限
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_READ = "template:read"
    TEMPLATE_UPDATE = "template:update"
    TEMPLATE_DELETE = "template:delete"
    TEMPLATE_LIST = "template:list"
    TEMPLATE_SHARE = "template:share"

    # 对话管理权限
    CONVERSATION_CREATE = "conversation:create"
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_UPDATE = "conversation:update"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_LIST = "conversation:list"
    CONVERSATION_SHARE = "conversation:share"

    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_BACKUP = "system:backup"

    # API权限
    API_ACCESS = "api:access"
    API_ADMIN = "api:admin"

    # 统计和分析权限
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"


class Role:
    """角色类"""

    def __init__(self, name: str, display_name: str, description: str, permissions: Set[Permission]):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.permissions = permissions
        self.created_at = datetime.now(timezone.utc)
        self.is_system = False  # 是否为系统内置角色

    def has_permission(self, permission: Permission) -> bool:
        """检查角色是否有指定权限"""
        return permission in self.permissions

    def add_permission(self, permission: Permission) -> None:
        """添加权限"""
        if self.is_system:
            raise ServiceError("Cannot modify system role permissions")
        self.permissions.add(permission)

    def remove_permission(self, permission: Permission) -> None:
        """移除权限"""
        if self.is_system:
            raise ServiceError("Cannot modify system role permissions")
        self.permissions.discard(permission)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "is_system": self.is_system
        }


# 预定义系统角色
SYSTEM_ROLES = {
    "admin": Role(
        name="admin",
        display_name="系统管理员",
        description="拥有系统所有权限的超级管理员",
        permissions=set(Permission)  # 所有权限
    ),
    "user": Role(
        name="user",
        display_name="普通用户",
        description="具有基本功能权限的普通用户",
        permissions={
            # 基本用户权限
            Permission.USER_READ,
            # 提示词权限
            Permission.PROMPT_CREATE,
            Permission.PROMPT_READ,
            Permission.PROMPT_UPDATE,
            Permission.PROMPT_DELETE,
            Permission.PROMPT_LIST,
            # 模板权限
            Permission.TEMPLATE_CREATE,
            Permission.TEMPLATE_READ,
            Permission.TEMPLATE_UPDATE,
            Permission.TEMPLATE_DELETE,
            Permission.TEMPLATE_LIST,
            Permission.TEMPLATE_SHARE,
            # 对话权限
            Permission.CONVERSATION_CREATE,
            Permission.CONVERSATION_READ,
            Permission.CONVERSATION_UPDATE,
            Permission.CONVERSATION_DELETE,
            Permission.CONVERSATION_LIST,
            Permission.CONVERSATION_SHARE,
            # API权限
            Permission.API_ACCESS,
        }
    ),
    "viewer": Role(
        name="viewer",
        display_name="访客",
        description="只有查看权限的访客用户",
        permissions={
            # 只读权限
            Permission.USER_READ,
            Permission.PROMPT_READ,
            Permission.PROMPT_LIST,
            Permission.TEMPLATE_READ,
            Permission.TEMPLATE_LIST,
            Permission.CONVERSATION_READ,
            Permission.CONVERSATION_LIST,
            Permission.API_ACCESS,
        }
    )
}

# 标记为系统角色
for role in SYSTEM_ROLES.values():
    role.is_system = True


class RoleService(BaseService):
    """角色和权限管理服务类

    功能包括：
    - 角色的创建、更新、删除
    - 权限管理和验证
    - 用户角色分配和检查
    - 权限继承和层次结构
    """

    def __init__(self):
        super().__init__(
            cache_namespace="role",
            enable_caching=True,
            default_cache_ttl=7200  # 2小时缓存
        )
        self.settings = get_settings()

        # 初始化角色存储（在实际项目中应该使用数据库）
        self._roles: Dict[str, Role] = SYSTEM_ROLES.copy()

        # 角色层次结构定义（用于权限继承）
        self._role_hierarchy = {
            "admin": [],  # 管理员不继承其他角色
            "user": ["viewer"],  # 用户继承访客权限
            "viewer": []  # 访客不继承其他角色
        }

    async def create_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: List[str],
        inherit_from: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建新角色

        Args:
            name: 角色名称（唯一标识）
            display_name: 显示名称
            description: 角色描述
            permissions: 权限列表
            inherit_from: 继承的角色列表

        Returns:
            创建的角色信息字典

        Raises:
            ConflictError: 角色已存在
            ValidationError: 输入数据无效
            ServiceError: 创建失败
        """
        try:
            await self.log_operation("create_role", {"name": name, "display_name": display_name})

            # 验证输入数据
            validation_rules = {
                "name": {"required": True, "type": str, "min_length": 1, "max_length": 50},
                "display_name": {"required": True, "type": str, "min_length": 1, "max_length": 100},
                "description": {"required": True, "type": str, "min_length": 1, "max_length": 500}
            }

            data = {
                "name": name,
                "display_name": display_name,
                "description": description
            }

            validated_data = await self.validate_input(data, validation_rules)

            # 验证角色名称格式（只能包含字母、数字、下划线、连字符）
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', validated_data["name"]):
                raise ValidationError("角色名称只能包含字母、数字、下划线和连字符")

            # 检查角色是否已存在
            if validated_data["name"] in self._roles:
                raise ConflictError(f"角色 '{validated_data['name']}' 已存在")

            # 验证权限
            role_permissions = set()
            for perm_str in permissions:
                try:
                    permission = Permission(perm_str)
                    role_permissions.add(permission)
                except ValueError:
                    raise ValidationError(f"无效的权限: {perm_str}")

            # 处理权限继承
            if inherit_from:
                for parent_role_name in inherit_from:
                    if parent_role_name not in self._roles:
                        raise ValidationError(f"父角色不存在: {parent_role_name}")

                    parent_role = self._roles[parent_role_name]
                    role_permissions.update(parent_role.permissions)

            # 创建角色
            role = Role(
                name=validated_data["name"],
                display_name=validated_data["display_name"],
                description=validated_data["description"],
                permissions=role_permissions
            )

            # 存储角色
            self._roles[role.name] = role

            # 设置继承关系
            if inherit_from:
                self._role_hierarchy[role.name] = inherit_from
            else:
                self._role_hierarchy[role.name] = []

            # 清除相关缓存
            await self.cache_delete("role_list", f"role:{role.name}")

            result = role.to_dict()

            await self.log_operation(
                "role_created",
                {"role_name": role.name, "permission_count": len(role.permissions)}
            )

            return result

        except (ValidationError, ConflictError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "create_role", {"name": name})
            raise error

    async def get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        """获取角色信息

        Args:
            role_name: 角色名称

        Returns:
            角色信息字典或None
        """
        try:
            cache_key = f"role:{role_name}"

            # 尝试从缓存获取
            cached_role = await self.cache_get(cache_key)
            if cached_role:
                return cached_role

            # 从内存获取
            role = self._roles.get(role_name)
            if not role:
                return None

            result = role.to_dict()

            # 缓存结果
            await self.cache_set(cache_key, result)

            return result

        except Exception as e:
            error = await self.handle_error(e, "get_role", {"role_name": role_name})
            raise error

    async def update_role(
        self,
        role_name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新角色信息

        Args:
            role_name: 角色名称
            display_name: 新的显示名称
            description: 新的描述
            permissions: 新的权限列表

        Returns:
            更新后的角色信息字典或None

        Raises:
            NotFoundError: 角色不存在
            ServiceError: 不能修改系统角色
            ValidationError: 输入数据无效
        """
        try:
            await self.log_operation("update_role", {"role_name": role_name})

            role = self._roles.get(role_name)
            if not role:
                raise NotFoundError("role", role_name)

            if role.is_system:
                raise ServiceError("不能修改系统内置角色")

            # 更新显示名称
            if display_name is not None:
                if not display_name.strip():
                    raise ValidationError("显示名称不能为空")
                role.display_name = display_name.strip()

            # 更新描述
            if description is not None:
                if not description.strip():
                    raise ValidationError("描述不能为空")
                role.description = description.strip()

            # 更新权限
            if permissions is not None:
                new_permissions = set()
                for perm_str in permissions:
                    try:
                        permission = Permission(perm_str)
                        new_permissions.add(permission)
                    except ValueError:
                        raise ValidationError(f"无效的权限: {perm_str}")

                role.permissions = new_permissions

            # 清除相关缓存
            await self.cache_delete(f"role:{role_name}", "role_list")

            result = role.to_dict()

            await self.log_operation(
                "role_updated",
                {"role_name": role_name, "updated_fields": [
                    f for f in ["display_name", "description", "permissions"]
                    if locals()[f] is not None
                ]}
            )

            return result

        except (NotFoundError, ValidationError, ServiceError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "update_role", {"role_name": role_name})
            raise error

    async def delete_role(self, role_name: str) -> bool:
        """删除角色

        Args:
            role_name: 角色名称

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 角色不存在
            ServiceError: 不能删除系统角色
        """
        try:
            await self.log_operation("delete_role", {"role_name": role_name})

            role = self._roles.get(role_name)
            if not role:
                raise NotFoundError("role", role_name)

            if role.is_system:
                raise ServiceError("不能删除系统内置角色")

            # 删除角色
            del self._roles[role_name]

            # 删除继承关系
            if role_name in self._role_hierarchy:
                del self._role_hierarchy[role_name]

            # 从其他角色的继承列表中移除
            for parent_list in self._role_hierarchy.values():
                if role_name in parent_list:
                    parent_list.remove(role_name)

            # 清除相关缓存
            await self.cache_delete(f"role:{role_name}", "role_list")

            await self.log_operation(
                "role_deleted",
                {"role_name": role_name}
            )

            return True

        except (NotFoundError, ServiceError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "delete_role", {"role_name": role_name})
            raise error

    async def list_roles(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """获取所有角色列表

        Args:
            include_system: 是否包含系统内置角色

        Returns:
            角色信息列表
        """
        try:
            cache_key = f"role_list:system_{include_system}"

            # 尝试从缓存获取
            cached_roles = await self.cache_get(cache_key)
            if cached_roles:
                return cached_roles

            # 获取角色列表
            roles = []
            for role in self._roles.values():
                if not include_system and role.is_system:
                    continue
                roles.append(role.to_dict())

            # 按角色名称排序
            roles.sort(key=lambda x: x["name"])

            # 缓存结果
            await self.cache_set(cache_key, roles)

            return roles

        except Exception as e:
            error = await self.handle_error(e, "list_roles")
            raise error

    async def check_permission(self, role_name: str, permission: str) -> bool:
        """检查角色是否有指定权限

        Args:
            role_name: 角色名称
            permission: 权限字符串

        Returns:
            是否有权限
        """
        try:
            role = self._roles.get(role_name)
            if not role:
                return False

            # 验证权限格式
            try:
                perm_enum = Permission(permission)
            except ValueError:
                return False

            # 检查直接权限
            if role.has_permission(perm_enum):
                return True

            # 检查继承权限
            inherited_roles = self._role_hierarchy.get(role_name, [])
            for parent_role_name in inherited_roles:
                if await self.check_permission(parent_role_name, permission):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking permission {permission} for role {role_name}: {e}")
            return False

    async def get_user_permissions(self, roles: List[str]) -> Set[str]:
        """获取用户的所有权限（基于角色列表）

        Args:
            roles: 用户角色列表

        Returns:
            权限集合
        """
        try:
            all_permissions = set()

            for role_name in roles:
                role = self._roles.get(role_name)
                if role:
                    # 添加角色直接权限
                    all_permissions.update(p.value for p in role.permissions)

                    # 添加继承权限
                    inherited_roles = self._role_hierarchy.get(role_name, [])
                    for parent_role_name in inherited_roles:
                        parent_permissions = await self.get_user_permissions([parent_role_name])
                        all_permissions.update(parent_permissions)

            return all_permissions

        except Exception as e:
            error = await self.handle_error(e, "get_user_permissions", {"roles": roles})
            raise error

    async def validate_role_assignment(self, user_role: str, target_role: str) -> bool:
        """验证角色分配权限

        Args:
            user_role: 执行操作的用户角色
            target_role: 目标角色

        Returns:
            是否有权限分配该角色
        """
        try:
            # 管理员可以分配任何角色
            if user_role == "admin":
                return True

            # 用户不能分配管理员角色
            if target_role == "admin":
                return False

            # 用户只能分配低于或等于自己等级的角色
            role_levels = {
                "admin": 3,
                "user": 2,
                "viewer": 1
            }

            user_level = role_levels.get(user_role, 0)
            target_level = role_levels.get(target_role, 0)

            return user_level >= target_level

        except Exception as e:
            self.logger.error(f"Error validating role assignment: {e}")
            return False

    async def get_role_statistics(self) -> Dict[str, Any]:
        """获取角色统计信息

        Returns:
            角色统计信息字典
        """
        try:
            total_roles = len(self._roles)
            system_roles = sum(1 for role in self._roles.values() if role.is_system)
            custom_roles = total_roles - system_roles

            # 权限使用统计
            permission_usage = {}
            for permission in Permission:
                count = sum(
                    1 for role in self._roles.values()
                    if role.has_permission(permission)
                )
                permission_usage[permission.value] = count

            # 最常用的权限
            most_used_permissions = sorted(
                permission_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            return {
                "total_roles": total_roles,
                "system_roles": system_roles,
                "custom_roles": custom_roles,
                "total_permissions": len(Permission),
                "permission_usage": permission_usage,
                "most_used_permissions": most_used_permissions
            }

        except Exception as e:
            error = await self.handle_error(e, "get_role_statistics")
            raise error

    async def health_check(self) -> Dict[str, Any]:
        """角色服务健康检查"""
        health_info = {
            "service": self.service_name,
            "status": "unknown",
            "total_roles": 0,
            "system_roles": 0,
            "cache_connection": False,
            "error": None
        }

        try:
            # 检查角色存储
            health_info["total_roles"] = len(self._roles)
            health_info["system_roles"] = sum(1 for role in self._roles.values() if role.is_system)

            # 测试缓存连接
            if self.enable_caching:
                cache = await self.cache
                test_key = f"health_check:{self.service_name}"
                await cache.set(test_key, "test", ttl=10)
                await cache.get(test_key)
                await cache.delete(test_key)
                health_info["cache_connection"] = True
            else:
                health_info["cache_connection"] = "disabled"

            # 验证系统角色完整性
            for role_name in ["admin", "user", "viewer"]:
                if role_name not in self._roles:
                    raise ServiceError(f"系统角色 {role_name} 缺失")

            health_info["status"] = "healthy"

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            self.logger.error(f"Health check failed for {self.service_name}: {e}")

        return health_info


# 全局角色服务实例
_role_service: Optional[RoleService] = None


def get_role_service() -> RoleService:
    """获取角色服务实例（单例模式）"""
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service


# 权限装饰器工厂
def require_permission(permission: Permission):
    """权限验证装饰器

    Args:
        permission: 所需权限

    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 这里需要从请求上下文中获取用户角色信息
            # 在实际应用中，这通常通过FastAPI的依赖注入实现

            # 示例实现（需要根据实际情况调整）
            user_roles = kwargs.get('user_roles', [])
            if not user_roles:
                raise ServiceError("用户未认证")

            role_service = get_role_service()
            has_permission = False

            for role_name in user_roles:
                if await role_service.check_permission(role_name, permission.value):
                    has_permission = True
                    break

            if not has_permission:
                raise ServiceError(f"权限不足，需要权限: {permission.value}")

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# 便捷的权限检查函数
async def has_permission(user_roles: List[str], permission: str) -> bool:
    """检查用户是否有指定权限

    Args:
        user_roles: 用户角色列表
        permission: 权限字符串

    Returns:
        是否有权限
    """
    role_service = get_role_service()

    for role_name in user_roles:
        if await role_service.check_permission(role_name, permission):
            return True

    return False


async def get_user_all_permissions(user_roles: List[str]) -> Set[str]:
    """获取用户的所有权限

    Args:
        user_roles: 用户角色列表

    Returns:
        权限集合
    """
    role_service = get_role_service()
    return await role_service.get_user_permissions(user_roles)