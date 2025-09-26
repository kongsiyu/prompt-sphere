"""用户管理服务

提供用户账户管理、配置文件管理、DingTalk用户同步等功能
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from app.auth.dingtalk import DingTalkClient, DingTalkError
from app.auth.exceptions import AuthenticationError, UserNotFoundError
from app.core.config import get_settings
from database.models.user import User
from database.repositories.user_repository import UserRepository
from database.session import get_session

from .base import BaseService, ConflictError, NotFoundError, ServiceError, ValidationError

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """用户管理服务类

    功能包括：
    - 用户CRUD操作
    - 用户配置文件管理
    - DingTalk用户数据同步
    - 用户偏好设置管理
    - 用户活动跟踪
    """

    def __init__(self):
        super().__init__(
            cache_namespace="user",
            enable_caching=True,
            default_cache_ttl=3600
        )
        self.settings = get_settings()
        self._dingtalk_client: Optional[DingTalkClient] = None

    @property
    async def dingtalk_client(self) -> Optional[DingTalkClient]:
        """获取DingTalk客户端实例"""
        if not self._dingtalk_client and hasattr(self.settings, 'dingtalk_app_key'):
            self._dingtalk_client = DingTalkClient(
                app_key=self.settings.dingtalk_app_key,
                app_secret=self.settings.dingtalk_app_secret
            )
        return self._dingtalk_client

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "user",
        dingtalk_userid: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        **additional_data
    ) -> Dict[str, Any]:
        """创建新用户

        Args:
            email: 用户邮箱
            password: 用户密码
            full_name: 用户全名
            role: 用户角色 (admin, user, viewer)
            dingtalk_userid: 钉钉用户ID
            preferences: 用户偏好设置
            **additional_data: 其他用户数据

        Returns:
            创建的用户信息字典

        Raises:
            ValidationError: 输入数据无效
            ConflictError: 用户已存在
            ServiceError: 创建失败
        """
        try:
            await self.log_operation("create_user", {"email": email, "role": role})

            # 验证输入数据
            validation_rules = {
                "email": {"required": True, "type": str, "min_length": 5, "max_length": 255},
                "password": {"required": True, "type": str, "min_length": 8, "max_length": 128},
                "full_name": {"required": True, "type": str, "min_length": 1, "max_length": 100},
                "role": {"required": True, "type": str}
            }

            data = {
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role
            }

            validated_data = await self.validate_input(data, validation_rules)

            # 验证邮箱格式
            if "@" not in validated_data["email"] or "." not in validated_data["email"]:
                raise ValidationError("Invalid email format")

            # 验证角色
            valid_roles = ["admin", "user", "viewer"]
            if validated_data["role"] not in valid_roles:
                raise ValidationError(f"Role must be one of: {', '.join(valid_roles)}")

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)

                # 检查用户是否已存在
                existing_user = await user_repo.find_by_email(validated_data["email"])
                if existing_user:
                    raise ConflictError(f"User with email {validated_data['email']} already exists")

                # 创建用户
                user = await user_repo.create_user(
                    email=validated_data["email"],
                    password=validated_data["password"],
                    full_name=validated_data["full_name"],
                    role=validated_data["role"],
                    **additional_data
                )

                # 设置用户偏好
                if preferences:
                    for key, value in preferences.items():
                        user.update_preference(key, value)

                # 如果提供了DingTalk用户ID，尝试同步用户数据
                if dingtalk_userid:
                    try:
                        await self._sync_dingtalk_user_data(user, dingtalk_userid)
                    except Exception as e:
                        self.logger.warning(f"Failed to sync DingTalk data for user {user.email}: {e}")

                await session.session.flush()
                await session.session.refresh(user)

                # 清除相关缓存
                await self.cache_delete(f"user_stats")

                result = user.to_dict(include_sensitive=False)

                await self.log_operation(
                    "user_created",
                    {"user_id": user.id, "email": user.email, "role": user.role}
                )

                return result

        except (ValidationError, ConflictError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "create_user", {"email": email})
            raise error

    async def get_user(self, user_id: str, include_sensitive: bool = False) -> Optional[Dict[str, Any]]:
        """获取用户信息

        Args:
            user_id: 用户ID
            include_sensitive: 是否包含敏感信息

        Returns:
            用户信息字典或None
        """
        try:
            cache_key = f"user:{user_id}"

            # 尝试从缓存获取
            cached_user = await self.cache_get(cache_key)
            if cached_user and not include_sensitive:
                return cached_user

            async with self.with_session() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.get_by_id(user_id)

                if not user:
                    return None

                result = user.to_dict(include_sensitive=include_sensitive)

                # 缓存结果（不包含敏感信息）
                if not include_sensitive:
                    await self.cache_set(cache_key, result)

                return result

        except Exception as e:
            error = await self.handle_error(e, "get_user", {"user_id": user_id})
            raise error

    async def get_user_by_email(self, email: str, include_sensitive: bool = False) -> Optional[Dict[str, Any]]:
        """通过邮箱获取用户信息

        Args:
            email: 用户邮箱
            include_sensitive: 是否包含敏感信息

        Returns:
            用户信息字典或None
        """
        try:
            cache_key = f"user:email:{email.lower()}"

            # 尝试从缓存获取
            cached_user = await self.cache_get(cache_key)
            if cached_user and not include_sensitive:
                return cached_user

            async with self.with_session() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.find_by_email(email)

                if not user:
                    return None

                result = user.to_dict(include_sensitive=include_sensitive)

                # 缓存结果（不包含敏感信息）
                if not include_sensitive:
                    await self.cache_set(cache_key, result)

                return result

        except Exception as e:
            error = await self.handle_error(e, "get_user_by_email", {"email": email})
            raise error

    async def update_user(self, user_id: str, **update_data) -> Optional[Dict[str, Any]]:
        """更新用户信息

        Args:
            user_id: 用户ID
            **update_data: 要更新的数据

        Returns:
            更新后的用户信息字典或None

        Raises:
            NotFoundError: 用户不存在
            ValidationError: 更新数据无效
            ServiceError: 更新失败
        """
        try:
            await self.log_operation("update_user", {"user_id": user_id})

            # 定义可更新的字段
            allowed_fields = {
                "full_name", "role", "is_active", "email_verified"
            }

            # 过滤允许更新的字段
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if not filtered_data:
                raise ValidationError("No valid fields to update")

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.get_by_id(user_id)

                if not user:
                    raise NotFoundError("user", user_id)

                # 验证角色
                if "role" in filtered_data:
                    valid_roles = ["admin", "user", "viewer"]
                    if filtered_data["role"] not in valid_roles:
                        raise ValidationError(f"Role must be one of: {', '.join(valid_roles)}")

                # 验证全名
                if "full_name" in filtered_data:
                    if not filtered_data["full_name"] or len(filtered_data["full_name"]) > 100:
                        raise ValidationError("Full name must be 1-100 characters")

                # 更新字段
                for field, value in filtered_data.items():
                    setattr(user, field, value)

                await session.session.flush()
                await session.session.refresh(user)

                # 清除相关缓存
                await self.cache_delete(
                    f"user:{user_id}",
                    f"user:email:{user.email.lower()}"
                )

                result = user.to_dict(include_sensitive=False)

                await self.log_operation(
                    "user_updated",
                    {"user_id": user_id, "updated_fields": list(filtered_data.keys())}
                )

                return result

        except (NotFoundError, ValidationError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "update_user", {"user_id": user_id})
            raise error

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新用户偏好设置

        Args:
            user_id: 用户ID
            preferences: 偏好设置字典

        Returns:
            更新后的用户信息字典或None
        """
        try:
            await self.log_operation("update_user_preferences", {"user_id": user_id})

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)
                success = await user_repo.update_preferences(user_id, preferences)

                if not success:
                    raise NotFoundError("user", user_id)

                # 获取更新后的用户信息
                user = await user_repo.get_by_id(user_id)
                result = user.to_dict(include_sensitive=False)

                # 清除相关缓存
                await self.cache_delete(
                    f"user:{user_id}",
                    f"user:email:{user.email.lower()}"
                )

                await self.log_operation(
                    "user_preferences_updated",
                    {"user_id": user_id, "preference_keys": list(preferences.keys())}
                )

                return result

        except NotFoundError as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "update_user_preferences", {"user_id": user_id})
            raise error

    async def change_password(self, user_id: str, new_password: str) -> bool:
        """修改用户密码

        Args:
            user_id: 用户ID
            new_password: 新密码

        Returns:
            是否修改成功

        Raises:
            NotFoundError: 用户不存在
            ValidationError: 密码无效
            ServiceError: 修改失败
        """
        try:
            await self.log_operation("change_password", {"user_id": user_id})

            # 验证密码长度
            if not new_password or len(new_password) < 8 or len(new_password) > 128:
                raise ValidationError("Password must be 8-128 characters long")

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)
                success = await user_repo.update_password(user_id, new_password)

                if not success:
                    raise NotFoundError("user", user_id)

                await self.log_operation(
                    "password_changed",
                    {"user_id": user_id}
                )

                return True

        except (NotFoundError, ValidationError) as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "change_password", {"user_id": user_id})
            raise error

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户身份

        Args:
            email: 用户邮箱
            password: 密码

        Returns:
            验证成功的用户信息字典或None
        """
        try:
            await self.log_operation("authenticate_user", {"email": email})

            async with self.with_session() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.authenticate(email, password)

                if not user:
                    return None

                # 更新最后登录时间
                await user_repo.update_last_login(user.id)

                result = user.to_dict(include_sensitive=False)

                await self.log_operation(
                    "user_authenticated",
                    {"user_id": user.id, "email": email}
                )

                return result

        except Exception as e:
            error = await self.handle_error(e, "authenticate_user", {"email": email})
            raise error

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        role: Optional[str] = None,
        active_only: bool = True,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户列表

        Args:
            limit: 返回数量限制
            offset: 偏移量
            role: 按角色过滤
            active_only: 仅返回活跃用户
            search_term: 搜索词（邮箱或姓名）

        Returns:
            包含用户列表和总数的字典
        """
        try:
            await self.log_operation("list_users", {"limit": limit, "offset": offset})

            async with self.with_session() as session:
                user_repo = UserRepository(session.session)

                if search_term:
                    # 搜索用户
                    users = await user_repo.search_users(
                        search_term,
                        include_inactive=not active_only,
                        limit=limit
                    )
                    total_users = len(users)  # 简化计数
                elif role:
                    # 按角色获取用户
                    all_users = await user_repo.get_users_by_role(role)
                    users = all_users[offset:offset + limit] if offset or limit < len(all_users) else all_users
                    total_users = len(all_users)
                else:
                    # 获取活跃用户
                    users = await user_repo.get_active_users(
                        limit=limit,
                        offset=offset,
                        order_by="created_at",
                        order_desc=True
                    )
                    # 获取总数统计
                    stats = await user_repo.get_user_statistics()
                    total_users = stats["active_users"] if active_only else stats["total_users"]

                # 转换为字典格式
                user_list = [user.to_dict(include_sensitive=False) for user in users]

                return {
                    "users": user_list,
                    "total": total_users,
                    "limit": limit,
                    "offset": offset
                }

        except Exception as e:
            error = await self.handle_error(e, "list_users", {"limit": limit, "offset": offset})
            raise error

    async def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息

        Returns:
            用户统计信息字典
        """
        try:
            cache_key = "user_stats"

            # 尝试从缓存获取
            cached_stats = await self.cache_get(cache_key)
            if cached_stats:
                return cached_stats

            async with self.with_session() as session:
                user_repo = UserRepository(session.session)
                stats = await user_repo.get_user_statistics()

                # 缓存统计信息（较短的TTL）
                await self.cache_set(cache_key, stats, ttl=300)  # 5分钟

                await self.log_operation("get_user_statistics")

                return stats

        except Exception as e:
            error = await self.handle_error(e, "get_user_statistics")
            raise error

    async def sync_dingtalk_user(self, user_id: str, dingtalk_userid: str) -> Dict[str, Any]:
        """同步DingTalk用户数据

        Args:
            user_id: 用户ID
            dingtalk_userid: DingTalk用户ID

        Returns:
            同步后的用户信息字典

        Raises:
            NotFoundError: 用户不存在
            ServiceError: 同步失败
        """
        try:
            await self.log_operation("sync_dingtalk_user", {"user_id": user_id})

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.get_by_id(user_id)

                if not user:
                    raise NotFoundError("user", user_id)

                # 同步DingTalk用户数据
                await self._sync_dingtalk_user_data(user, dingtalk_userid)

                await session.session.flush()
                await session.session.refresh(user)

                # 清除相关缓存
                await self.cache_delete(
                    f"user:{user_id}",
                    f"user:email:{user.email.lower()}"
                )

                result = user.to_dict(include_sensitive=False)

                await self.log_operation(
                    "dingtalk_user_synced",
                    {"user_id": user_id, "dingtalk_userid": dingtalk_userid}
                )

                return result

        except NotFoundError as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "sync_dingtalk_user", {"user_id": user_id})
            raise error

    async def _sync_dingtalk_user_data(self, user: User, dingtalk_userid: str) -> None:
        """内部方法：同步DingTalk用户数据

        Args:
            user: 用户实例
            dingtalk_userid: DingTalk用户ID

        Raises:
            ServiceError: 同步失败
        """
        try:
            dingtalk_client = await self.dingtalk_client
            if not dingtalk_client:
                self.logger.warning("DingTalk client not configured, skipping user sync")
                return

            # 获取DingTalk用户信息
            user_info = await dingtalk_client.get_user_info(dingtalk_userid)

            # 更新用户信息
            if user_info.get("name") and not user.full_name:
                user.full_name = user_info["name"]

            if user_info.get("avatar"):
                user.update_preference("avatar_url", user_info["avatar"])

            if user_info.get("mobile"):
                user.update_preference("mobile", user_info["mobile"])

            if user_info.get("job_number"):
                user.update_preference("job_number", user_info["job_number"])

            if user_info.get("title"):
                user.update_preference("job_title", user_info["title"])

            # 存储DingTalk用户ID
            user.update_preference("dingtalk_userid", dingtalk_userid)

            self.logger.info(f"Synced DingTalk data for user {user.email}")

        except DingTalkError as e:
            self.logger.error(f"DingTalk API error when syncing user {user.email}: {e}")
            raise ServiceError(f"Failed to sync DingTalk user data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error syncing DingTalk user {user.email}: {e}")
            raise ServiceError(f"Unexpected error in DingTalk sync: {str(e)}")

    async def delete_user(self, user_id: str, soft_delete: bool = True) -> bool:
        """删除用户（软删除或硬删除）

        Args:
            user_id: 用户ID
            soft_delete: 是否软删除

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 用户不存在
            ServiceError: 删除失败
        """
        try:
            await self.log_operation("delete_user", {"user_id": user_id, "soft_delete": soft_delete})

            async with self.with_transaction() as session:
                user_repo = UserRepository(session.session)
                user = await user_repo.get_by_id(user_id)

                if not user:
                    raise NotFoundError("user", user_id)

                if soft_delete:
                    # 软删除：设置删除时间和停用账户
                    user.deleted_at = datetime.now(timezone.utc)
                    user.is_active = False
                else:
                    # 硬删除：从数据库中删除
                    await session.session.delete(user)

                await session.session.flush()

                # 清除相关缓存
                await self.cache_delete(
                    f"user:{user_id}",
                    f"user:email:{user.email.lower()}",
                    "user_stats"
                )

                await self.log_operation(
                    "user_deleted",
                    {"user_id": user_id, "email": user.email, "soft_delete": soft_delete}
                )

                return True

        except NotFoundError as e:
            raise e
        except Exception as e:
            error = await self.handle_error(e, "delete_user", {"user_id": user_id})
            raise error

    async def track_user_activity(
        self,
        user_id: str,
        activity_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """跟踪用户活动

        Args:
            user_id: 用户ID
            activity_type: 活动类型
            details: 活动详情

        Returns:
            是否记录成功
        """
        try:
            # 存储在Redis中以便后续批量处理
            redis = await self.redis
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_id": str(uuid4())
            }

            activity_key = f"user_activity:{user_id}:{activity_data['activity_id']}"
            await redis.set(activity_key, json.dumps(activity_data), ex=3600 * 24 * 7)  # 保存7天

            # 更新用户活动计数
            daily_key = f"user_activity_count:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
            await redis.incr(daily_key)
            await redis.expire(daily_key, 3600 * 24 * 30)  # 保存30天

            await self.log_operation(
                "user_activity_tracked",
                {"user_id": user_id, "activity_type": activity_type},
                level="debug"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to track user activity: {e}")
            return False

    async def get_user_activity_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取用户活动摘要

        Args:
            user_id: 用户ID
            days: 统计天数

        Returns:
            用户活动摘要字典
        """
        try:
            redis = await self.redis
            activity_counts = {}

            # 获取最近N天的活动计数
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_key = f"user_activity_count:{user_id}:{date}"
                count = await redis.get(daily_key)
                activity_counts[date] = int(count.decode()) if count else 0

            total_activities = sum(activity_counts.values())

            return {
                "user_id": user_id,
                "period_days": days,
                "total_activities": total_activities,
                "daily_counts": activity_counts,
                "average_daily": total_activities / days if days > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get user activity summary: {e}")
            return {
                "user_id": user_id,
                "period_days": days,
                "total_activities": 0,
                "daily_counts": {},
                "average_daily": 0,
                "error": str(e)
            }

    async def health_check(self) -> Dict[str, Any]:
        """用户服务健康检查"""
        health_info = {
            "service": self.service_name,
            "status": "unknown",
            "database_connection": False,
            "cache_connection": False,
            "dingtalk_connection": False,
            "user_count": 0,
            "error": None
        }

        try:
            # 测试数据库连接
            async with self.with_session() as session:
                user_repo = UserRepository(session.session)
                stats = await user_repo.get_user_statistics()
                health_info["database_connection"] = True
                health_info["user_count"] = stats.get("total_users", 0)

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

            # 测试DingTalk连接（如果配置了）
            dingtalk_client = await self.dingtalk_client
            if dingtalk_client:
                try:
                    await dingtalk_client.get_access_token()
                    health_info["dingtalk_connection"] = True
                except:
                    health_info["dingtalk_connection"] = False
            else:
                health_info["dingtalk_connection"] = "not_configured"

            health_info["status"] = "healthy"

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            self.logger.error(f"Health check failed for {self.service_name}: {e}")

        return health_info


# 全局用户服务实例
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """获取用户服务实例（单例模式）"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service