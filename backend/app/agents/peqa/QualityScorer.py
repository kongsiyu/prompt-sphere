"""
质量评分器

负责对提示词进行多维度质量评分，包括清晰度、具体性、完整性、有效性和鲁棒性评估。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import QualityDimension, QualityScore, ScoringError
from .config import PEQAConfig


class QualityScorer:
    """质量评分器"""

    def __init__(self, config: PEQAConfig):
        """初始化质量评分器"""
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def score_all_dimensions(self, prompt: str) -> Dict[QualityDimension, QualityScore]:
        """
        对所有维度进行评分

        Args:
            prompt: 要评分的提示词

        Returns:
            Dict[QualityDimension, QualityScore]: 各维度评分结果
        """
        try:
            if self.config.enable_parallel_processing:
                # 并行评分
                tasks = [
                    self.score_clarity(prompt),
                    self.score_specificity(prompt),
                    self.score_completeness(prompt),
                    self.score_effectiveness(prompt),
                    self.score_robustness(prompt)
                ]
                results = await asyncio.gather(*tasks)

                dimensions = [
                    QualityDimension.CLARITY,
                    QualityDimension.SPECIFICITY,
                    QualityDimension.COMPLETENESS,
                    QualityDimension.EFFECTIVENESS,
                    QualityDimension.ROBUSTNESS
                ]

                return dict(zip(dimensions, results))
            else:
                # 串行评分
                return {
                    QualityDimension.CLARITY: await self.score_clarity(prompt),
                    QualityDimension.SPECIFICITY: await self.score_specificity(prompt),
                    QualityDimension.COMPLETENESS: await self.score_completeness(prompt),
                    QualityDimension.EFFECTIVENESS: await self.score_effectiveness(prompt),
                    QualityDimension.ROBUSTNESS: await self.score_robustness(prompt)
                }
        except Exception as e:
            self.logger.error(f"评分失败: {str(e)}")
            raise ScoringError(f"质量评分失败: {str(e)}")

    async def score_clarity(self, prompt: str) -> QualityScore:
        """评估清晰度"""
        try:
            # 基于规则的清晰度评估
            score = 0.0
            evidence = []
            issues = []

            # 长度检查
            if 50 <= len(prompt) <= 1000:
                score += 0.2
                evidence.append("提示词长度适中")
            elif len(prompt) < 50:
                issues.append("提示词过短，可能缺乏必要信息")
            else:
                issues.append("提示词过长，可能影响清晰度")

            # 结构检查
            if '.' in prompt or ',' in prompt:
                score += 0.2
                evidence.append("使用了适当的标点符号")

            # 指令词检查
            instruction_words = ['请', '帮我', '生成', '创建', '分析', '总结', '解释']
            if any(word in prompt for word in instruction_words):
                score += 0.3
                evidence.append("包含明确的指令词")
            else:
                issues.append("缺乏明确的指令词")

            # 问号检查
            if '?' in prompt or '？' in prompt:
                score += 0.1
                evidence.append("使用疑问句增强清晰度")

            # 专业术语密度
            if len(prompt.split()) > 0:
                word_count = len(prompt.split())
                if word_count >= 10:
                    score += 0.2
                    evidence.append("词汇丰富，表达清晰")

            return QualityScore(
                dimension=QualityDimension.CLARITY,
                score=min(score, 1.0),
                confidence=0.8,
                reasoning="基于语言结构和指令清晰度分析",
                evidence=evidence,
                issues=issues
            )
        except Exception as e:
            raise ScoringError(f"清晰度评分失败: {str(e)}")

    async def score_specificity(self, prompt: str) -> QualityScore:
        """评估具体性"""
        try:
            score = 0.0
            evidence = []
            issues = []

            # 具体数值检查
            import re
            numbers = re.findall(r'\d+', prompt)
            if numbers:
                score += 0.3
                evidence.append(f"包含具体数值: {len(numbers)}个")
            else:
                issues.append("缺乏具体的数值或指标")

            # 技术术语检查
            tech_terms = ['API', 'JSON', 'Python', 'SQL', '数据库', '算法', '模型', '系统']
            found_terms = [term for term in tech_terms if term in prompt]
            if found_terms:
                score += 0.2
                evidence.append(f"包含技术术语: {', '.join(found_terms)}")

            # 示例检查
            example_indicators = ['例如', '比如', '示例', '举例', '如下']
            if any(indicator in prompt for indicator in example_indicators):
                score += 0.2
                evidence.append("提供了具体示例")
            else:
                issues.append("缺乏具体示例")

            # 格式要求检查
            format_words = ['格式', 'CSV', 'JSON', 'XML', '表格', '列表']
            if any(word in prompt for word in format_words):
                score += 0.2
                evidence.append("指定了输出格式")

            # 详细程度
            if len(prompt) > 100:
                score += 0.1
                evidence.append("描述较为详细")

            return QualityScore(
                dimension=QualityDimension.SPECIFICITY,
                score=min(score, 1.0),
                confidence=0.7,
                reasoning="基于具体性指标和详细程度分析",
                evidence=evidence,
                issues=issues
            )
        except Exception as e:
            raise ScoringError(f"具体性评分失败: {str(e)}")

    async def score_completeness(self, prompt: str) -> QualityScore:
        """评估完整性"""
        try:
            score = 0.0
            evidence = []
            issues = []

            # 上下文信息
            context_indicators = ['背景', '目的', '目标', '需求', '场景']
            if any(indicator in prompt for indicator in context_indicators):
                score += 0.3
                evidence.append("提供了上下文信息")
            else:
                issues.append("缺乏背景上下文")

            # 输入输出规范
            io_indicators = ['输入', '输出', '返回', '结果', '格式']
            if any(indicator in prompt for indicator in io_indicators):
                score += 0.2
                evidence.append("说明了输入输出要求")

            # 约束条件
            constraint_indicators = ['要求', '限制', '条件', '规则', '标准']
            if any(indicator in prompt for indicator in constraint_indicators):
                score += 0.2
                evidence.append("包含约束条件")
            else:
                issues.append("缺乏必要的约束条件")

            # 步骤说明
            step_indicators = ['步骤', '流程', '过程', '方法', '顺序']
            if any(indicator in prompt for indicator in step_indicators):
                score += 0.2
                evidence.append("提供了操作步骤")

            # 完整性检查
            if len(prompt.split()) >= 20:
                score += 0.1
                evidence.append("内容较为完整")

            return QualityScore(
                dimension=QualityDimension.COMPLETENESS,
                score=min(score, 1.0),
                confidence=0.75,
                reasoning="基于信息完整性和覆盖度分析",
                evidence=evidence,
                issues=issues
            )
        except Exception as e:
            raise ScoringError(f"完整性评分失败: {str(e)}")

    async def score_effectiveness(self, prompt: str) -> QualityScore:
        """评估有效性"""
        try:
            score = 0.0
            evidence = []
            issues = []

            # 目标明确性
            goal_indicators = ['目标', '目的', '达成', '实现', '完成']
            if any(indicator in prompt for indicator in goal_indicators):
                score += 0.3
                evidence.append("目标明确")
            else:
                issues.append("目标不够明确")

            # 可操作性
            action_words = ['创建', '生成', '分析', '处理', '计算', '设计', '实现']
            if any(word in prompt for word in action_words):
                score += 0.3
                evidence.append("具有可操作性")
            else:
                issues.append("缺乏可操作的指令")

            # 结果可验证性
            verification_indicators = ['验证', '检查', '测试', '评估', '确认']
            if any(indicator in prompt for indicator in verification_indicators):
                score += 0.2
                evidence.append("结果可验证")

            # 实用价值
            value_indicators = ['解决', '改进', '优化', '提升', '帮助']
            if any(indicator in prompt for indicator in value_indicators):
                score += 0.1
                evidence.append("具有实用价值")

            # 逻辑结构
            if ',' in prompt or '。' in prompt:
                score += 0.1
                evidence.append("具有逻辑结构")

            return QualityScore(
                dimension=QualityDimension.EFFECTIVENESS,
                score=min(score, 1.0),
                confidence=0.8,
                reasoning="基于目标明确性和可操作性分析",
                evidence=evidence,
                issues=issues
            )
        except Exception as e:
            raise ScoringError(f"有效性评分失败: {str(e)}")

    async def score_robustness(self, prompt: str) -> QualityScore:
        """评估鲁棒性"""
        try:
            score = 0.0
            evidence = []
            issues = []

            # 错误处理
            error_indicators = ['错误', '异常', '失败', '处理', '容错']
            if any(indicator in prompt for indicator in error_indicators):
                score += 0.3
                evidence.append("考虑了错误处理")
            else:
                issues.append("未考虑错误处理")

            # 边界情况
            boundary_indicators = ['边界', '极限', '最大', '最小', '空值', '特殊']
            if any(indicator in prompt for indicator in boundary_indicators):
                score += 0.2
                evidence.append("考虑了边界情况")
            else:
                issues.append("未考虑边界情况")

            # 灵活性
            flexibility_indicators = ['可选', '或者', '可以', '支持', '兼容']
            if any(indicator in prompt for indicator in flexibility_indicators):
                score += 0.2
                evidence.append("具有一定灵活性")

            # 扩展性
            extension_indicators = ['扩展', '增加', '支持', '适应', '兼容']
            if any(indicator in prompt for indicator in extension_indicators):
                score += 0.2
                evidence.append("考虑了扩展性")

            # 通用性
            if len(prompt) < 500:  # 不过于具体，保持通用性
                score += 0.1
                evidence.append("保持适当的通用性")

            return QualityScore(
                dimension=QualityDimension.ROBUSTNESS,
                score=min(score, 1.0),
                confidence=0.7,
                reasoning="基于错误处理和边界情况考虑分析",
                evidence=evidence,
                issues=issues
            )
        except Exception as e:
            raise ScoringError(f"鲁棒性评分失败: {str(e)}")

    async def score_single_dimension(self, prompt: str, dimension: QualityDimension) -> QualityScore:
        """评估单个维度"""
        score_methods = {
            QualityDimension.CLARITY: self.score_clarity,
            QualityDimension.SPECIFICITY: self.score_specificity,
            QualityDimension.COMPLETENESS: self.score_completeness,
            QualityDimension.EFFECTIVENESS: self.score_effectiveness,
            QualityDimension.ROBUSTNESS: self.score_robustness
        }

        method = score_methods.get(dimension)
        if not method:
            raise ScoringError(f"不支持的评分维度: {dimension}")

        return await method(prompt)