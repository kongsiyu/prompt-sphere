"""应用层用户数据模型

提供API层使用的用户数据传输对象（DTO）和验证模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    theme: str = Field(default="light", description="界面主题")
    language: str = Field(default="zh-CN", description="界面语言")
    timezone: str = Field(default="Asia/Shanghai", description="时区设置")
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "push": False,
            "system": True
        },
        description="通知设置"
    )
    ai_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_model": "qwen-turbo",
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True
        },
        description="AI模型设置"
    )
    dashboard_layout: Dict[str, Any] = Field(
        default_factory=dict,
        description="仪表板布局设置"
    )

    @validator("theme")
    def validate_theme(cls, v):
        allowed_themes = ["light", "dark", "auto"]
        if v not in allowed_themes:
            raise ValueError(f"主题必须是以下之一: {', '.join(allowed_themes)}")
        return v

    @validator("language")
    def validate_language(cls, v):
        allowed_languages = ["zh-CN", "en-US", "ja-JP"]
        if v not in allowed_languages:
            raise ValueError(f"语言必须是以下之一: {', '.join(allowed_languages)}")
        return v


class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="用户密码")
    full_name: str = Field(..., min_length=1, max_length=100, description="用户全名")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    dingtalk_userid: Optional[str] = Field(None, max_length=100, description="钉钉用户ID")
    preferences: Optional[UserPreferences] = Field(None, description="用户偏好设置")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展元数据")

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一位数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一位字母")
        return v

    @validator("full_name")
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError("用户全名不能为空")
        return v.strip()


class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户全名")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    email_verified: Optional[bool] = Field(None, description="邮箱是否已验证")

    @validator("full_name")
    def validate_full_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("用户全名不能为空")
        return v.strip() if v else v


class UserPasswordChangeRequest(BaseModel):
    """用户密码修改请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("两次输入的密码不匹配")
        return v

    @validator("new_password")
    def validate_new_password(cls, v, values):
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("新密码不能与当前密码相同")
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一位数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一位字母")
        return v


class UserPreferencesUpdateRequest(BaseModel):
    """用户偏好更新请求模型"""
    theme: Optional[str] = Field(None, description="界面主题")
    language: Optional[str] = Field(None, description="界面语言")
    timezone: Optional[str] = Field(None, description="时区设置")
    notifications: Optional[Dict[str, bool]] = Field(None, description="通知设置")
    ai_settings: Optional[Dict[str, Any]] = Field(None, description="AI模型设置")
    dashboard_layout: Optional[Dict[str, Any]] = Field(None, description="仪表板布局设置")

    @validator("theme")
    def validate_theme(cls, v):
        if v is not None:
            allowed_themes = ["light", "dark", "auto"]
            if v not in allowed_themes:
                raise ValueError(f"主题必须是以下之一: {', '.join(allowed_themes)}")
        return v

    @validator("language")
    def validate_language(cls, v):
        if v is not None:
            allowed_languages = ["zh-CN", "en-US", "ja-JP"]
            if v not in allowed_languages:
                raise ValueError(f"语言必须是以下之一: {', '.join(allowed_languages)}")
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="用户密码")
    remember_me: bool = Field(default=False, description="记住我")
    device_info: Optional[Dict[str, str]] = Field(None, description="设备信息")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    full_name: str = Field(..., description="用户全名")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否活跃")
    email_verified: bool = Field(..., description="邮箱是否已验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    preferences: Optional[UserPreferences] = Field(None, description="用户偏好设置")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserDetailResponse(UserResponse):
    """用户详情响应模型（包含更多信息）"""
    login_attempts: int = Field(..., description="登录尝试次数")
    locked_until: Optional[datetime] = Field(None, description="锁定到期时间")
    dingtalk_userid: Optional[str] = Field(None, description="钉钉用户ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")

    @classmethod
    def from_user_dict(cls, user_dict: Dict[str, Any]) -> "UserDetailResponse":
        """从用户字典创建详情响应"""
        # 处理偏好设置
        preferences_data = user_dict.get("preferences")
        preferences = None
        if preferences_data:
            try:
                if isinstance(preferences_data, dict):
                    preferences = UserPreferences(**preferences_data)
                else:
                    preferences = UserPreferences()
            except Exception:
                preferences = UserPreferences()

        # 提取钉钉用户ID
        dingtalk_userid = None
        if preferences_data and isinstance(preferences_data, dict):
            dingtalk_userid = preferences_data.get("dingtalk_userid")

        return cls(
            id=user_dict["id"],
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=UserRole(user_dict["role"]),
            is_active=user_dict["is_active"],
            email_verified=user_dict["email_verified"],
            created_at=user_dict["created_at"],
            updated_at=user_dict["updated_at"],
            last_login_at=user_dict.get("last_login_at"),
            login_attempts=user_dict.get("login_attempts", 0),
            locked_until=user_dict.get("locked_until"),
            preferences=preferences,
            dingtalk_userid=dingtalk_userid,
            metadata=user_dict.get("metadata", {})
        )


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总用户数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多数据")

    @validator("has_more", pre=True, always=True)
    def calculate_has_more(cls, v, values):
        if "total" in values and "offset" in values and "limit" in values:
            return values["offset"] + values["limit"] < values["total"]
        return False


class UserStatisticsResponse(BaseModel):
    """用户统计响应模型"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    users_by_role: Dict[str, int] = Field(..., description="按角色统计的用户数")
    recent_users: int = Field(..., description="最近注册用户数")
    growth_rate: float = Field(default=0.0, description="增长率")

    @validator("growth_rate", pre=True, always=True)
    def calculate_growth_rate(cls, v, values):
        if "total_users" in values and "recent_users" in values:
            total = values["total_users"]
            recent = values["recent_users"]
            if total > 0:
                return round((recent / total) * 100, 2)
        return 0.0


class UserActivitySummary(BaseModel):
    """用户活动摘要模型"""
    user_id: str = Field(..., description="用户ID")
    period_days: int = Field(..., description="统计天数")
    total_activities: int = Field(..., description="总活动数")
    daily_counts: Dict[str, int] = Field(..., description="每日活动数")
    average_daily: float = Field(..., description="日均活动数")


class LoginResponse(BaseModel):
    """登录响应模型"""
    user: UserResponse = Field(..., description="用户信息")
    session_id: str = Field(..., description="会话ID")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    expires_at: datetime = Field(..., description="会话过期时间")


class TokenRefreshRequest(BaseModel):
    """令牌刷新请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenRefreshResponse(BaseModel):
    """令牌刷新响应模型"""
    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[str] = Field(..., description="用户角色列表")


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    last_accessed: datetime = Field(..., description="最后访问时间")
    expires_at: datetime = Field(..., description="过期时间")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    is_current: bool = Field(default=False, description="是否为当前会话")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserSessionsResponse(BaseModel):
    """用户会话响应模型"""
    user_id: str = Field(..., description="用户ID")
    sessions: List[SessionInfo] = Field(..., description="会话列表")
    total_sessions: int = Field(..., description="总会话数")

    @validator("total_sessions", pre=True, always=True)
    def calculate_total_sessions(cls, v, values):
        if "sessions" in values:
            return len(values["sessions"])
        return 0


class DingTalkSyncRequest(BaseModel):
    """钉钉同步请求模型"""
    dingtalk_userid: str = Field(..., max_length=100, description="钉钉用户ID")
    force_update: bool = Field(default=False, description="是否强制更新")


class UserSearchRequest(BaseModel):
    """用户搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    role: Optional[UserRole] = Field(None, description="按角色过滤")
    active_only: bool = Field(default=True, description="仅搜索活跃用户")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")


class BulkUserOperation(BaseModel):
    """批量用户操作模型"""
    user_ids: List[str] = Field(..., min_items=1, max_items=100, description="用户ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作参数")

    @validator("operation")
    def validate_operation(cls, v):
        allowed_operations = ["activate", "deactivate", "delete", "change_role", "send_notification"]
        if v not in allowed_operations:
            raise ValueError(f"操作类型必须是以下之一: {', '.join(allowed_operations)}")
        return v


class BulkOperationResponse(BaseModel):
    """批量操作响应模型"""
    operation: str = Field(..., description="操作类型")
    total_requested: int = Field(..., description="请求操作的用户数")
    successful: int = Field(..., description="成功操作的用户数")
    failed: int = Field(..., description="失败操作的用户数")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="错误详情")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="操作结果详情")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认请求模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("两次输入的密码不匹配")
        return v

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一位数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一位字母")
        return v