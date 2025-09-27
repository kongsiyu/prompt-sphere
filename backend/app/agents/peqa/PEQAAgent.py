"""
PEQA (Prompt Engineering Quality Assessment) Agent

负责提示词质量评估、评分、改进建议生成和详细报告创建的智能代理。
基于多维度质量评估框架，提供专业的提示词质量分析服务。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..base.base_agent import BaseAgent
from .types import (
    QualityAssessment, QualityScore, QualityDimension, QualityLevel,
    Improvement, AssessmentReport, BenchmarkResult,
    AssessmentRequest, BatchAssessmentRequest,
    AssessmentError, InvalidPromptError
)
from .QualityScorer import QualityScorer
from .ImprovementEngine import ImprovementEngine
from .ReportGenerator import ReportGenerator
from .config import PEQAConfig


class PEQAAgent(BaseAgent):
    """
    PEQA质量评估Agent

    提供提示词质量评估的完整解决方案，包括：
    - 多维度质量评分 (清晰度、具体性、完整性、有效性、鲁棒性)
    - 智能改进建议生成
    - 详细评估报告创建
    - 性能基准测试
    """

    def __init__(self, config: Optional[PEQAConfig] = None):
        """初始化PEQA Agent"""
        super().__init__(
            agent_id="peqa_agent",
            agent_type="PEQA"
        )

        self.config = config or PEQAConfig()
        self.logger = logging.getLogger(__name__)

        # 初始化核心组件
        self.quality_scorer = QualityScorer(self.config)
        self.improvement_engine = ImprovementEngine(self.config)
        self.report_generator = ReportGenerator(self.config)

        # 性能统计
        self.stats = {
            "total_assessments": 0,
            "total_processing_time_ms": 0,
            "average_score": 0.0,
            "last_assessment_time": None
        }

    async def assess_prompt(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> QualityAssessment:
        """
        评估提示词质量

        Args:
            prompt: 要评估的提示词
            options: 评估选项

        Returns:
            QualityAssessment: 完整的质量评估结果

        Raises:
            InvalidPromptError: 当提示词无效时
            AssessmentError: 当评估过程出错时
        """
        start_time = datetime.now()

        try:
            # 验证输入
            self._validate_prompt(prompt)

            # 使用质量评分器进行多维度评估
            dimension_scores = await self.quality_scorer.score_all_dimensions(prompt)

            # 计算总体评分
            overall_score = await self._calculate_overall_score(dimension_scores)

            # 确定质量等级
            quality_level = self._determine_quality_level(overall_score)

            # 分析优势和不足
            strengths, weaknesses = await self._analyze_strengths_weaknesses(dimension_scores)

            # 生成改进建议
            improvements = await self.improvement_engine.generate_improvements(
                prompt, dimension_scores
            )

            # 计算置信度
            confidence_level = self._calculate_confidence(dimension_scores)

            # 创建评估结果
            assessment = QualityAssessment(
                prompt_content=prompt,
                overall_score=overall_score,
                dimension_scores={dim: score for dim, score in dimension_scores.items()},
                quality_level=quality_level,
                confidence_level=confidence_level,
                strengths=strengths,
                weaknesses=weaknesses,
                improvement_suggestions=improvements,
                detailed_analysis=await self._create_detailed_analysis(prompt, dimension_scores),
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            # 更新统计
            self._update_stats(assessment)

            return assessment

        except Exception as e:
            self.logger.error(f"评估提示词时出错: {str(e)}")
            if isinstance(e, (InvalidPromptError, AssessmentError)):
                raise
            raise AssessmentError(f"评估过程中出现未预期错误: {str(e)}")

    async def generate_score(self, assessment: QualityAssessment) -> Dict[str, float]:
        """
        从评估结果生成详细评分信息

        Args:
            assessment: 质量评估结果

        Returns:
            Dict[str, float]: 详细评分信息
        """
        return {
            "overall_score": assessment.overall_score,
            "weighted_breakdown": {
                dim.value: score.score * self.config.dimension_weights.get(dim, 0.2)
                for dim, score in assessment.dimension_scores.items()
            },
            "confidence_level": assessment.confidence_level,
            "quality_level_numeric": self._quality_level_to_numeric(assessment.quality_level),
            "improvement_potential": 1.0 - assessment.overall_score
        }

    async def suggest_improvements(self, assessment: QualityAssessment) -> List[Improvement]:
        """
        基于评估结果生成改进建议

        Args:
            assessment: 质量评估结果

        Returns:
            List[Improvement]: 改进建议列表
        """
        return assessment.improvement_suggestions

    async def create_report(self, assessment: QualityAssessment,
                          format: str = "detailed") -> AssessmentReport:
        """
        创建详细评估报告

        Args:
            assessment: 质量评估结果
            format: 报告格式类型

        Returns:
            AssessmentReport: 评估报告
        """
        return await self.report_generator.generate_report(assessment, format)

    async def benchmark_performance(self, prompts: List[str]) -> BenchmarkResult:
        """
        执行性能基准测试

        Args:
            prompts: 测试提示词列表

        Returns:
            BenchmarkResult: 基准测试结果
        """
        start_time = datetime.now()
        assessments = []

        try:
            # 并行评估所有提示词
            if self.config.enable_parallel_processing:
                tasks = [self.assess_prompt(prompt) for prompt in prompts]
                assessments = await asyncio.gather(*tasks, return_exceptions=True)

                # 过滤掉异常结果
                valid_assessments = [a for a in assessments if isinstance(a, QualityAssessment)]
            else:
                # 串行评估
                for prompt in prompts:
                    try:
                        assessment = await self.assess_prompt(prompt)
                        assessments.append(assessment)
                    except Exception as e:
                        self.logger.warning(f"评估提示词失败: {str(e)}")
                        continue
                valid_assessments = assessments

            if not valid_assessments:
                raise AssessmentError("没有成功评估的提示词")

            # 计算统计指标
            scores = [a.overall_score for a in valid_assessments]
            processing_times = [a.processing_time_ms for a in valid_assessments]

            total_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            benchmark_result = BenchmarkResult(
                benchmark_type="quality",
                total_prompts=len(prompts),
                average_score=sum(scores) / len(scores),
                highest_score=max(scores),
                lowest_score=min(scores),
                total_processing_time_ms=total_time_ms,
                average_processing_time_ms=sum(processing_times) / len(processing_times),
                throughput=len(valid_assessments) / (total_time_ms / 1000) if total_time_ms > 0 else 0,
                individual_results=valid_assessments,
                performance_metrics={
                    "success_rate": len(valid_assessments) / len(prompts),
                    "error_count": len(prompts) - len(valid_assessments),
                    "parallel_processing": self.config.enable_parallel_processing
                }
            )

            return benchmark_result

        except Exception as e:
            self.logger.error(f"基准测试执行失败: {str(e)}")
            raise AssessmentError(f"基准测试失败: {str(e)}")

    async def batch_assess(self, request: BatchAssessmentRequest) -> Dict[str, Any]:
        """
        批量评估提示词

        Args:
            request: 批量评估请求

        Returns:
            Dict[str, Any]: 批量评估结果
        """
        start_time = datetime.now()

        try:
            assessments = []

            if request.parallel_processing and self.config.enable_parallel_processing:
                # 并行处理
                tasks = [self.assess_prompt(prompt, request.assessment_options)
                        for prompt in request.prompts]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, QualityAssessment):
                        assessments.append(result)
                    else:
                        self.logger.warning(f"评估失败: {str(result)}")
            else:
                # 串行处理
                for prompt in request.prompts:
                    try:
                        assessment = await self.assess_prompt(prompt, request.assessment_options)
                        assessments.append(assessment)
                    except Exception as e:
                        self.logger.warning(f"评估提示词失败: {str(e)}")

            # 创建批量结果
            result = {
                "request_id": request.request_id,
                "assessments": assessments,
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "success_count": len(assessments),
                "total_count": len(request.prompts),
                "success_rate": len(assessments) / len(request.prompts) if request.prompts else 0
            }

            # 添加汇总信息
            if request.include_summary and assessments:
                scores = [a.overall_score for a in assessments]
                result["summary"] = {
                    "average_score": sum(scores) / len(scores),
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "quality_distribution": self._get_quality_distribution(assessments)
                }

            return result

        except Exception as e:
            self.logger.error(f"批量评估失败: {str(e)}")
            raise AssessmentError(f"批量评估失败: {str(e)}")

    def _validate_prompt(self, prompt: str) -> None:
        """验证提示词有效性"""
        if not prompt or not isinstance(prompt, str):
            raise InvalidPromptError(prompt, "提示词必须是非空字符串")

        if len(prompt.strip()) < 3:
            raise InvalidPromptError(prompt, "提示词过短")

        if len(prompt) > self.config.max_prompt_length:
            raise InvalidPromptError(prompt, f"提示词超过最大长度限制 ({self.config.max_prompt_length})")

    async def _calculate_overall_score(self, dimension_scores: Dict[QualityDimension, QualityScore]) -> float:
        """计算总体评分"""
        weighted_sum = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.config.dimension_weights.get(dimension, 0.2)
            weighted_sum += score.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        thresholds = self.config.quality_thresholds

        if score >= thresholds["excellent"]:
            return QualityLevel.EXCELLENT
        elif score >= thresholds["good"]:
            return QualityLevel.GOOD
        elif score >= thresholds["fair"]:
            return QualityLevel.FAIR
        elif score >= thresholds["poor"]:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR

    async def _analyze_strengths_weaknesses(self, dimension_scores: Dict[QualityDimension, QualityScore]) -> tuple:
        """分析优势和不足"""
        strengths = []
        weaknesses = []

        for dimension, score in dimension_scores.items():
            if score.score >= 0.8:
                strengths.extend([f"{dimension.value}: {reason}" for reason in score.evidence])
            elif score.score <= 0.5:
                weaknesses.extend([f"{dimension.value}: {issue}" for issue in score.issues])

        return strengths, weaknesses

    def _calculate_confidence(self, dimension_scores: Dict[QualityDimension, QualityScore]) -> float:
        """计算整体置信度"""
        confidences = [score.confidence for score in dimension_scores.values()]
        return sum(confidences) / len(confidences) if confidences else 0.0

    async def _create_detailed_analysis(self, prompt: str,
                                      dimension_scores: Dict[QualityDimension, QualityScore]) -> Dict[str, Any]:
        """创建详细分析"""
        return {
            "prompt_length": len(prompt),
            "word_count": len(prompt.split()),
            "sentence_count": len([s for s in prompt.split('.') if s.strip()]),
            "dimension_details": {
                dim.value: {
                    "score": score.score,
                    "confidence": score.confidence,
                    "reasoning": score.reasoning,
                    "evidence_count": len(score.evidence),
                    "issue_count": len(score.issues)
                }
                for dim, score in dimension_scores.items()
            },
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _quality_level_to_numeric(self, quality_level: QualityLevel) -> float:
        """质量等级转数值"""
        mapping = {
            QualityLevel.EXCELLENT: 1.0,
            QualityLevel.GOOD: 0.8,
            QualityLevel.FAIR: 0.6,
            QualityLevel.POOR: 0.4,
            QualityLevel.VERY_POOR: 0.2
        }
        return mapping.get(quality_level, 0.0)

    def _get_quality_distribution(self, assessments: List[QualityAssessment]) -> Dict[str, int]:
        """获取质量分布"""
        distribution = {level.value: 0 for level in QualityLevel}
        for assessment in assessments:
            distribution[assessment.quality_level.value] += 1
        return distribution

    def _update_stats(self, assessment: QualityAssessment) -> None:
        """更新统计信息"""
        self.stats["total_assessments"] += 1
        self.stats["total_processing_time_ms"] += assessment.processing_time_ms

        # 更新平均分
        current_avg = self.stats["average_score"]
        count = self.stats["total_assessments"]
        self.stats["average_score"] = ((current_avg * (count - 1)) + assessment.overall_score) / count

        self.stats["last_assessment_time"] = assessment.assessed_at

    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "prompt_quality_assessment",      # 提示词质量评估
            "multi_dimension_scoring",        # 多维度评分
            "improvement_suggestions",        # 改进建议生成
            "detailed_reporting",            # 详细报告生成
            "batch_processing",              # 批量处理
            "performance_benchmarking",      # 性能基准测试
            "quality_level_classification",  # 质量等级分类
            "confidence_scoring",            # 置信度评分
            "export_multiple_formats"       # 多格式导出
        ]

    async def process_task(self, task) -> Dict[str, Any]:
        """处理具体任务"""
        try:
            task_type = task.get('type', 'assess_prompt')

            if task_type == 'assess_prompt':
                prompt = task.get('prompt', '')
                options = task.get('options', {})
                assessment = await self.assess_prompt(prompt, options)
                return {
                    'success': True,
                    'result': assessment.model_dump(),
                    'task_type': task_type
                }

            elif task_type == 'batch_assess':
                from .types import BatchAssessmentRequest
                request_data = task.get('request', {})
                request = BatchAssessmentRequest(**request_data)
                result = await self.batch_assess(request)
                return {
                    'success': True,
                    'result': result,
                    'task_type': task_type
                }

            elif task_type == 'benchmark':
                prompts = task.get('prompts', [])
                result = await self.benchmark_performance(prompts)
                return {
                    'success': True,
                    'result': result.model_dump(),
                    'task_type': task_type
                }

            elif task_type == 'health_check':
                result = await self.health_check()
                return {
                    'success': True,
                    'result': result,
                    'task_type': task_type
                }

            else:
                return {
                    'success': False,
                    'error': f'不支持的任务类型: {task_type}',
                    'task_type': task_type
                }

        except Exception as e:
            self.logger.error(f"任务处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'task_type': task.get('type', 'unknown')
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.stats.copy()
        if stats["total_assessments"] > 0:
            stats["average_processing_time_ms"] = (
                stats["total_processing_time_ms"] / stats["total_assessments"]
            )
        return stats

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试基本功能
            test_prompt = "这是一个测试提示词，用于验证PEQA Agent的基本功能。"
            test_assessment = await self.assess_prompt(test_prompt)

            return {
                "status": "healthy",
                "components": {
                    "quality_scorer": "ok",
                    "improvement_engine": "ok",
                    "report_generator": "ok"
                },
                "test_result": {
                    "test_score": test_assessment.overall_score,
                    "processing_time_ms": test_assessment.processing_time_ms
                },
                "stats": self.get_stats(),
                "config": {
                    "parallel_processing": self.config.enable_parallel_processing,
                    "max_prompt_length": self.config.max_prompt_length
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "stats": self.get_stats()
            }