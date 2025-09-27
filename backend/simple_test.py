#!/usr/bin/env python3
"""
PEQA简单测试
验证基本导入和功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_basic():
    """基本测试"""
    try:
        print("测试PEQA导入...")

        # 测试类型导入
        from agents.peqa.types import QualityDimension, QualityLevel
        print("类型导入成功")

        # 测试配置导入
        from agents.peqa.config import PEQAConfig
        print("配置导入成功")

        # 创建配置
        config = PEQAConfig()
        print("配置创建成功")

        # 测试Agent导入
        from agents.peqa.PEQAAgent import PEQAAgent
        print("Agent导入成功")

        # 创建Agent
        agent = PEQAAgent(config)
        print("Agent创建成功")

        # 测试简单评估
        test_prompt = "请创建一个Python函数计算平均值"
        print(f"测试提示词: {test_prompt}")

        assessment = await agent.assess_prompt(test_prompt)
        print("评估完成")

        print(f"总体评分: {assessment.overall_score:.2f}")
        print(f"质量等级: {assessment.quality_level.value}")
        print(f"维度数量: {len(assessment.dimension_scores)}")
        print(f"改进建议: {len(assessment.improvement_suggestions)}")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始PEQA简单测试")
    success = asyncio.run(test_basic())
    if success:
        print("测试通过")
    else:
        print("测试失败")
    sys.exit(0 if success else 1)