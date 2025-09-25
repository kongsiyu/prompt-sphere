"""
简化的BaseAgent测试，避免复杂的异步和生命周期问题
"""

import pytest
import asyncio
from unittest.mock import Mock
import sys
import os

# 设置编码
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.agents.base.base_agent import BaseAgent
from app.agents.base.message_types import (
    TaskMessage, AgentStatus, create_task_message
)


class SimpleTestAgent(BaseAgent):
    """简化的测试Agent，避免复杂的依赖和生命周期"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "simple_test")
        self.processed_tasks = []

    async def get_capabilities(self):
        return ["test_task"]

    async def process_task(self, task):
        await asyncio.sleep(0.01)  # 模拟很短的处理时间
        self.processed_tasks.append(task)
        return {"result": f"Task {task.id} completed"}

    async def _initialize_dependencies(self):
        self.dashscope_client = Mock()
        self.redis_client = Mock()

    async def _cleanup_resources(self):
        pass


class TestSimpleAgent:
    """简化的Agent测试"""

    def test_basic_properties(self):
        """测试基础属性"""
        agent = SimpleTestAgent("test_001")
        assert agent.agent_id == "test_001"
        assert agent.agent_type == "simple_test"
        assert not agent.is_running
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_capabilities(self):
        """测试能力获取"""
        agent = SimpleTestAgent("test_002")
        caps = await agent.get_capabilities()
        assert "test_task" in caps

    @pytest.mark.asyncio
    async def test_direct_task_processing(self):
        """测试直接任务处理（不通过消息队列）"""
        agent = SimpleTestAgent("test_003")

        task = create_task_message(
            sender_id="test",
            recipient_id="test_003",
            task_type="test_task",
            task_data={"test": "data"}
        )

        # 直接调用处理方法
        await agent._handle_task_message(task)

        assert len(agent.processed_tasks) == 1
        assert agent.processed_tasks[0].id == task.id

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        agent = SimpleTestAgent("test_004")
        await agent._initialize_dependencies()

        health = await agent.health_check()
        assert health.success
        assert "uptime_seconds" in health.system_metrics

    @pytest.mark.asyncio
    async def test_simple_lifecycle(self):
        """测试简化的生命周期，快速启动停止"""
        agent = SimpleTestAgent("test_005")

        # 启动
        await agent.start()
        await asyncio.sleep(0.05)  # 很短的等待

        assert agent.is_running
        assert agent._start_time is not None

        # 立即停止
        await agent.stop()

        assert not agent.is_running
        assert agent.status == AgentStatus.STOPPED

    @pytest.mark.asyncio
    async def test_message_queue(self):
        """测试消息队列基础功能"""
        agent = SimpleTestAgent("test_006")

        task = create_task_message(
            sender_id="test",
            recipient_id="test_006",
            task_type="test_task",
            task_data={}
        )

        # 发送消息到队列
        await agent.send_message(task)

        assert not agent._message_queue.empty()
        assert agent._message_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])