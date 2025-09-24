"""
BaseAgent抽象基类

定义所有Agent的通用接口和基础功能，包括消息处理、生命周期管理、健康检查等。
集成DashScope API客户端和Redis缓存系统。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .message_types import (
    AgentMessage, TaskMessage, ResponseMessage, StatusMessage,
    HealthCheckMessage, HealthCheckResponse, HeartbeatMessage, ErrorMessage,
    AgentStatus, Priority, MessageType,
    create_response_message, create_status_message, create_error_message
)

# 注意：这些导入需要根据实际项目结构调整
# from app.dashscope.client import DashScopeClient
# from app.core.redis import RedisClient
# from app.core.config import Settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent抽象基类

    提供所有Agent的通用功能：
    - 消息队列管理
    - 生命周期管理
    - 健康检查
    - DashScope API集成
    - Redis缓存集成
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        max_concurrent_tasks: int = 5,
        heartbeat_interval: int = 30,
        max_queue_size: int = 100
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.max_concurrent_tasks = max_concurrent_tasks
        self.heartbeat_interval = heartbeat_interval
        self.max_queue_size = max_queue_size

        # 状态管理
        self._status = AgentStatus.IDLE
        self._is_running = False
        self._start_time: Optional[datetime] = None
        self._last_activity = datetime.utcnow()

        # 消息队列
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._processing_tasks: Set[asyncio.Task] = set()
        self._message_handlers: Dict[MessageType, Callable] = {}

        # 统计信息
        self._message_count = 0
        self._error_count = 0
        self._task_count = 0
        self._last_error: Optional[str] = None

        # 外部依赖（需要在子类中初始化）
        self.dashscope_client = None  # DashScopeClient实例
        self.redis_client = None      # RedisClient实例
        self.settings = None          # Settings实例

        # 注册默认消息处理器
        self._register_default_handlers()

        # 后台任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self._message_handlers.update({
            MessageType.TASK: self._handle_task_message,
            MessageType.STATUS: self._handle_status_message,
            MessageType.HEALTH_CHECK: self._handle_health_check,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.ERROR: self._handle_error_message,
        })

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running

    @property
    def uptime_seconds(self) -> int:
        """获取运行时间（秒）"""
        if self._start_time:
            return int((datetime.utcnow() - self._start_time).total_seconds())
        return 0

    @property
    def load_percentage(self) -> float:
        """获取当前负载百分比"""
        if self.max_concurrent_tasks == 0:
            return 0.0
        return (len(self._processing_tasks) / self.max_concurrent_tasks) * 100

    async def start(self):
        """启动Agent"""
        if self._is_running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return

        logger.info(f"Starting agent {self.agent_id} of type {self.agent_type}")

        try:
            # 初始化外部依赖
            await self._initialize_dependencies()

            # 设置状态
            self._is_running = True
            self._start_time = datetime.utcnow()
            self._status = AgentStatus.IDLE

            # 启动后台任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            # 启动消息处理循环
            await self._message_processing_loop()

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self._status = AgentStatus.ERROR
            self._last_error = str(e)
            raise

    async def stop(self, timeout: int = 30):
        """停止Agent"""
        if not self._is_running:
            return

        logger.info(f"Stopping agent {self.agent_id}")
        self._status = AgentStatus.STOPPING

        try:
            # 等待当前任务完成
            if self._processing_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self._processing_tasks, return_exceptions=True),
                    timeout=timeout
                )

            # 取消后台任务
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()

            # 清理资源
            await self._cleanup_resources()

            self._is_running = False
            self._status = AgentStatus.STOPPED
            logger.info(f"Agent {self.agent_id} stopped successfully")

        except asyncio.TimeoutError:
            logger.warning(f"Agent {self.agent_id} stop timeout, forcing shutdown")
            # 强制取消所有任务
            for task in self._processing_tasks:
                task.cancel()
            self._status = AgentStatus.ERROR
        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}")
            self._status = AgentStatus.ERROR
            raise

    async def restart(self, timeout: int = 30):
        """重启Agent"""
        await self.stop(timeout)
        await asyncio.sleep(1)  # 短暂等待
        await self.start()

    async def send_message(self, message: AgentMessage):
        """发送消息到队列"""
        try:
            await self._message_queue.put(message)
            self._message_count += 1
            self._last_activity = datetime.utcnow()
        except asyncio.QueueFull:
            error_msg = f"Message queue full for agent {self.agent_id}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def get_status(self) -> StatusMessage:
        """获取当前状态消息"""
        return create_status_message(
            sender_id=self.agent_id,
            status=self._status,
            load_percentage=self.load_percentage,
            capabilities=await self.get_capabilities()
        )

    async def health_check(self) -> HealthCheckResponse:
        """执行健康检查"""
        service_status = {}
        system_metrics = {}

        try:
            # 检查DashScope连接
            if self.dashscope_client:
                service_status["dashscope"] = await self._check_dashscope_health()

            # 检查Redis连接
            if self.redis_client:
                service_status["redis"] = await self._check_redis_health()

            # 收集系统指标
            system_metrics.update({
                "uptime_seconds": self.uptime_seconds,
                "message_count": self._message_count,
                "error_count": self._error_count,
                "task_count": self._task_count,
                "load_percentage": self.load_percentage,
                "queue_size": self._message_queue.qsize()
            })

            return HealthCheckResponse(
                sender_id=self.agent_id,
                original_message_id="health_check",
                success=all(service_status.values()),
                service_status=service_status,
                system_metrics=system_metrics,
                last_error=self._last_error
            )

        except Exception as e:
            logger.error(f"Health check failed for agent {self.agent_id}: {e}")
            return HealthCheckResponse(
                sender_id=self.agent_id,
                original_message_id="health_check",
                success=False,
                service_status=service_status,
                last_error=str(e)
            )

    # 抽象方法，子类必须实现
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        pass

    @abstractmethod
    async def process_task(self, task: TaskMessage) -> Dict[str, Any]:
        """处理具体任务，子类实现"""
        pass

    # 内部方法
    async def _initialize_dependencies(self):
        """初始化外部依赖，子类可重写"""
        # 这里应该初始化DashScope客户端、Redis客户端等
        # 具体实现依赖于项目结构
        pass

    async def _cleanup_resources(self):
        """清理资源，子类可重写"""
        pass

    async def _message_processing_loop(self):
        """消息处理主循环"""
        while self._is_running:
            try:
                # 等待消息，带超时避免阻塞
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )

                # 处理消息
                task = asyncio.create_task(self._process_message(message))
                self._processing_tasks.add(task)
                task.add_done_callback(self._processing_tasks.discard)

                # 如果任务过多，等待一些完成
                if len(self._processing_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)

            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                self._error_count += 1
                self._last_error = str(e)
                await asyncio.sleep(1)  # 错误时短暂等待

    async def _process_message(self, message: AgentMessage):
        """处理单个消息"""
        try:
            handler = self._message_handlers.get(message.type)
            if handler:
                await handler(message)
            else:
                logger.warning(f"No handler for message type {message.type}")

        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self._error_count += 1
            self._last_error = str(e)

            # 发送错误响应（如果需要）
            if hasattr(message, 'sender_id') and message.sender_id != self.agent_id:
                error_response = create_error_message(
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    correlation_id=message.correlation_id,
                    error_code="PROCESSING_ERROR",
                    error_message=str(e)
                )
                await self.send_message(error_response)

    async def _handle_task_message(self, message: TaskMessage):
        """处理任务消息"""
        start_time = datetime.utcnow()
        self._status = AgentStatus.PROCESSING
        self._task_count += 1

        try:
            # 检查任务是否过期
            if message.expires_at and message.expires_at <= datetime.utcnow():
                raise RuntimeError("Task message expired")

            # 处理任务
            result = await self.process_task(message)

            # 计算处理时间
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # 发送成功响应
            response = create_response_message(
                sender_id=self.agent_id,
                original_message=message,
                success=True,
                result=result,
                processing_time_ms=processing_time
            )
            await self.send_message(response)

        except Exception as e:
            # 发送错误响应
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            response = create_response_message(
                sender_id=self.agent_id,
                original_message=message,
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time
            )
            await self.send_message(response)
            raise
        finally:
            # 如果没有其他任务在处理，返回空闲状态
            if len(self._processing_tasks) <= 1:  # 当前任务即将完成
                self._status = AgentStatus.IDLE

    async def _handle_status_message(self, message: StatusMessage):
        """处理状态消息"""
        # 默认实现：记录日志
        logger.info(f"Received status from {message.sender_id}: {message.status}")

    async def _handle_health_check(self, message: HealthCheckMessage):
        """处理健康检查消息"""
        response = await self.health_check()
        response.original_message_id = message.id
        response.correlation_id = message.correlation_id
        response.recipient_id = message.sender_id
        await self.send_message(response)

    async def _handle_heartbeat(self, message: HeartbeatMessage):
        """处理心跳消息"""
        # 默认实现：更新活动时间
        self._last_activity = datetime.utcnow()

    async def _handle_error_message(self, message: ErrorMessage):
        """处理错误消息"""
        logger.error(f"Received error from {message.sender_id}: {message.error_message}")
        self._error_count += 1

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._is_running:
            try:
                heartbeat = HeartbeatMessage(
                    sender_id=self.agent_id,
                    uptime_seconds=self.uptime_seconds,
                    message_count=self._message_count,
                    last_activity=self._last_activity
                )
                await self.send_message(heartbeat)
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _cleanup_loop(self):
        """清理循环，定期清理过期消息和任务"""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # 每分钟执行一次
                # 这里可以添加清理逻辑
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _check_dashscope_health(self) -> bool:
        """检查DashScope连接健康状态"""
        try:
            if self.dashscope_client:
                # 执行简单的健康检查请求
                # return await self.dashscope_client.health_check()
                return True  # 暂时返回True
            return False
        except Exception:
            return False

    async def _check_redis_health(self) -> bool:
        """检查Redis连接健康状态"""
        try:
            if self.redis_client:
                # 执行Redis ping
                # return await self.redis_client.ping()
                return True  # 暂时返回True
            return False
        except Exception:
            return False