"""令牌数据模型和相关的数据结构"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseEntity(Base):
    """数据库实体基类"""
    __abstract__ = True

    id = Column(String(36), primary_key=True, comment="主键ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class TokenType(str, Enum):
    """令牌类型枚举"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"


class TokenStatus(str, Enum):
    """令牌状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    BLACKLISTED = "blacklisted"


class TokenScope(str, Enum):
    """令牌作用域枚举"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    USER_MANAGEMENT = "user:management"
    API_ACCESS = "api:access"


class UserTokenModel(BaseEntity):
    """用户令牌数据库模型"""
    __tablename__ = "user_tokens"

    jti = Column(String(36), unique=True, nullable=False, index=True, comment="JWT ID")
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    token_type = Column(String(32), nullable=False, comment="令牌类型")
    token_hash = Column(String(256), nullable=True, comment="令牌哈希")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="签发时间")
    status = Column(String(32), nullable=False, default=TokenStatus.ACTIVE.value, comment="令牌状态")
    scopes = Column(Text, nullable=True, comment="令牌作用域（JSON格式）")
    client_info = Column(Text, nullable=True, comment="客户端信息（JSON格式）")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    refresh_count = Column(Integer, default=0, comment="刷新次数")
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")


class TokenCreateRequest(BaseModel):
    """创建令牌请求"""
    user_id: str = Field(..., description="用户ID")
    token_type: TokenType = Field(default=TokenType.ACCESS, description="令牌类型")
    expires_in: Optional[int] = Field(default=900, description="过期时间（秒）")
    scopes: List[TokenScope] = Field(default_factory=list, description="令牌作用域")
    client_info: Optional[Dict[str, Any]] = Field(default=None, description="客户端信息")

    @validator('expires_in')
    def validate_expires_in(cls, v):
        if v and (v < 60 or v > 31536000):  # 1分钟到1年
            raise ValueError("过期时间必须在60秒到31536000秒之间")
        return v


class TokenInfo(BaseModel):
    """令牌信息"""
    jti: str = Field(..., description="令牌ID")
    user_id: str = Field(..., description="用户ID")
    token_type: TokenType = Field(..., description="令牌类型")
    status: TokenStatus = Field(..., description="令牌状态")
    scopes: List[TokenScope] = Field(default_factory=list, description="令牌作用域")
    issued_at: datetime = Field(..., description="签发时间")
    expires_at: datetime = Field(..., description="过期时间")
    last_used_at: Optional[datetime] = Field(default=None, description="最后使用时间")
    refresh_count: int = Field(default=0, description="刷新次数")
    client_info: Optional[Dict[str, Any]] = Field(default=None, description="客户端信息")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: Optional[str] = Field(default=None, description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    scope: Optional[str] = Field(default=None, description="令牌作用域")

    @validator('token_type')
    def validate_token_type(cls, v):
        if v.lower() not in ['bearer', 'basic']:
            raise ValueError("令牌类型必须是 'bearer' 或 'basic'")
        return v.lower()


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")
    scopes: Optional[List[TokenScope]] = Field(default=None, description="新的作用域（可选）")


class RevokeTokenRequest(BaseModel):
    """撤销令牌请求"""
    token: str = Field(..., description="要撤销的令牌")
    token_type_hint: Optional[str] = Field(default=None, description="令牌类型提示")


class TokenValidationResult(BaseModel):
    """令牌验证结果"""
    is_valid: bool = Field(..., description="是否有效")
    token_info: Optional[TokenInfo] = Field(default=None, description="令牌信息")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")


class TokenBlacklistEntry(BaseModel):
    """令牌黑名单条目"""
    jti: str = Field(..., description="令牌ID")
    user_id: str = Field(..., description="用户ID")
    token_hash: str = Field(..., description="令牌哈希")
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow, description="加入黑名单时间")
    reason: Optional[str] = Field(default=None, description="黑名单原因")
    expires_at: datetime = Field(..., description="原始过期时间")

    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """用户会话信息"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[str] = Field(default_factory=list, description="用户角色")
    permissions: List[str] = Field(default_factory=list, description="用户权限")
    login_time: datetime = Field(default_factory=datetime.utcnow, description="登录时间")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="最后活动时间")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    is_active: bool = Field(default=True, description="是否活跃")

    class Config:
        from_attributes = True


class LoginAttempt(BaseModel):
    """登录尝试记录"""
    username: str = Field(..., description="用户名")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    attempt_time: datetime = Field(default_factory=datetime.utcnow, description="尝试时间")
    success: bool = Field(..., description="是否成功")
    failure_reason: Optional[str] = Field(default=None, description="失败原因")

    class Config:
        from_attributes = True


class SecurityEvent(BaseModel):
    """安全事件"""
    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    event_time: datetime = Field(default_factory=datetime.utcnow, description="事件时间")
    severity: str = Field(default="info", description="严重程度")
    details: Optional[Dict[str, Any]] = Field(default=None, description="事件详情")

    class Config:
        from_attributes = True

    @validator('severity')
    def validate_severity(cls, v):
        allowed_severities = ['info', 'warning', 'error', 'critical']
        if v.lower() not in allowed_severities:
            raise ValueError(f"严重程度必须是以下之一: {allowed_severities}")
        return v.lower()


class TokenMetrics(BaseModel):
    """令牌指标统计"""
    total_tokens: int = Field(default=0, description="总令牌数")
    active_tokens: int = Field(default=0, description="活跃令牌数")
    expired_tokens: int = Field(default=0, description="过期令牌数")
    revoked_tokens: int = Field(default=0, description="撤销令牌数")
    tokens_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型分组的令牌数")
    tokens_by_user: Dict[str, int] = Field(default_factory=dict, description="按用户分组的令牌数")

    class Config:
        from_attributes = True


class CleanupResult(BaseModel):
    """清理操作结果"""
    cleaned_tokens: int = Field(default=0, description="清理的令牌数")
    cleaned_sessions: int = Field(default=0, description="清理的会话数")
    cleaned_attempts: int = Field(default=0, description="清理的登录尝试记录数")
    cleaned_events: int = Field(default=0, description="清理的安全事件数")
    operation_time: float = Field(default=0.0, description="操作耗时（秒）")

    class Config:
        from_attributes = True