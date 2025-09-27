"""
PEQA基准测试运行器

提供多种类型的基准测试：性能测试、质量测试、可扩展性测试、准确性测试
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from .types import BenchmarkResult, BenchmarkType, QualityAssessment
from .config import PEQAConfig


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    test_type: BenchmarkType
    sample_size: int = 100
    parallel_workers: int = 5
    timeout_seconds: int = 300
    memory_limit_mb: int = 1024
    warmup_rounds: int = 3
    benchmark_rounds: int = 5
    save_results: bool = True
    compare_baseline: bool = False
    baseline_file: Optional[str] = None


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, peqa_agent, config: PEQAConfig):
        """初始化基准测试运行器"""
        self.peqa_agent = peqa_agent
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def run_performance_benchmark(self, prompts: List[str],
                                      benchmark_config: BenchmarkConfig) -> BenchmarkResult:
        """
        运行性能基准测试

        测试指标：
        - 吞吐量 (prompts/second)
        - 平均响应时间
        - 内存使用率
        - CPU使用率
        - 并发处理能力
        """
        self.logger.info(f"开始性能基准测试，样本数量: {len(prompts)}")

        # 性能监控
        start_memory = psutil.virtual_memory().used
        start_cpu_percent = psutil.cpu_percent()

        # 预热
        await self._warmup(prompts[:benchmark_config.warmup_rounds])

        # 多轮测试
        all_results = []

        for round_num in range(benchmark_config.benchmark_rounds):
            self.logger.info(f"执行第 {round_num + 1} 轮性能测试")

            round_start = time.time()

            # 并行处理
            if benchmark_config.parallel_workers > 1:
                results = await self._parallel_assess(prompts, benchmark_config.parallel_workers)
            else:
                results = await self._sequential_assess(prompts)

            round_time = time.time() - round_start

            # 计算性能指标
            valid_results = [r for r in results if isinstance(r, QualityAssessment)]
            throughput = len(valid_results) / round_time if round_time > 0 else 0

            round_metrics = {
                'round': round_num + 1,
                'throughput': throughput,
                'total_time': round_time,
                'success_rate': len(valid_results) / len(prompts),
                'avg_processing_time': sum(r.processing_time_ms for r in valid_results) / len(valid_results) if valid_results else 0
            }

            all_results.append(round_metrics)

        # 汇总结果
        avg_throughput = sum(r['throughput'] for r in all_results) / len(all_results)
        avg_processing_time = sum(r['avg_processing_time'] for r in all_results) / len(all_results)

        # 资源使用情况
        end_memory = psutil.virtual_memory().used
        memory_used_mb = (end_memory - start_memory) / 1024 / 1024

        performance_metrics = {
            'average_throughput': avg_throughput,
            'average_processing_time_ms': avg_processing_time,
            'memory_used_mb': memory_used_mb,
            'cpu_usage_percent': psutil.cpu_percent() - start_cpu_percent,
            'parallel_workers': benchmark_config.parallel_workers,
            'round_details': all_results
        }

        return BenchmarkResult(
            benchmark_type=BenchmarkType.PERFORMANCE,
            total_prompts=len(prompts),
            average_score=0.0,  # 性能测试不关注评分
            highest_score=0.0,
            lowest_score=0.0,
            total_processing_time_ms=int(sum(r['total_time'] * 1000 for r in all_results)),
            average_processing_time_ms=avg_processing_time,
            throughput=avg_throughput,
            performance_metrics=performance_metrics
        )

    async def run_quality_benchmark(self, test_cases: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        运行质量基准测试

        测试指标：
        - 评分准确性
        - 维度评分一致性
        - 改进建议质量
        - 置信度校准
        """
        self.logger.info(f"开始质量基准测试，测试用例数量: {len(test_cases)}")

        assessments = []
        accuracy_scores = []

        for test_case in test_cases:
            prompt = test_case['prompt']
            expected_score = test_case.get('expected_score')
            expected_level = test_case.get('expected_level')

            try:
                assessment = await self.peqa_agent.assess_prompt(prompt)
                assessments.append(assessment)

                # 计算准确性
                if expected_score is not None:
                    accuracy = 1 - abs(assessment.overall_score - expected_score)
                    accuracy_scores.append(accuracy)

                # 验证质量等级预测
                if expected_level and assessment.quality_level.value != expected_level:
                    self.logger.warning(f"质量等级预测不匹配: 预期 {expected_level}, 实际 {assessment.quality_level.value}")

            except Exception as e:
                self.logger.error(f"质量测试失败: {str(e)}")
                continue

        # 计算质量指标
        if assessments:
            scores = [a.overall_score for a in assessments]
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0

            quality_metrics = {
                'assessment_accuracy': avg_accuracy,
                'score_variance': self._calculate_variance(scores),
                'confidence_calibration': self._calculate_confidence_calibration(assessments),
                'dimension_consistency': self._calculate_dimension_consistency(assessments),
                'improvement_coverage': self._calculate_improvement_coverage(assessments)
            }
        else:
            quality_metrics = {}

        return BenchmarkResult(
            benchmark_type=BenchmarkType.QUALITY,
            total_prompts=len(test_cases),
            average_score=sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0,
            highest_score=max(a.overall_score for a in assessments) if assessments else 0,
            lowest_score=min(a.overall_score for a in assessments) if assessments else 0,
            total_processing_time_ms=sum(a.processing_time_ms for a in assessments),
            average_processing_time_ms=sum(a.processing_time_ms for a in assessments) / len(assessments) if assessments else 0,
            throughput=0,  # 质量测试不关注吞吐量
            individual_results=assessments,
            performance_metrics=quality_metrics
        )

    async def run_scalability_benchmark(self, base_prompts: List[str],
                                      scale_factors: List[int]) -> Dict[str, BenchmarkResult]:
        """
        运行可扩展性基准测试

        测试不同数据规模下的性能表现
        """
        self.logger.info(f"开始可扩展性基准测试，规模因子: {scale_factors}")

        results = {}

        for scale_factor in scale_factors:
            # 生成对应规模的测试数据
            scaled_prompts = (base_prompts * scale_factor)[:scale_factor * len(base_prompts)]

            self.logger.info(f"测试规模 {scale_factor}x ({len(scaled_prompts)} 个提示词)")

            start_time = time.time()

            try:
                # 使用当前最优配置进行测试
                benchmark_config = BenchmarkConfig(
                    test_type=BenchmarkType.SCALABILITY,
                    parallel_workers=self.config.batch_size,
                    benchmark_rounds=1  # 可扩展性测试只需一轮
                )

                result = await self.run_performance_benchmark(scaled_prompts, benchmark_config)

                # 添加可扩展性特定指标
                result.performance_metrics.update({
                    'scale_factor': scale_factor,
                    'total_prompts': len(scaled_prompts),
                    'efficiency_ratio': result.throughput / scale_factor if scale_factor > 0 else 0
                })

                results[f"scale_{scale_factor}x"] = result

            except Exception as e:
                self.logger.error(f"可扩展性测试失败 (规模 {scale_factor}x): {str(e)}")
                continue

        return results

    async def run_accuracy_benchmark(self, gold_standard_dataset: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        运行准确性基准测试

        使用黄金标准数据集验证评估准确性
        """
        self.logger.info(f"开始准确性基准测试，黄金标准数据集大小: {len(gold_standard_dataset)}")

        assessments = []
        accuracy_metrics = []

        for item in gold_standard_dataset:
            prompt = item['prompt']
            ground_truth = item['ground_truth']

            try:
                assessment = await self.peqa_agent.assess_prompt(prompt)
                assessments.append(assessment)

                # 计算各种准确性指标
                metrics = self._calculate_accuracy_metrics(assessment, ground_truth)
                accuracy_metrics.append(metrics)

            except Exception as e:
                self.logger.error(f"准确性测试失败: {str(e)}")
                continue

        # 汇总准确性指标
        if accuracy_metrics:
            avg_metrics = {
                'overall_score_mae': sum(m['overall_score_mae'] for m in accuracy_metrics) / len(accuracy_metrics),
                'dimension_score_mae': sum(m['dimension_score_mae'] for m in accuracy_metrics) / len(accuracy_metrics),
                'quality_level_accuracy': sum(m['quality_level_correct'] for m in accuracy_metrics) / len(accuracy_metrics),
                'improvement_relevance': sum(m['improvement_relevance'] for m in accuracy_metrics) / len(accuracy_metrics)
            }
        else:
            avg_metrics = {}

        return BenchmarkResult(
            benchmark_type=BenchmarkType.ACCURACY,
            total_prompts=len(gold_standard_dataset),
            average_score=sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0,
            highest_score=max(a.overall_score for a in assessments) if assessments else 0,
            lowest_score=min(a.overall_score for a in assessments) if assessments else 0,
            total_processing_time_ms=sum(a.processing_time_ms for a in assessments),
            average_processing_time_ms=sum(a.processing_time_ms for a in assessments) / len(assessments) if assessments else 0,
            throughput=0,
            individual_results=assessments,
            performance_metrics=avg_metrics
        )

    async def _warmup(self, warmup_prompts: List[str]):
        """预热系统"""
        self.logger.info("系统预热中...")
        for prompt in warmup_prompts:
            try:
                await self.peqa_agent.assess_prompt(prompt)
            except:
                pass  # 预热阶段忽略错误

    async def _parallel_assess(self, prompts: List[str], workers: int) -> List[Any]:
        """并行评估"""
        semaphore = asyncio.Semaphore(workers)

        async def assess_with_semaphore(prompt):
            async with semaphore:
                return await self.peqa_agent.assess_prompt(prompt)

        tasks = [assess_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _sequential_assess(self, prompts: List[str]) -> List[Any]:
        """串行评估"""
        results = []
        for prompt in prompts:
            try:
                result = await self.peqa_agent.assess_prompt(prompt)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def _calculate_variance(self, scores: List[float]) -> float:
        """计算方差"""
        if len(scores) < 2:
            return 0.0
        mean = sum(scores) / len(scores)
        return sum((x - mean) ** 2 for x in scores) / len(scores)

    def _calculate_confidence_calibration(self, assessments: List[QualityAssessment]) -> float:
        """计算置信度校准"""
        # 简化实现：检查高置信度预测的准确性
        high_confidence = [a for a in assessments if a.confidence_level > 0.8]
        if not high_confidence:
            return 0.0

        # 这里应该有更复杂的校准逻辑
        return len(high_confidence) / len(assessments)

    def _calculate_dimension_consistency(self, assessments: List[QualityAssessment]) -> float:
        """计算维度一致性"""
        if not assessments:
            return 0.0

        # 检查各维度评分是否与总体评分一致
        consistency_scores = []
        for assessment in assessments:
            dimension_avg = sum(score.score for score in assessment.dimension_scores.values()) / len(assessment.dimension_scores)
            consistency = 1 - abs(assessment.overall_score - dimension_avg)
            consistency_scores.append(consistency)

        return sum(consistency_scores) / len(consistency_scores)

    def _calculate_improvement_coverage(self, assessments: List[QualityAssessment]) -> float:
        """计算改进建议覆盖率"""
        if not assessments:
            return 0.0

        # 检查低分提示词是否都有改进建议
        low_score_assessments = [a for a in assessments if a.overall_score < 0.7]
        if not low_score_assessments:
            return 1.0

        with_suggestions = [a for a in low_score_assessments if a.improvement_suggestions]
        return len(with_suggestions) / len(low_score_assessments)

    def _calculate_accuracy_metrics(self, assessment: QualityAssessment,
                                  ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """计算准确性指标"""
        metrics = {}

        # 总体评分准确性 (MAE: Mean Absolute Error)
        if 'overall_score' in ground_truth:
            metrics['overall_score_mae'] = abs(assessment.overall_score - ground_truth['overall_score'])

        # 维度评分准确性
        if 'dimension_scores' in ground_truth:
            dimension_errors = []
            for dim, expected_score in ground_truth['dimension_scores'].items():
                if dim in assessment.dimension_scores:
                    actual_score = assessment.dimension_scores[dim].score
                    dimension_errors.append(abs(actual_score - expected_score))
            metrics['dimension_score_mae'] = sum(dimension_errors) / len(dimension_errors) if dimension_errors else 0

        # 质量等级准确性
        if 'quality_level' in ground_truth:
            metrics['quality_level_correct'] = 1 if assessment.quality_level.value == ground_truth['quality_level'] else 0

        # 改进建议相关性
        if 'expected_issues' in ground_truth:
            suggested_categories = [imp.category.value for imp in assessment.improvement_suggestions]
            expected_issues = ground_truth['expected_issues']
            relevance = len(set(suggested_categories) & set(expected_issues)) / len(expected_issues) if expected_issues else 0
            metrics['improvement_relevance'] = relevance

        return metrics

    async def generate_benchmark_report(self, results: Dict[str, BenchmarkResult]) -> str:
        """生成基准测试报告"""
        report = "# PEQA基准测试报告\n\n"
        report += f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for test_name, result in results.items():
            report += f"## {test_name}\n\n"
            report += f"- 测试类型: {result.benchmark_type.value}\n"
            report += f"- 测试样本: {result.total_prompts}\n"
            report += f"- 平均评分: {result.average_score:.3f}\n"
            report += f"- 处理时间: {result.total_processing_time_ms}ms\n"
            report += f"- 吞吐量: {result.throughput:.2f} prompts/sec\n"

            if result.performance_metrics:
                report += "### 详细指标\n"
                for key, value in result.performance_metrics.items():
                    report += f"- {key}: {value}\n"

            report += "\n"

        return report