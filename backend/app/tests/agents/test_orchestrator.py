"""
AgentOrchestrator测试模块

测试Agent编排器的功能，包括Agent注册、任务分发、负载均衡、健康监控等。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.agents.base.orchestrator import (
    AgentOrchestrator, LoadBalancer, AgentRegistration, TaskHistory,
    LoadBalanceStrategy
)
from app.agents.base.base_agent import BaseAgent
from app.agents.base.message_types import (
    AgentMessage, TaskMessage, StatusMessage, AgentStatus, Priority,
    create_task_message
)


class MockAgent(BaseAgent):
    """测试用的Mock Agent"""

    def __init__(self, agent_id: str, capabilities: List[str] = None):
        super().__init__(agent_id, "mock_agent")
        self._capabilities = capabilities or ["test_task"]
        self._mock_load = 0.0
        self._mock_status = AgentStatus.IDLE

    async def get_capabilities(self) -> List[str]:
        return self._capabilities

    async def process_task(self, task: TaskMessage) -> Dict[str, Any]:
        await asyncio.sleep(0.01)  # 模拟处理时间
        return {"result": f"Task {task.id} completed by {self.agent_id}"}

    @property
    def status(self) -> AgentStatus:
        return self._mock_status

    @property
    def load_percentage(self) -> float:
        return self._mock_load

    def set_mock_load(self, load: float):
        self._mock_load = load

    def set_mock_status(self, status: AgentStatus):
        self._mock_status = status


@pytest.fixture
def orchestrator():
    """创建测试用编排器"""
    return AgentOrchestrator(
        load_balance_strategy=LoadBalanceStrategy.LEAST_LOADED,
        health_check_interval=1,
        max_task_history=100
    )


@pytest.fixture
def mock_agents():
    """创建测试用Agent列表"""
    agents = [
        MockAgent("agent_001", ["task_a", "task_b"]),
        MockAgent("agent_002", ["task_b", "task_c"]),
        MockAgent("agent_003", ["task_a", "task_c"])
    ]
    return agents


class TestLoadBalancer:
    """测试负载均衡器"""

    def test_load_balancer_initialization(self):
        """测试负载均衡器初始化"""
        lb = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)
        assert lb.strategy == LoadBalanceStrategy.ROUND_ROBIN
        assert lb._round_robin_index == 0

    def test_round_robin_selection(self):
        """测试轮询选择策略"""
        lb = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)

        # 创建mock agent registrations
        agents = {}
        for i in range(3):
            mock_agent = MockAgent(f"agent_{i:03d}")
            agents[mock_agent.agent_id] = AgentRegistration(
                mock_agent, ["test_task"]
            )

        # 测试轮询选择
        selections = []
        for _ in range(6):  # 选择6次，应该轮询两轮
            selected = lb.select_agent(agents, "test_task")
            selections.append(selected)

        # 验证轮询模式
        assert len(set(selections)) == 3  # 应该选中所有3个agent
        assert selections[0] == selections[3]  # 第1和第4次应该选择相同agent

    def test_least_loaded_selection(self):
        """测试最少负载选择策略"""
        lb = LoadBalancer(LoadBalanceStrategy.LEAST_LOADED)

        agents = {}
        loads = [10.0, 50.0, 25.0]

        for i, load in enumerate(loads):
            mock_agent = MockAgent(f"agent_{i:03d}")
            mock_agent.set_mock_load(load)
            agents[mock_agent.agent_id] = AgentRegistration(
                mock_agent, ["test_task"]
            )

        selected = lb.select_agent(agents, "test_task")

        # 应该选择负载最低的agent（agent_000，负载10%）
        assert selected == "agent_000"

    def test_no_available_agents(self):
        """测试没有可用Agent时的处理"""
        lb = LoadBalancer(LoadBalanceStrategy.LEAST_LOADED)

        # 创建不健康的agent
        mock_agent = MockAgent("unhealthy_agent")
        mock_agent.set_mock_status(AgentStatus.ERROR)

        agents = {
            "unhealthy_agent": AgentRegistration(mock_agent, ["test_task"])
        }
        agents["unhealthy_agent"].is_healthy = False

        selected = lb.select_agent(agents, "test_task")
        assert selected is None

    def test_capability_filtering(self):
        """测试基于能力的过滤"""
        lb = LoadBalancer(LoadBalanceStrategy.LEAST_LOADED)

        # 创建具有不同能力的agents
        agents = {}

        agent1 = MockAgent("agent_001", ["task_a"])
        agent2 = MockAgent("agent_002", ["task_b"])

        agents["agent_001"] = AgentRegistration(agent1, ["task_a"])
        agents["agent_002"] = AgentRegistration(agent2, ["task_b"])

        # 选择task_a任务
        selected = lb.select_agent(agents, "task_a")
        assert selected == "agent_001"

        # 选择task_b任务
        selected = lb.select_agent(agents, "task_b")
        assert selected == "agent_002"

        # 选择不存在的任务类型
        selected = lb.select_agent(agents, "task_c")
        assert selected is None


class TestTaskHistory:
    """测试任务历史记录"""

    def test_task_history_initialization(self):
        """测试任务历史初始化"""
        history = TaskHistory(max_history=50)
        assert history.max_history == 50
        assert len(history.tasks) == 0

    def test_record_task(self):
        """测试任务记录"""
        history = TaskHistory(max_history=100)

        history.record_task(
            task_id="task_001",
            agent_id="agent_001",
            task_type="test_task",
            success=True,
            processing_time=0.5
        )

        assert len(history.tasks) == 1
        task_record = history.tasks[0]
        assert task_record["task_id"] == "task_001"
        assert task_record["success"] is True

    def test_task_statistics(self):
        """测试任务统计"""
        history = TaskHistory(max_history=100)

        # 记录多个任务
        for i in range(5):
            history.record_task(
                task_id=f"task_{i:03d}",
                agent_id="agent_001",
                task_type="test_task",
                success=i % 2 == 0,  # 50%成功率
                processing_time=0.1 + i * 0.1
            )

        stats = history.task_stats["agent_001:test_task"]
        assert stats["count"] == 5
        assert 0.4 <= stats["success_rate"] <= 0.6  # 约50%成功率
        assert stats["avg_time"] > 0

    def test_agent_performance(self):
        """测试Agent性能统计"""
        history = TaskHistory(max_history=100)

        # 记录任务
        for i in range(3):
            history.record_task(
                task_id=f"task_{i:03d}",
                agent_id="agent_001",
                task_type="test_task",
                success=True,
                processing_time=0.2
            )

        performance = history.get_agent_performance("agent_001")
        assert performance["total_tasks"] == 3
        assert performance["success_rate"] == 1.0
        assert performance["avg_processing_time"] == 0.2

    def test_max_history_limit(self):
        """测试历史记录数量限制"""
        history = TaskHistory(max_history=3)

        # 记录超过限制数量的任务
        for i in range(5):
            history.record_task(
                task_id=f"task_{i:03d}",
                agent_id="agent_001",
                task_type="test_task",
                success=True,
                processing_time=0.1
            )

        # 应该只保留最新的3条记录
        assert len(history.tasks) == 3
        assert history.tasks[0]["task_id"] == "task_002"  # 最老的保留记录


class TestAgentOrchestrator:
    """测试Agent编排器"""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """测试编排器初始化"""
        assert isinstance(orchestrator.load_balancer, LoadBalancer)
        assert orchestrator.health_check_interval == 1
        assert len(orchestrator.agents) == 0
        assert not orchestrator._is_running

    @pytest.mark.asyncio
    async def test_start_stop_orchestrator(self, orchestrator):
        """测试编排器启动停止"""
        assert not orchestrator._is_running

        # 启动编排器
        await orchestrator.start()
        assert orchestrator._is_running

        # 停止编排器
        await orchestrator.stop()
        assert not orchestrator._is_running

    @pytest.mark.asyncio
    async def test_agent_registration(self, orchestrator, mock_agents):
        """测试Agent注册"""
        await orchestrator.start()

        agent = mock_agents[0]
        success = await orchestrator.register_agent(
            agent=agent,
            capabilities=["task_a", "task_b"],
            weight=1.0
        )

        assert success is True
        assert agent.agent_id in orchestrator.agents

        registration = orchestrator.agents[agent.agent_id]
        assert registration.agent == agent
        assert "task_a" in registration.capabilities

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_duplicate_agent_registration(self, orchestrator, mock_agents):
        """测试重复注册Agent"""
        await orchestrator.start()

        agent = mock_agents[0]

        # 第一次注册
        success1 = await orchestrator.register_agent(agent, ["task_a"])
        assert success1 is True

        # 重复注册
        success2 = await orchestrator.register_agent(agent, ["task_a"])
        assert success2 is False

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_agent_unregistration(self, orchestrator, mock_agents):
        """测试Agent注销"""
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        assert agent.agent_id in orchestrator.agents

        success = await orchestrator.unregister_agent(agent.agent_id)
        assert success is True
        assert agent.agent_id not in orchestrator.agents

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_task_dispatch(self, orchestrator, mock_agents):
        """测试任务分发"""
        await orchestrator.start()

        # 注册Agent
        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["test_task"])

        # 分发任务
        task_id = await orchestrator.dispatch_task(
            task_type="test_task",
            task_data={"param": "value"},
            priority=Priority.NORMAL
        )

        assert task_id is not None
        assert task_id in orchestrator.pending_tasks
        assert task_id in orchestrator.task_assignments

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_task_dispatch_no_available_agent(self, orchestrator):
        """测试没有可用Agent时的任务分发"""
        await orchestrator.start()

        # 尝试分发任务但没有注册任何Agent
        task_id = await orchestrator.dispatch_task(
            task_type="nonexistent_task",
            task_data={}
        )

        assert task_id is None

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_broadcast_message(self, orchestrator, mock_agents):
        """测试广播消息"""
        await orchestrator.start()

        # 注册多个Agent
        for agent in mock_agents:
            await orchestrator.register_agent(agent, agent._capabilities)

        # 广播消息
        await orchestrator.broadcast_message(
            broadcast_type="test_broadcast",
            data={"message": "Hello all agents"}
        )

        # 这里应该验证所有Agent都收到了消息
        # 由于是mock agent，我们主要验证没有异常抛出
        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_targeted_broadcast(self, orchestrator, mock_agents):
        """测试目标广播"""
        await orchestrator.start()

        # 注册Agent
        for agent in mock_agents:
            await orchestrator.register_agent(agent, agent._capabilities)

        # 目标广播给有特定能力的Agent
        await orchestrator.broadcast_message(
            broadcast_type="targeted_broadcast",
            data={"message": "Targeted message"},
            target_capabilities=["task_a"]
        )

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_get_agent_status(self, orchestrator, mock_agents):
        """测试获取Agent状态"""
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        status = await orchestrator.get_agent_status(agent.agent_id)

        assert status is not None
        assert status["agent_id"] == agent.agent_id
        assert status["status"] == agent.status.value
        assert "capabilities" in status
        assert "load_percentage" in status

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_get_all_agents_status(self, orchestrator, mock_agents):
        """测试获取所有Agent状态"""
        await orchestrator.start()

        # 注册多个Agent
        for agent in mock_agents[:2]:  # 只注册前2个
            await orchestrator.register_agent(agent, agent._capabilities)

        all_status = await orchestrator.get_all_agents_status()

        assert len(all_status) == 2
        for agent_id, status in all_status.items():
            assert status["agent_id"] == agent_id

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_orchestrator_metrics(self, orchestrator, mock_agents):
        """测试编排器指标"""
        await orchestrator.start()

        # 注册Agent
        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        metrics = await orchestrator.get_orchestrator_metrics()

        assert metrics["total_agents"] == 1
        assert metrics["healthy_agents"] == 1
        assert "idle_agents" in metrics
        assert "busy_agents" in metrics
        assert "pending_tasks" in metrics

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_load_balancing_in_dispatch(self, orchestrator, mock_agents):
        """测试任务分发中的负载均衡"""
        await orchestrator.start()

        # 注册多个有相同能力的Agent
        for agent in mock_agents:
            await orchestrator.register_agent(agent, ["common_task"])

        # 设置不同的负载
        mock_agents[0].set_mock_load(10.0)
        mock_agents[1].set_mock_load(50.0)
        mock_agents[2].set_mock_load(25.0)

        # 分发任务，应该选择负载最低的Agent
        task_id = await orchestrator.dispatch_task(
            task_type="common_task",
            task_data={}
        )

        # 验证任务被分配给负载最低的Agent
        assigned_agent_id = orchestrator.task_assignments[task_id]
        assert assigned_agent_id == mock_agents[0].agent_id  # 负载10%的Agent

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_health_check_functionality(self, orchestrator, mock_agents):
        """测试健康检查功能"""
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        # 执行健康检查
        await orchestrator._perform_health_checks()

        # 由于是mock agent，主要验证没有异常
        registration = orchestrator.agents[agent.agent_id]
        assert registration.is_healthy is True

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_unhealthy_agent_handling(self, orchestrator, mock_agents):
        """测试不健康Agent的处理"""
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        # 模拟Agent变得不健康
        registration = orchestrator.agents[agent.agent_id]
        registration.is_healthy = False

        # 尝试分发任务，应该找不到可用的Agent
        task_id = await orchestrator.dispatch_task(
            task_type="task_a",
            task_data={}
        )

        assert task_id is None  # 没有健康的Agent可用

        await orchestrator.stop()


class TestOrchestratorCallbacks:
    """测试编排器回调功能"""

    @pytest.mark.asyncio
    async def test_agent_registered_callback(self, orchestrator, mock_agents):
        """测试Agent注册回调"""
        callback_called = False
        callback_agent_id = None

        async def on_agent_registered(agent_id, capabilities):
            nonlocal callback_called, callback_agent_id
            callback_called = True
            callback_agent_id = agent_id

        orchestrator.on_agent_registered = on_agent_registered
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        assert callback_called is True
        assert callback_agent_id == agent.agent_id

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_agent_unregistered_callback(self, orchestrator, mock_agents):
        """测试Agent注销回调"""
        callback_called = False

        async def on_agent_unregistered(agent_id):
            nonlocal callback_called
            callback_called = True

        orchestrator.on_agent_unregistered = on_agent_unregistered
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])
        await orchestrator.unregister_agent(agent.agent_id)

        assert callback_called is True

        await orchestrator.stop()


class TestOrchestratorErrorHandling:
    """测试编排器错误处理"""

    @pytest.mark.asyncio
    async def test_registration_error_handling(self, orchestrator):
        """测试注册错误处理"""
        await orchestrator.start()

        # 尝试注册None agent
        success = await orchestrator.register_agent(
            agent=None,
            capabilities=["task_a"]
        )

        assert success is False

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self, orchestrator):
        """测试注销不存在的Agent"""
        await orchestrator.start()

        success = await orchestrator.unregister_agent("nonexistent_agent")
        assert success is False

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_cleanup_expired_tasks(self, orchestrator, mock_agents):
        """测试过期任务清理"""
        await orchestrator.start()

        agent = mock_agents[0]
        await orchestrator.register_agent(agent, ["task_a"])

        # 创建过期任务
        task = create_task_message(
            sender_id="test",
            recipient_id=agent.agent_id,
            task_type="task_a",
            task_data={}
        )
        task.expires_at = datetime.utcnow() - timedelta(minutes=1)  # 已过期

        orchestrator.pending_tasks[task.id] = task
        orchestrator.task_assignments[task.id] = agent.agent_id

        # 执行清理
        await orchestrator._cleanup_expired_tasks()

        # 过期任务应该被清理
        assert task.id not in orchestrator.pending_tasks
        assert task.id not in orchestrator.task_assignments

        await orchestrator.stop()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])