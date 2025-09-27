#!/usr/bin/env python3
"""
PEQA简单基准测试
验证基准测试功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_basic_performance():
    """测试基本性能基准"""
    try:
        print("开始性能基准测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig

        # 创建Agent
        config = PEQAConfig()
        config.enable_parallel_processing = True
        agent = PEQAAgent(config)

        # 测试提示词
        test_prompts = [
            "写代码",
            "分析数据",
            "创建报告",
            "请编写一个Python函数计算平均值",
            "分析销售数据并生成可视化图表"
        ]

        print(f"测试 {len(test_prompts)} 个提示词")

        # 执行基准测试
        result = await agent.benchmark_performance(test_prompts)

        print("性能测试结果:")
        print(f"  总样本: {result.total_prompts}")
        print(f"  平均评分: {result.average_score:.3f}")
        print(f"  最高评分: {result.highest_score:.3f}")
        print(f"  最低评分: {result.lowest_score:.3f}")
        print(f"  处理时间: {result.total_processing_time_ms}ms")
        print(f"  平均时间: {result.average_processing_time_ms:.2f}ms")
        print(f"  吞吐量: {result.throughput:.2f} prompts/sec")

        if result.performance_metrics:
            success_rate = result.performance_metrics.get('success_rate', 0)
            error_count = result.performance_metrics.get('error_count', 0)
            print(f"  成功率: {success_rate:.3f}")
            print(f"  错误数: {error_count}")

        return True

    except Exception as e:
        print(f"性能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_quality_assessment():
    """测试质量评估"""
    try:
        print("\n开始质量评估测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig

        config = PEQAConfig()
        agent = PEQAAgent(config)

        # 不同质量的测试用例
        test_cases = [
            {
                "prompt": "写代码",
                "expected_quality": "very_poor"
            },
            {
                "prompt": "请创建一个Python函数计算数字平均值",
                "expected_quality": "fair"
            },
            {
                "prompt": "作为专业开发工程师，请编写一个完整的数据分析脚本，包含CSV读取、统计计算、可视化和错误处理。",
                "expected_quality": "good"
            }
        ]

        correct_predictions = 0

        for i, case in enumerate(test_cases):
            assessment = await agent.assess_prompt(case["prompt"])

            print(f"\n测试用例 {i+1}:")
            print(f"  提示词: {case['prompt'][:50]}...")
            print(f"  实际等级: {assessment.quality_level.value}")
            print(f"  期望等级: {case['expected_quality']}")
            print(f"  评分: {assessment.overall_score:.3f}")
            print(f"  改进建议: {len(assessment.improvement_suggestions)}项")

            # 简单验证
            if assessment.quality_level.value == case['expected_quality']:
                correct_predictions += 1
                print("  预测: 正确")
            else:
                print("  预测: 不符合期望")

        accuracy = correct_predictions / len(test_cases)
        print(f"\n质量评估准确率: {accuracy:.3f} ({correct_predictions}/{len(test_cases)})")

        return True

    except Exception as e:
        print(f"质量评估测试失败: {str(e)}")
        return False

async def test_batch_processing():
    """测试批量处理"""
    try:
        print("\n开始批量处理测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig
        from agents.peqa.types import BatchAssessmentRequest

        config = PEQAConfig()
        config.enable_parallel_processing = True
        agent = PEQAAgent(config)

        # 批量测试数据
        batch_prompts = [
            "创建Web应用",
            "分析用户数据",
            "优化系统性能",
            "设计数据库架构",
            "实现API接口"
        ]

        request = BatchAssessmentRequest(
            prompts=batch_prompts,
            parallel_processing=True,
            include_summary=True
        )

        result = await agent.batch_assess(request)

        print("批量处理结果:")
        print(f"  请求ID: {result['request_id']}")
        print(f"  成功处理: {result['success_count']}/{result['total_count']}")
        print(f"  成功率: {result['success_rate']:.3f}")
        print(f"  处理时间: {result['processing_time_ms']}ms")

        if 'summary' in result:
            summary = result['summary']
            print(f"  平均评分: {summary['average_score']:.3f}")
            print(f"  最高评分: {summary['highest_score']:.3f}")
            print(f"  最低评分: {summary['lowest_score']:.3f}")

            # 显示质量分布
            distribution = summary.get('quality_distribution', {})
            if distribution:
                print("  质量分布:")
                for level, count in distribution.items():
                    print(f"    {level}: {count}")

        return True

    except Exception as e:
        print(f"批量处理测试失败: {str(e)}")
        return False

async def test_health_check():
    """测试健康检查"""
    try:
        print("\n开始健康检查测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig

        config = PEQAConfig()
        agent = PEQAAgent(config)

        health_result = await agent.health_check()

        print("健康检查结果:")
        print(f"  状态: {health_result['status']}")

        if health_result['status'] == 'healthy':
            components = health_result.get('components', {})
            for component, status in components.items():
                print(f"  {component}: {status}")

            test_result = health_result.get('test_result', {})
            if test_result:
                print(f"  测试评分: {test_result.get('test_score', 0):.3f}")
                print(f"  测试耗时: {test_result.get('processing_time_ms', 0)}ms")

            stats = health_result.get('stats', {})
            if stats:
                print(f"  评估次数: {stats.get('total_assessments', 0)}")
                print(f"  平均评分: {stats.get('average_score', 0):.3f}")

        return health_result['status'] == 'healthy'

    except Exception as e:
        print(f"健康检查失败: {str(e)}")
        return False

async def test_capabilities():
    """测试Agent能力"""
    try:
        print("\n开始能力测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig

        config = PEQAConfig()
        agent = PEQAAgent(config)

        capabilities = await agent.get_capabilities()

        print("Agent能力列表:")
        for i, capability in enumerate(capabilities, 1):
            print(f"  {i}. {capability}")

        # 测试任务处理
        test_task = {
            'type': 'assess_prompt',
            'prompt': '请编写一个Python函数',
            'options': {}
        }

        task_result = await agent.process_task(test_task)

        print("\n任务处理测试:")
        print(f"  成功: {task_result['success']}")
        if task_result['success']:
            result = task_result['result']
            print(f"  评分: {result['overall_score']:.3f}")
            print(f"  等级: {result['quality_level']}")

        return True

    except Exception as e:
        print(f"能力测试失败: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("启动PEQA基准测试\n")

    # 运行各项测试
    performance_ok = await test_basic_performance()
    quality_ok = await test_quality_assessment()
    batch_ok = await test_batch_processing()
    health_ok = await test_health_check()
    capabilities_ok = await test_capabilities()

    # 总结
    print("\n" + "="*50)
    print("基准测试总结")
    print("="*50)
    print(f"性能基准测试: {'通过' if performance_ok else '失败'}")
    print(f"质量评估测试: {'通过' if quality_ok else '失败'}")
    print(f"批量处理测试: {'通过' if batch_ok else '失败'}")
    print(f"健康检查测试: {'通过' if health_ok else '失败'}")
    print(f"能力测试: {'通过' if capabilities_ok else '失败'}")

    all_passed = all([performance_ok, quality_ok, batch_ok, health_ok, capabilities_ok])
    print(f"\n整体结果: {'全部通过' if all_passed else '部分失败'}")

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)