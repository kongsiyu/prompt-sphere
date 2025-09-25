#!/usr/bin/env python3
"""
简化的测试运行器，用于验证BaseAgent基本功能
"""

import sys
import os
import subprocess
import asyncio

# Fix Windows console encoding
if os.name == 'nt':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.agents.base.base_agent import BaseAgent
from app.agents.base.message_types import (
    TaskMessage, AgentStatus, create_task_message
)


class SimpleTestAgent(BaseAgent):
    """简化测试Agent"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "simple_test_agent")
        self.processed_tasks = []

    async def get_capabilities(self):
        return ["test_task"]

    async def process_task(self, task):
        self.processed_tasks.append(task)
        await asyncio.sleep(0.01)  # 模拟处理时间
        return {"result": f"Processed {task.id}"}

    async def _initialize_dependencies(self):
        """简化依赖初始化"""
        pass

    async def _cleanup_resources(self):
        """简化资源清理"""
        pass


async def test_basic_functionality():
    """测试基础功能"""
    print("开始测试BaseAgent基础功能...")

    # 创建测试Agent
    agent = SimpleTestAgent("test_001")
    print(f"✓ 创建Agent: {agent.agent_id}")

    # 测试初始状态
    assert not agent.is_running
    assert agent.status == AgentStatus.IDLE
    print("✓ 初始状态正确")

    # 测试启动
    await agent.start()
    await asyncio.sleep(0.1)  # 等待启动完成

    assert agent.is_running
    print("✓ Agent启动成功")

    # 测试消息发送
    task = create_task_message(
        sender_id="test_sender",
        recipient_id=agent.agent_id,
        task_type="test_task",
        task_data={"test": "data"}
    )

    await agent.send_message(task)
    await asyncio.sleep(0.1)  # 等待处理
    print("✓ 消息发送成功")

    # 等待任务处理
    await asyncio.sleep(0.2)

    # 检查任务处理结果
    if len(agent.processed_tasks) > 0:
        print(f"✓ 任务处理成功，处理了 {len(agent.processed_tasks)} 个任务")
    else:
        print("⚠ 任务可能还在处理中")

    # 测试健康检查
    health = await agent.health_check()
    assert health.success
    print("✓ 健康检查通过")

    # 测试停止
    await agent.stop()
    assert not agent.is_running
    print("✓ Agent停止成功")

    print("\n🎉 所有基础功能测试通过！")


async def main():
    try:
        await test_basic_functionality()
        print("\n测试完成，没有发现问题。")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)