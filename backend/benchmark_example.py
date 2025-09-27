#!/usr/bin/env python3
"""
PEQA基准测试示例

演示如何使用PEQA的基准测试功能
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def run_basic_benchmark():
    """运行基本基准测试"""
    try:
        print("=== PEQA基准测试示例 ===\n")

        # 导入必要的模块
        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig
        from agents.peqa.BenchmarkRunner import BenchmarkRunner, BenchmarkConfig
        from agents.peqa.benchmarks.benchmark_datasets import BenchmarkDatasets
        from agents.peqa.types import BenchmarkType

        # 创建PEQA Agent
        config = PEQAConfig()
        config.enable_parallel_processing = True
        config.batch_size = 3

        agent = PEQAAgent(config)
        benchmark_runner = BenchmarkRunner(agent, config)

        print("✅ PEQA Agent和基准测试运行器创建成功\n")

        # 1. 性能基准测试
        print("🚀 开始性能基准测试...")
        performance_prompts = BenchmarkDatasets.get_performance_test_prompts()[:10]  # 使用前10个

        benchmark_config = BenchmarkConfig(
            test_type=BenchmarkType.PERFORMANCE,
            parallel_workers=3,
            benchmark_rounds=2,
            warmup_rounds=1
        )

        performance_result = await benchmark_runner.run_performance_benchmark(
            performance_prompts, benchmark_config
        )

        print(f"✅ 性能测试完成:")
        print(f"   - 测试样本: {performance_result.total_prompts}")
        print(f"   - 平均吞吐量: {performance_result.throughput:.2f} prompts/sec")
        print(f"   - 平均处理时间: {performance_result.average_processing_time_ms:.2f}ms")
        print(f"   - 总处理时间: {performance_result.total_processing_time_ms}ms")

        if performance_result.performance_metrics:
            print(f"   - 内存使用: {performance_result.performance_metrics.get('memory_used_mb', 0):.2f}MB")
            print(f"   - 并行工作者: {performance_result.performance_metrics.get('parallel_workers', 0)}")

        print()

        # 2. 质量基准测试
        print("📊 开始质量基准测试...")
        quality_test_cases = BenchmarkDatasets.get_quality_test_cases()

        quality_result = await benchmark_runner.run_quality_benchmark(quality_test_cases)

        print(f"✅ 质量测试完成:")
        print(f"   - 测试用例: {quality_result.total_prompts}")
        print(f"   - 平均评分: {quality_result.average_score:.3f}")
        print(f"   - 最高评分: {quality_result.highest_score:.3f}")
        print(f"   - 最低评分: {quality_result.lowest_score:.3f}")

        if quality_result.performance_metrics:
            accuracy = quality_result.performance_metrics.get('assessment_accuracy', 0)
            print(f"   - 评估准确性: {accuracy:.3f}")

        print()

        # 3. 可扩展性基准测试
        print("📈 开始可扩展性基准测试...")
        base_prompts = BenchmarkDatasets.get_scalability_test_prompts()
        scale_factors = [1, 2, 3]  # 测试1x, 2x, 3x规模

        scalability_results = await benchmark_runner.run_scalability_benchmark(
            base_prompts, scale_factors
        )

        print(f"✅ 可扩展性测试完成:")
        for scale_name, result in scalability_results.items():
            scale_factor = result.performance_metrics['scale_factor']
            efficiency = result.performance_metrics.get('efficiency_ratio', 0)
            print(f"   - {scale_name}: 吞吐量 {result.throughput:.2f}, 效率比 {efficiency:.3f}")

        print()

        # 4. 准确性基准测试
        print("🎯 开始准确性基准测试...")
        gold_standard = BenchmarkDatasets.get_accuracy_gold_standard()

        accuracy_result = await benchmark_runner.run_accuracy_benchmark(gold_standard)

        print(f"✅ 准确性测试完成:")
        print(f"   - 黄金标准样本: {accuracy_result.total_prompts}")
        print(f"   - 平均评分: {accuracy_result.average_score:.3f}")

        if accuracy_result.performance_metrics:
            mae = accuracy_result.performance_metrics.get('overall_score_mae', 0)
            level_accuracy = accuracy_result.performance_metrics.get('quality_level_accuracy', 0)
            print(f"   - 评分误差(MAE): {mae:.3f}")
            print(f"   - 等级准确率: {level_accuracy:.3f}")

        print()

        # 5. 生成综合报告
        print("📝 生成基准测试报告...")
        all_results = {
            "性能测试": performance_result,
            "质量测试": quality_result,
            "准确性测试": accuracy_result,
            **{f"可扩展性测试_{k}": v for k, v in scalability_results.items()}
        }

        report = await benchmark_runner.generate_benchmark_report(all_results)

        # 保存报告
        report_file = f"peqa_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 报告已保存到: {report_file}")

        # 6. 显示报告摘要
        print("\n" + "="*60)
        print("📊 基准测试摘要")
        print("="*60)
        print(f"性能吞吐量: {performance_result.throughput:.2f} prompts/sec")
        print(f"质量评估准确性: {quality_result.performance_metrics.get('assessment_accuracy', 0):.3f}")
        print(f"系统响应时间: {performance_result.average_processing_time_ms:.2f}ms")
        print(f"可扩展性效率: {scalability_results.get('scale_3x', scalability_results[list(scalability_results.keys())[-1]]).performance_metrics.get('efficiency_ratio', 0):.3f}")

        return True

    except Exception as e:
        print(f"❌ 基准测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_stress_test():
    """运行压力测试"""
    try:
        print("\n🔥 开始压力测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig
        from agents.peqa.benchmarks.benchmark_datasets import BenchmarkDatasets

        # 创建高并发配置
        config = PEQAConfig()
        config.enable_parallel_processing = True
        config.batch_size = 10

        agent = PEQAAgent(config)

        # 生成大量测试数据
        stress_prompts = BenchmarkDatasets.get_stress_test_prompts(50)  # 50个提示词

        print(f"生成 {len(stress_prompts)} 个测试提示词")

        start_time = datetime.now()

        # 执行压力测试
        results = await agent.benchmark_performance(stress_prompts)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"✅ 压力测试完成:")
        print(f"   - 处理时间: {duration:.2f}秒")
        print(f"   - 吞吐量: {results.throughput:.2f} prompts/sec")
        print(f"   - 成功率: {results.performance_metrics.get('success_rate', 0):.3f}")
        print(f"   - 错误数量: {results.performance_metrics.get('error_count', 0)}")

        return True

    except Exception as e:
        print(f"❌ 压力测试失败: {str(e)}")
        return False

async def run_edge_case_test():
    """运行边界情况测试"""
    try:
        print("\n🧪 开始边界情况测试...")

        from agents.peqa.PEQAAgent import PEQAAgent
        from agents.peqa.config import PEQAConfig
        from agents.peqa.benchmarks.benchmark_datasets import BenchmarkDatasets

        config = PEQAConfig()
        agent = PEQAAgent(config)

        edge_cases = BenchmarkDatasets.get_edge_case_prompts()

        print(f"测试 {len(edge_cases)} 个边界情况")

        success_count = 0
        error_count = 0

        for i, prompt in enumerate(edge_cases):
            try:
                assessment = await agent.assess_prompt(prompt)
                success_count += 1
                print(f"✅ 边界情况 {i+1}: 评分 {assessment.overall_score:.3f}")
            except Exception as e:
                error_count += 1
                print(f"❌ 边界情况 {i+1}: {str(e)[:50]}...")

        print(f"\n边界情况测试结果:")
        print(f"   - 成功: {success_count}/{len(edge_cases)}")
        print(f"   - 失败: {error_count}/{len(edge_cases)}")
        print(f"   - 成功率: {success_count/len(edge_cases):.3f}")

        return True

    except Exception as e:
        print(f"❌ 边界情况测试失败: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("🚀 启动PEQA完整基准测试套件\n")

    # 运行基本基准测试
    basic_success = await run_basic_benchmark()

    # 运行压力测试
    stress_success = await run_stress_test()

    # 运行边界情况测试
    edge_success = await run_edge_case_test()

    # 总结
    print("\n" + "="*60)
    print("🎯 基准测试总结")
    print("="*60)
    print(f"基本基准测试: {'✅ 通过' if basic_success else '❌ 失败'}")
    print(f"压力测试: {'✅ 通过' if stress_success else '❌ 失败'}")
    print(f"边界情况测试: {'✅ 通过' if edge_success else '❌ 失败'}")

    overall_success = all([basic_success, stress_success, edge_success])
    print(f"\n🏆 整体结果: {'✅ 全部通过' if overall_success else '❌ 部分失败'}")

    return overall_success

if __name__ == "__main__":
    # 运行完整基准测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)