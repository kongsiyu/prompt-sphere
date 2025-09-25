"""
Agent编排器模块

负责管理多个Agent实例，包括Agent注册、任务分发、负载均衡、
健康监控等功能。支持多种负载均衡策略和故障恢复机制。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import defaultdict, deque
import json

from .base_agent import BaseAgent
from .message_types import (
    AgentMessage, TaskMessage, StatusMessage, HealthCheckMessage,
    BroadcastMessage, ErrorMessage, AgentStatus, Priority, MessageType,
    create_task_message, create_error_message
)

logger = logging.getLogger(__name__)


class LoadBalanceStrategy(str, Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    RANDOM = "random"


class AgentRegistration:
    """Agent注册信息"""
    def __init__(
        self,
        agent: BaseAgent,
        capabilities: List[str],
        weight: float = 1.0,
        max_queue_size: int = 100
    ):
        self.agent = agent
        self.capabilities = capabilities
        self.weight = weight
        self.max_queue_size = max_queue_size
        self.registered_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.task_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.is_healthy = True


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_LOADED):
        self.strategy = strategy
        self._round_robin_index = 0
        self._agent_weights: Dict[str, float] = {}

    def select_agent(
        self,
        agents: Dict[str, AgentRegistration],
        task_type: Optional[str] = None
    ) -> Optional[str]:
        """根据策略选择Agent"""

        # 过滤可用的Agent
        available_agents = {
            agent_id: reg for agent_id, reg in agents.items()
            if reg.is_healthy and reg.agent.status in [AgentStatus.IDLE, AgentStatus.BUSY]
            and (not task_type or task_type in reg.capabilities)
        }

        if not available_agents:
            return None

        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(list(available_agents.keys()))
        elif self.strategy == LoadBalanceStrategy.LEAST_LOADED:
            return self._least_loaded_select(available_agents)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(available_agents)
        else:  # RANDOM
            import random
            return random.choice(list(available_agents.keys()))

    def _round_robin_select(self, agent_ids: List[str]) -> str:
        """轮询选择"""
        if not agent_ids:
            return None

        selected = agent_ids[self._round_robin_index % len(agent_ids)]
        self._round_robin_index += 1
        return selected

    def _least_loaded_select(self, agents: Dict[str, AgentRegistration]) -> str:
        """选择负载最少的Agent"""
        min_load = float('inf')
        selected_agent = None

        for agent_id, reg in agents.items():
            load = reg.agent.load_percentage
            if load < min_load:
                min_load = load
                selected_agent = agent_id

        return selected_agent

    def _weighted_select(self, agents: Dict[str, AgentRegistration]) -> str:
        """加权选择"""
        import random

        # 计算权重（考虑负载和配置权重）
        weighted_agents = []
        for agent_id, reg in agents.items():
            # 权重 = 配置权重 * (1 - 负载百分比/100)
            effective_weight = reg.weight * (1 - reg.agent.load_percentage / 100)
            weighted_agents.append((agent_id, effective_weight))

        # 加权随机选择
        total_weight = sum(weight for _, weight in weighted_agents)
        if total_weight == 0:
            return random.choice(list(agents.keys()))

        r = random.uniform(0, total_weight)
        cumulative = 0
        for agent_id, weight in weighted_agents:
            cumulative += weight
            if r <= cumulative:
                return agent_id

        return weighted_agents[-1][0]  # 回退


class TaskHistory:
    """任务历史记录"""
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.tasks: deque = deque(maxlen=max_history)
        self.task_stats = defaultdict(lambda: {"count": 0, "avg_time": 0, "success_rate": 0})

    def record_task(
        self,
        task_id: str,
        agent_id: str,
        task_type: str,
        success: bool,
        processing_time: float
    ):
        """记录任务执行历史"""
        record = {
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "success": success,
            "processing_time": processing_time,
            "timestamp": datetime.now(timezone.utc)
        }
        self.tasks.append(record)

        # 更新统计信息
        key = f"{agent_id}:{task_type}"
        stats = self.task_stats[key]
        stats["count"] += 1
        stats["avg_time"] = (stats["avg_time"] * (stats["count"] - 1) + processing_time) / stats["count"]

        # 计算成功率
        recent_tasks = [t for t in self.tasks if t["agent_id"] == agent_id and t["task_type"] == task_type]
        success_count = sum(1 for t in recent_tasks if t["success"])
        stats["success_rate"] = success_count / len(recent_tasks) if recent_tasks else 0

    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent性能统计"""
        agent_tasks = [t for t in self.tasks if t["agent_id"] == agent_id]
        if not agent_tasks:
            return {}

        success_count = sum(1 for t in agent_tasks if t["success"])
        avg_time = sum(t["processing_time"] for t in agent_tasks) / len(agent_tasks)

        return {
            "total_tasks": len(agent_tasks),
            "success_rate": success_count / len(agent_tasks),
            "avg_processing_time": avg_time,
            "last_task": agent_tasks[-1]["timestamp"] if agent_tasks else None
        }


class AgentOrchestrator:
    """Agent编排器主类"""

    def __init__(
        self,
        load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_LOADED,
        health_check_interval: int = 30,
        max_task_history: int = 1000,
        redis_client=None  # Redis客户端实例
    ):
        self.load_balancer = LoadBalancer(load_balance_strategy)
        self.health_check_interval = health_check_interval
        self.redis_client = redis_client

        # Agent管理
        self.agents: Dict[str, AgentRegistration] = {}
        self.task_history = TaskHistory(max_task_history)

        # 任务管理
        self.pending_tasks: Dict[str, TaskMessage] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id

        # 状态管理
        self._is_running = False
        self._background_tasks: Set[asyncio.Task] = set()

        # 事件回调
        self.on_agent_registered: Optional[Callable] = None
        self.on_agent_unregistered: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None
        self.on_agent_error: Optional[Callable] = None

    async def start(self):
        """启动编排器"""
        if self._is_running:
            return

        logger.info("Starting Agent Orchestrator")
        self._is_running = True

        # 启动后台任务
        health_task = asyncio.create_task(self._health_check_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())

        self._background_tasks.update([health_task, cleanup_task])

        # 从Redis恢复Agent注册信息（如果配置了Redis）
        if self.redis_client:
            await self._restore_agent_registrations()

    async def stop(self):
        """停止编排器"""
        if not self._is_running:
            return

        logger.info("Stopping Agent Orchestrator")
        self._is_running = False

        # 取消所有后台任务
        for task in self._background_tasks:
            task.cancel()

        # 等待任务完成
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

    async def register_agent(
        self,
        agent: BaseAgent,
        capabilities: List[str],
        weight: float = 1.0,
        max_queue_size: int = 100
    ) -> bool:
        """注册Agent"""
        try:
            # 检查agent是否为None
            if agent is None:
                logger.error("Cannot register None agent")
                return False

            if agent.agent_id in self.agents:
                logger.warning(f"Agent {agent.agent_id} already registered")
                return False

            registration = AgentRegistration(agent, capabilities, weight, max_queue_size)
            self.agents[agent.agent_id] = registration

            # 持久化到Redis
            if self.redis_client:
                await self._persist_agent_registration(agent.agent_id, registration)

            logger.info(f"Agent {agent.agent_id} registered with capabilities: {capabilities}")

            # 触发回调
            if self.on_agent_registered:
                await self.on_agent_registered(agent.agent_id, capabilities)

            return True

        except Exception as e:
            agent_id = getattr(agent, 'agent_id', 'unknown') if agent else 'unknown'
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not registered")
                return False

            # 取消该Agent的所有待处理任务
            await self._reassign_agent_tasks(agent_id)

            # 移除注册
            del self.agents[agent_id]

            # 从Redis删除
            if self.redis_client:
                await self._remove_agent_registration(agent_id)

            logger.info(f"Agent {agent_id} unregistered")

            # 触发回调
            if self.on_agent_unregistered:
                await self.on_agent_unregistered(agent_id)

            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    async def dispatch_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        timeout_seconds: Optional[int] = None
    ) -> Optional[str]:
        """分发任务到合适的Agent"""
        try:
            # 选择Agent
            agent_id = self.load_balancer.select_agent(self.agents, task_type)
            if not agent_id:
                logger.error(f"No available agent for task type: {task_type}")
                return None

            # 创建任务消息
            task_message = create_task_message(
                sender_id="orchestrator",
                recipient_id=agent_id,
                task_type=task_type,
                task_data=task_data,
                priority=priority,
                timeout_seconds=timeout_seconds
            )

            # 记录任务分配
            self.pending_tasks[task_message.id] = task_message
            self.task_assignments[task_message.id] = agent_id

            # 发送任务到Agent
            agent_registration = self.agents[agent_id]
            await agent_registration.agent.send_message(task_message)

            logger.info(f"Task {task_message.id} dispatched to agent {agent_id}")
            return task_message.id

        except Exception as e:
            logger.error(f"Failed to dispatch task: {e}")
            return None

    async def broadcast_message(
        self,
        broadcast_type: str,
        data: Dict[str, Any],
        target_capabilities: Optional[List[str]] = None
    ):
        """广播消息给所有或特定Agent"""
        try:
            message = BroadcastMessage(
                sender_id="orchestrator",
                broadcast_type=broadcast_type,
                data=data,
                target_roles=target_capabilities
            )

            target_agents = self.agents.values()
            if target_capabilities:
                # 过滤具有特定能力的Agent
                target_agents = [
                    reg for reg in target_agents
                    if any(cap in reg.capabilities for cap in target_capabilities)
                ]

            for registration in target_agents:
                await registration.agent.send_message(message)

            logger.info(f"Broadcast message '{broadcast_type}' sent to {len(target_agents)} agents")

        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent状态"""
        if agent_id not in self.agents:
            return None

        registration = self.agents[agent_id]
        agent = registration.agent

        return {
            "agent_id": agent_id,
            "status": agent.status.value,
            "capabilities": registration.capabilities,
            "load_percentage": agent.load_percentage,
            "uptime_seconds": agent.uptime_seconds,
            "task_count": registration.task_count,
            "error_count": registration.error_count,
            "is_healthy": registration.is_healthy,
            "last_heartbeat": registration.last_heartbeat,
            "performance": self.task_history.get_agent_performance(agent_id)
        }

    async def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent状态"""
        return {
            agent_id: await self.get_agent_status(agent_id)
            for agent_id in self.agents.keys()
        }

    async def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """获取编排器指标"""
        total_agents = len(self.agents)
        healthy_agents = sum(1 for reg in self.agents.values() if reg.is_healthy)
        idle_agents = sum(
            1 for reg in self.agents.values()
            if reg.agent.status == AgentStatus.IDLE
        )
        busy_agents = sum(
            1 for reg in self.agents.values()
            if reg.agent.status == AgentStatus.BUSY
        )

        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "idle_agents": idle_agents,
            "busy_agents": busy_agents,
            "pending_tasks": len(self.pending_tasks),
            "total_task_history": len(self.task_history.tasks),
            "is_running": self._is_running
        }

    # 内部方法
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _cleanup_loop(self):
        """清理循环"""
        while self._is_running:
            try:
                await asyncio.sleep(300)  # 每5分钟执行一次
                await self._cleanup_expired_tasks()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _perform_health_checks(self):
        """执行健康检查"""
        current_time = datetime.now(timezone.utc)

        for agent_id, registration in self.agents.items():
            try:
                # 检查心跳超时
                heartbeat_timeout = timedelta(seconds=self.health_check_interval * 3)
                if current_time - registration.last_heartbeat > heartbeat_timeout:
                    logger.warning(f"Agent {agent_id} heartbeat timeout")
                    registration.is_healthy = False
                    continue

                # 执行健康检查
                health_check_msg = HealthCheckMessage(
                    sender_id="orchestrator",
                    recipient_id=agent_id
                )

                await registration.agent.send_message(health_check_msg)

            except Exception as e:
                logger.error(f"Health check failed for agent {agent_id}: {e}")
                registration.is_healthy = False

    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        current_time = datetime.now(timezone.utc)
        expired_tasks = []

        for task_id, task_message in self.pending_tasks.items():
            if (task_message.expires_at and
                task_message.expires_at <= current_time):
                expired_tasks.append(task_id)

        for task_id in expired_tasks:
            logger.warning(f"Task {task_id} expired")
            self._remove_task(task_id)

    async def _reassign_agent_tasks(self, agent_id: str):
        """重新分配Agent的任务"""
        tasks_to_reassign = [
            task_id for task_id, assigned_agent_id in self.task_assignments.items()
            if assigned_agent_id == agent_id
        ]

        for task_id in tasks_to_reassign:
            if task_id in self.pending_tasks:
                task_message = self.pending_tasks[task_id]
                logger.info(f"Reassigning task {task_id} from agent {agent_id}")

                # 尝试重新分发任务
                new_task_id = await self.dispatch_task(
                    task_message.task_type,
                    task_message.task_data,
                    task_message.priority,
                    task_message.timeout_seconds
                )

                if new_task_id:
                    # 移除原任务
                    self._remove_task(task_id)
                else:
                    logger.error(f"Failed to reassign task {task_id}")

    def _remove_task(self, task_id: str):
        """移除任务记录"""
        self.pending_tasks.pop(task_id, None)
        self.task_assignments.pop(task_id, None)

    async def _persist_agent_registration(self, agent_id: str, registration: AgentRegistration):
        """持久化Agent注册信息到Redis"""
        if not self.redis_client:
            return

        try:
            data = {
                "capabilities": registration.capabilities,
                "weight": registration.weight,
                "max_queue_size": registration.max_queue_size,
                "registered_at": registration.registered_at.isoformat()
            }
            # await self.redis_client.hset(
            #     "agent_registrations",
            #     agent_id,
            #     json.dumps(data)
            # )
        except Exception as e:
            logger.error(f"Failed to persist agent registration: {e}")

    async def _remove_agent_registration(self, agent_id: str):
        """从Redis删除Agent注册信息"""
        if not self.redis_client:
            return

        try:
            # await self.redis_client.hdel("agent_registrations", agent_id)
            pass
        except Exception as e:
            logger.error(f"Failed to remove agent registration: {e}")

    async def _restore_agent_registrations(self):
        """从Redis恢复Agent注册信息"""
        if not self.redis_client:
            return

        try:
            # registrations = await self.redis_client.hgetall("agent_registrations")
            # for agent_id, data_json in registrations.items():
            #     data = json.loads(data_json)
            #     # 这里需要重新连接到Agent实例，具体实现依赖于应用架构
            pass
        except Exception as e:
            logger.error(f"Failed to restore agent registrations: {e}")