"""
BaseAgent测试模块

测试BaseAgent抽象类的功能，包括消息处理、生命周期管理、健康检查等。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.agents.base.base_agent import BaseAgent
from app.agents.base.message_types import (
    AgentMessage, TaskMessage, StatusMessage, HealthCheckMessage,
    ResponseMessage, ErrorMessage, AgentStatus, Priority, MessageType,
    create_task_message, create_response_message
)


class TestAgent(BaseAgent):
    """测试用的Agent实现"""

    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "test_agent", **kwargs)
        self.processed_tasks = []
        self.should_fail = False
        self.processing_delay = 0

    async def get_capabilities(self) -> List[str]:
        return ["test_capability", "mock_task"]

    async def process_task(self, task: TaskMessage) -> Dict[str, Any]:
        """模拟任务处理"""
        if self.processing_delay > 0:
            await asyncio.sleep(self.processing_delay)

        if self.should_fail:
            raise RuntimeError("Simulated task failure")

        self.processed_tasks.append(task)
        return {
            "result": f"Task {task.id} processed successfully",
            "task_type": task.task_type,
            "data": task.task_data
        }

    async def _initialize_dependencies(self):
        """模拟依赖初始化"""
        self.dashscope_client = Mock()
        self.redis_client = Mock()
        self.settings = Mock()

    async def _cleanup_resources(self):
        """模拟资源清理"""
        pass


@pytest.fixture
def test_agent():
    """创建测试Agent实例"""
    return TestAgent("test_agent_001")


@pytest.fixture
def sample_task_message():
    """创建示例任务消息"""
    return create_task_message(
        sender_id="test_sender",
        recipient_id="test_agent_001",
        task_type="mock_task",
        task_data={"param1": "value1", "param2": 123}
    )


class TestBaseAgentBasics:
    """测试BaseAgent基础功能"""

    def test_agent_initialization(self):
        """测试Agent初始化"""
        agent = TestAgent(
            agent_id="test_001",
            max_concurrent_tasks=10,
            heartbeat_interval=60,
            max_queue_size=200
        )

        assert agent.agent_id == "test_001"
        assert agent.agent_type == "test_agent"
        assert agent.max_concurrent_tasks == 10
        assert agent.heartbeat_interval == 60
        assert agent.max_queue_size == 200
        assert agent.status == AgentStatus.IDLE
        assert not agent.is_running
        assert agent.uptime_seconds == 0

    @pytest.mark.asyncio
    async def test_agent_capabilities(self, test_agent):
        """测试Agent能力获取"""
        capabilities = await test_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert "test_capability" in capabilities
        assert "mock_task" in capabilities

    @pytest.mark.asyncio
    async def test_send_message(self, test_agent, sample_task_message):
        """测试消息发送"""
        await test_agent.send_message(sample_task_message)
        assert test_agent._message_count == 1
        assert not test_agent._message_queue.empty()

    @pytest.mark.asyncio
    async def test_queue_full_handling(self, test_agent):
        """测试队列满时的处理"""
        # 创建小队列的Agent
        small_queue_agent = TestAgent("small_queue", max_queue_size=2)

        # 填满队列
        for i in range(2):
            task = create_task_message("sender", "small_queue", "test", {})
            await small_queue_agent.send_message(task)

        # 尝试再发送一条消息应该抛出异常
        with pytest.raises(RuntimeError, match="Message queue full"):
            task = create_task_message("sender", "small_queue", "test", {})
            await small_queue_agent.send_message(task)


class TestBaseAgentLifecycle:
    """测试Agent生命周期管理"""

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, test_agent):
        """测试启动停止生命周期"""
        assert not test_agent.is_running

        # 启动Agent
        await test_agent.start()
        await asyncio.sleep(0.1)  # 让启动过程完成

        # 检查状态
        assert test_agent.is_running
        assert test_agent.status in [AgentStatus.IDLE, AgentStatus.BUSY]

        # 停止Agent
        await test_agent.stop()

        assert not test_agent.is_running
        assert test_agent.status == AgentStatus.STOPPED

    @pytest.mark.asyncio
    async def test_restart(self, test_agent):
        """测试重启功能"""
        # 启动和重启
        await test_agent.start()
        await asyncio.sleep(0.1)

        original_start_time = test_agent._start_time
        await test_agent.restart()
        await asyncio.sleep(0.1)

        # 重启后开始时间应该更新
        assert test_agent._start_time != original_start_time

        await test_agent.stop()

    @pytest.mark.asyncio
    async def test_duplicate_start_prevention(self, test_agent):
        """测试防止重复启动"""
        await test_agent.start()
        await asyncio.sleep(0.1)

        # 尝试再次启动应该被忽略
        await test_agent.start()  # 不应该抛出异常

        await test_agent.stop()


class TestBaseAgentMessageHandling:
    """测试消息处理功能"""

    @pytest.mark.asyncio
    async def test_task_message_processing(self, test_agent, sample_task_message):
        """测试任务消息处理"""
        # 直接调用处理方法
        await test_agent._handle_task_message(sample_task_message)

        # 检查任务是否被处理
        assert len(test_agent.processed_tasks) == 1
        processed_task = test_agent.processed_tasks[0]
        assert processed_task.id == sample_task_message.id
        assert processed_task.task_type == "mock_task"

    @pytest.mark.asyncio
    async def test_task_failure_handling(self, test_agent, sample_task_message):
        """测试任务失败处理"""
        test_agent.should_fail = True

        with pytest.raises(RuntimeError, match="Simulated task failure"):
            await test_agent._handle_task_message(sample_task_message)

        # 即使失败，状态也应该返回IDLE
        assert test_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_expired_task_handling(self, test_agent):
        """测试过期任务处理"""
        # 创建已过期的任务
        expired_task = create_task_message(
            sender_id="sender",
            recipient_id=test_agent.agent_id,
            task_type="test",
            task_data={}
        )
        expired_task.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        with pytest.raises(RuntimeError, match="Task message expired"):
            await test_agent._handle_task_message(expired_task)

    @pytest.mark.asyncio
    async def test_health_check_handling(self, test_agent):
        """测试健康检查消息处理"""
        health_check = HealthCheckMessage(
            sender_id="orchestrator",
            recipient_id=test_agent.agent_id
        )

        await test_agent._handle_health_check(health_check)

        # 检查是否发送了健康检查响应
        # 这里需要mock消息发送机制
        assert test_agent._message_count >= 1

    @pytest.mark.asyncio
    async def test_status_message_handling(self, test_agent):
        """测试状态消息处理"""
        status_msg = StatusMessage(
            sender_id="other_agent",
            status=AgentStatus.BUSY,
            load_percentage=75.0
        )

        # 应该能够处理状态消息而不抛出异常
        await test_agent._handle_status_message(status_msg)

    @pytest.mark.asyncio
    async def test_error_message_handling(self, test_agent):
        """测试错误消息处理"""
        error_msg = ErrorMessage(
            sender_id="other_agent",
            error_code="TEST_ERROR",
            error_message="Test error occurred"
        )

        await test_agent._handle_error_message(error_msg)
        assert test_agent._error_count == 1


class TestBaseAgentStatus:
    """测试Agent状态管理"""

    @pytest.mark.asyncio
    async def test_get_status(self, test_agent):
        """测试状态获取"""
        status = await test_agent.get_status()
        assert isinstance(status, StatusMessage)
        assert status.sender_id == test_agent.agent_id
        assert status.status == test_agent.status
        assert isinstance(status.capabilities, list)

    @pytest.mark.asyncio
    async def test_load_percentage_calculation(self, test_agent):
        """测试负载百分比计算"""
        initial_load = test_agent.load_percentage
        assert initial_load == 0.0

        # 模拟添加处理任务
        mock_task = Mock()
        test_agent._processing_tasks.add(mock_task)

        load_with_task = test_agent.load_percentage
        assert load_with_task > initial_load

        # 清理
        test_agent._processing_tasks.remove(mock_task)

    def test_uptime_calculation(self, test_agent):
        """测试运行时间计算"""
        assert test_agent.uptime_seconds == 0

        # 模拟启动时间
        test_agent._start_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        uptime = test_agent.uptime_seconds
        assert 25 <= uptime <= 35  # 允许一定误差


class TestBaseAgentHealthCheck:
    """测试健康检查功能"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, test_agent):
        """测试成功的健康检查"""
        # 初始化mock依赖
        await test_agent._initialize_dependencies()

        health_response = await test_agent.health_check()

        assert isinstance(health_response, ResponseMessage)
        assert health_response.sender_id == test_agent.agent_id
        assert health_response.success is True
        assert "uptime_seconds" in health_response.system_metrics
        assert "message_count" in health_response.system_metrics

    @pytest.mark.asyncio
    async def test_dashscope_health_check(self, test_agent):
        """测试DashScope健康检查"""
        test_agent.dashscope_client = Mock()

        health_status = await test_agent._check_dashscope_health()
        assert isinstance(health_status, bool)

    @pytest.mark.asyncio
    async def test_redis_health_check(self, test_agent):
        """测试Redis健康检查"""
        test_agent.redis_client = Mock()

        health_status = await test_agent._check_redis_health()
        assert isinstance(health_status, bool)


class TestBaseAgentConcurrency:
    """测试并发处理功能"""

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, test_agent):
        """测试并发任务处理"""
        test_agent.processing_delay = 0.1  # 添加小延迟

        # 创建多个任务
        tasks = []
        for i in range(3):
            task = create_task_message(
                sender_id="sender",
                recipient_id=test_agent.agent_id,
                task_type="concurrent_test",
                task_data={"index": i}
            )
            tasks.append(task)

        # 并发处理任务
        start_time = datetime.now(timezone.utc)
        await asyncio.gather(
            *[test_agent._handle_task_message(task) for task in tasks]
        )
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # 并发处理应该比顺序处理更快
        assert processing_time < 0.3  # 3个任务 * 0.1秒 = 0.3秒
        assert len(test_agent.processed_tasks) == 3

    @pytest.mark.asyncio
    async def test_max_concurrent_tasks_limit(self, test_agent):
        """测试最大并发任务限制"""
        test_agent.max_concurrent_tasks = 2
        test_agent.processing_delay = 0.2

        # 添加3个并发任务
        tasks = []
        for i in range(3):
            task_coro = test_agent._handle_task_message(
                create_task_message("sender", test_agent.agent_id, "test", {"i": i})
            )
            tasks.append(asyncio.create_task(task_coro))

        # 等待一段时间，检查负载
        await asyncio.sleep(0.05)
        assert len(test_agent._processing_tasks) <= test_agent.max_concurrent_tasks

        # 等待所有任务完成
        await asyncio.gather(*tasks)
        assert len(test_agent.processed_tasks) == 3


class TestBaseAgentIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_message_processing_workflow(self, test_agent):
        """测试完整的消息处理工作流"""
        # 启动Agent（模拟）
        await test_agent._initialize_dependencies()

        # 发送任务消息
        task = create_task_message(
            sender_id="test_sender",
            recipient_id=test_agent.agent_id,
            task_type="integration_test",
            task_data={"workflow": "complete"}
        )

        # 处理消息
        await test_agent._process_message(task)

        # 验证结果
        assert len(test_agent.processed_tasks) == 1
        assert test_agent._message_count == 1
        assert test_agent._task_count == 1

    @pytest.mark.asyncio
    async def test_error_recovery(self, test_agent):
        """测试错误恢复机制"""
        # 模拟处理错误
        test_agent.should_fail = True

        task = create_task_message("sender", test_agent.agent_id, "test", {})

        # 处理应该记录错误但不崩溃
        await test_agent._process_message(task)

        assert test_agent._error_count == 1
        assert test_agent._last_error is not None

        # 恢复正常处理
        test_agent.should_fail = False
        await test_agent._process_message(task)

        # 应该能够正常处理新任务
        assert len(test_agent.processed_tasks) == 1


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])