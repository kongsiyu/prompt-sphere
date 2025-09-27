#!/usr/bin/env python3
"""
PEQA基本功能测试
验证PEQA Agent的基本导入和功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_peqa_import():
    """测试PEQA模块导入"""
    try:
        print("🔍 测试PEQA模块导入...")

        # 测试基本类型导入
        from agents.peqa.types import (
            QualityDimension, QualityLevel, QualityScore,
            QualityAssessment, Improvement
        )
        print("✅ 基本类型导入成功")

        # 测试配置导入
        from agents.peqa.config import PEQAConfig
        print("✅ 配置模块导入成功")

        # 测试核心组件导入
        from agents.peqa.QualityScorer import QualityScorer
        from agents.peqa.ImprovementEngine import ImprovementEngine
        from agents.peqa.ReportGenerator import ReportGenerator
        print("✅ 核心组件导入成功")

        # 测试主Agent导入
        from agents.peqa.PEQAAgent import PEQAAgent
        print("✅ PEQAAgent导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

async def test_peqa_basic_functionality():
    """测试PEQA基本功能"""
    try:
        print("\n🔍 测试PEQA基本功能...")

        from agents.peqa.config import PEQAConfig
        from agents.peqa.PEQAAgent import PEQAAgent

        # 创建配置
        config = PEQAConfig()
        print("✅ 配置创建成功")

        # 创建Agent
        agent = PEQAAgent(config)
        print("✅ PEQAAgent创建成功")

        # 测试简单评估
        test_prompt = "请为我创建一个Python函数，计算两个数字的平均值。"

        print(f"📝 测试提示词: {test_prompt}")

        # 执行评估
        assessment = await agent.assess_prompt(test_prompt)
        print("✅ 提示词评估成功")

        # 显示结果
        print(f"📊 评估结果:")
        print(f"   总体评分: {assessment.overall_score:.2f}")
        print(f"   质量等级: {assessment.quality_level.value}")
        print(f"   置信度: {assessment.confidence_level:.2f}")
        print(f"   处理时间: {assessment.processing_time_ms}ms")

        # 显示维度评分
        print(f"📈 各维度评分:")
        for dimension, score in assessment.dimension_scores.items():
            print(f"   {dimension.value}: {score.score:.2f}")

        # 显示优势和不足
        if assessment.strengths:
            print(f"💪 优势 ({len(assessment.strengths)}项):")
            for strength in assessment.strengths[:3]:  # 只显示前3项
                print(f"   - {strength}")

        if assessment.weaknesses:
            print(f"⚠️  改进空间 ({len(assessment.weaknesses)}项):")
            for weakness in assessment.weaknesses[:3]:  # 只显示前3项
                print(f"   - {weakness}")

        # 显示改进建议
        if assessment.improvement_suggestions:
            print(f"💡 改进建议 ({len(assessment.improvement_suggestions)}项):")
            for suggestion in assessment.improvement_suggestions[:3]:  # 只显示前3项
                print(f"   - {suggestion.title} (优先级: {suggestion.priority.value})")

        return True

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_peqa_config():
    """测试PEQA配置"""
    try:
        print("\n🔍 测试PEQA配置...")

        from agents.peqa.config import PEQAConfig, get_default_config

        # 测试默认配置
        default_config = get_default_config()
        print("✅ 默认配置获取成功")

        # 测试配置验证
        validation_result = default_config.validate_configuration()
        print(f"📋 配置验证结果: {'✅ 有效' if validation_result['valid'] else '❌ 无效'}")

        if validation_result['issues']:
            print("⚠️  配置问题:")
            for issue in validation_result['issues']:
                print(f"   - {issue}")

        if validation_result['warnings']:
            print("⚠️  配置警告:")
            for warning in validation_result['warnings']:
                print(f"   - {warning}")

        # 显示关键配置
        print(f"📊 关键配置:")
        print(f"   模型名称: {default_config.model_name}")
        print(f"   并行处理: {default_config.enable_parallel_processing}")
        print(f"   批处理大小: {default_config.batch_size}")
        print(f"   最大提示词长度: {default_config.max_prompt_length}")

        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

async def test_peqa_health_check():
    """测试PEQA健康检查"""
    try:
        print("\n🔍 测试PEQA健康检查...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig

        config = PEQAConfig()
        agent = PEQAAgent(config)

        # 执行健康检查
        health_result = await agent.health_check()
        print(f"🏥 健康检查状态: {health_result['status']}")

        if health_result['status'] == 'healthy':
            print("✅ PEQA Agent运行正常")

            # 显示组件状态
            components = health_result.get('components', {})
            for component, status in components.items():
                print(f"   📦 {component}: {status}")

            # 显示测试结果
            test_result = health_result.get('test_result', {})
            if test_result:
                print(f"📊 测试评分: {test_result.get('test_score', 0):.2f}")
                print(f"⏱️  测试耗时: {test_result.get('processing_time_ms', 0)}ms")

            # 显示统计信息
            stats = health_result.get('stats', {})
            if stats:
                print(f"📈 统计信息:")
                print(f"   总评估次数: {stats.get('total_assessments', 0)}")
                print(f"   平均评分: {stats.get('average_score', 0):.2f}")
        else:
            print(f"❌ PEQA Agent不健康: {health_result.get('error', '未知错误')}")

        return health_result['status'] == 'healthy'

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始PEQA基本功能测试\n")

    # 测试导入
    import_success = await test_peqa_import()

    if not import_success:
        print("\n❌ 导入测试失败，无法继续其他测试")
        return False

    # 测试配置
    config_success = await test_peqa_config()

    # 测试基本功能
    functionality_success = await test_peqa_basic_functionality()

    # 测试健康检查
    health_success = await test_peqa_health_check()

    # 总结
    print(f"\n📊 测试总结:")
    print(f"   导入测试: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f"   配置测试: {'✅ 通过' if config_success else '❌ 失败'}")
    print(f"   功能测试: {'✅ 通过' if functionality_success else '❌ 失败'}")
    print(f"   健康检查: {'✅ 通过' if health_success else '❌ 失败'}")

    all_success = all([import_success, config_success, functionality_success, health_success])
    print(f"\n🎯 整体结果: {'✅ 全部通过' if all_success else '❌ 部分失败'}")

    return all_success

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)