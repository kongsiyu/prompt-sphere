"""
Agent消息类型定义模块

定义Agent间通信使用的消息类型，包括基础消息、任务消息、状态消息等。
基于Pydantic实现类型安全的消息传递系统。
"""

from enum import Enum
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """消息类型枚举"""
    TASK = "task"                    # 任务消息
    RESPONSE = "response"            # 响应消息
    STATUS = "status"                # 状态消息
    HEALTH_CHECK = "health_check"    # 健康检查
    HEARTBEAT = "heartbeat"          # 心跳消息
    ERROR = "error"                  # 错误消息
    BROADCAST = "broadcast"          # 广播消息


class Priority(int, Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class AgentMessage(BaseModel):
    """Agent消息基类"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: str
    recipient_id: Optional[str] = None  # None表示广播消息
    correlation_id: Optional[str] = None  # 用于消息关联
    priority: Priority = Priority.NORMAL
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('expires_at', pre=True)
    def validate_expires_at(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("expires_at must be in the future")
        return v


class TaskMessage(AgentMessage):
    """任务消息"""
    type: MessageType = MessageType.TASK
    task_type: str  # PE_ENGINEER, PEQA, etc.
    task_data: Dict[str, Any]
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: Optional[int] = None


class ResponseMessage(AgentMessage):
    """响应消息"""
    type: MessageType = MessageType.RESPONSE
    original_message_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None


class StatusMessage(AgentMessage):
    """状态消息"""
    type: MessageType = MessageType.STATUS
    status: AgentStatus
    current_task_id: Optional[str] = None
    load_percentage: Optional[float] = Field(None, ge=0, le=100)
    capabilities: List[str] = Field(default_factory=list)

    @validator('load_percentage')
    def validate_load_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("load_percentage must be between 0 and 100")
        return v


class HealthCheckMessage(AgentMessage):
    """健康检查消息"""
    type: MessageType = MessageType.HEALTH_CHECK
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    services: List[str] = Field(default_factory=list)  # 需要检查的服务


class HealthCheckResponse(ResponseMessage):
    """健康检查响应"""
    service_status: Dict[str, bool]  # 服务名 -> 是否健康
    system_metrics: Optional[Dict[str, Union[int, float]]] = None
    last_error: Optional[str] = None


class HeartbeatMessage(AgentMessage):
    """心跳消息"""
    type: MessageType = MessageType.HEARTBEAT
    uptime_seconds: int
    message_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class ErrorMessage(AgentMessage):
    """错误消息"""
    type: MessageType = MessageType.ERROR
    error_code: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = True


class BroadcastMessage(AgentMessage):
    """广播消息"""
    type: MessageType = MessageType.BROADCAST
    broadcast_type: str  # CONFIG_UPDATE, SHUTDOWN, etc.
    data: Dict[str, Any] = Field(default_factory=dict)
    target_roles: Optional[List[str]] = None  # 目标角色，None表示所有


# 消息工厂函数
def create_task_message(
    sender_id: str,
    recipient_id: str,
    task_type: str,
    task_data: Dict[str, Any],
    priority: Priority = Priority.NORMAL,
    correlation_id: Optional[str] = None,
    timeout_seconds: Optional[int] = None
) -> TaskMessage:
    """创建任务消息"""
    return TaskMessage(
        sender_id=sender_id,
        recipient_id=recipient_id,
        task_type=task_type,
        task_data=task_data,
        priority=priority,
        correlation_id=correlation_id,
        timeout_seconds=timeout_seconds
    )


def create_response_message(
    sender_id: str,
    original_message: AgentMessage,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None
) -> ResponseMessage:
    """创建响应消息"""
    return ResponseMessage(
        sender_id=sender_id,
        recipient_id=original_message.sender_id,
        original_message_id=original_message.id,
        correlation_id=original_message.correlation_id,
        success=success,
        result=result,
        error_message=error_message,
        processing_time_ms=processing_time_ms
    )


def create_status_message(
    sender_id: str,
    status: AgentStatus,
    current_task_id: Optional[str] = None,
    load_percentage: Optional[float] = None,
    capabilities: Optional[List[str]] = None
) -> StatusMessage:
    """创建状态消息"""
    return StatusMessage(
        sender_id=sender_id,
        status=status,
        current_task_id=current_task_id,
        load_percentage=load_percentage,
        capabilities=capabilities or []
    )


def create_error_message(
    sender_id: str,
    error_code: str,
    error_message: str,
    recipient_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    recoverable: bool = True,
    context: Optional[Dict[str, Any]] = None
) -> ErrorMessage:
    """创建错误消息"""
    return ErrorMessage(
        sender_id=sender_id,
        recipient_id=recipient_id,
        correlation_id=correlation_id,
        error_code=error_code,
        error_message=error_message,
        recoverable=recoverable,
        context=context or {}
    )