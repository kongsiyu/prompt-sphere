"""
改进建议引擎

基于质量评估结果生成具体的改进建议和优化方案。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import (
    QualityDimension, QualityScore, Improvement,
    ImprovementCategory, ImprovementPriority,
    ImprovementGenerationError
)
from .config import PEQAConfig


class ImprovementEngine:
    """改进建议引擎"""

    def __init__(self, config: PEQAConfig):
        """初始化改进建议引擎"""
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def generate_improvements(self, prompt: str,
                                  dimension_scores: Dict[QualityDimension, QualityScore]) -> List[Improvement]:
        """
        生成改进建议

        Args:
            prompt: 原始提示词
            dimension_scores: 各维度评分结果

        Returns:
            List[Improvement]: 改进建议列表
        """
        try:
            improvements = []

            # 为每个低分维度生成建议
            for dimension, score in dimension_scores.items():
                if score.score < 0.7:  # 低于良好阈值
                    dimension_improvements = await self._generate_dimension_improvements(
                        prompt, dimension, score
                    )
                    improvements.extend(dimension_improvements)

            # 按影响分数排序
            improvements.sort(key=lambda x: x.impact_score, reverse=True)

            # 限制建议数量
            max_suggestions = self.config.get_improvement_config("max_suggestions", 10)
            improvements = improvements[:max_suggestions]

            # 设置优先级
            self._assign_priorities(improvements)

            return improvements

        except Exception as e:
            self.logger.error(f"生成改进建议失败: {str(e)}")
            raise ImprovementGenerationError(f"改进建议生成失败: {str(e)}")

    async def _generate_dimension_improvements(self, prompt: str,
                                             dimension: QualityDimension,
                                             score: QualityScore) -> List[Improvement]:
        """为特定维度生成改进建议"""

        generators = {
            QualityDimension.CLARITY: self._generate_clarity_improvements,
            QualityDimension.SPECIFICITY: self._generate_specificity_improvements,
            QualityDimension.COMPLETENESS: self._generate_completeness_improvements,
            QualityDimension.EFFECTIVENESS: self._generate_effectiveness_improvements,
            QualityDimension.ROBUSTNESS: self._generate_robustness_improvements
        }

        generator = generators.get(dimension)
        if not generator:
            return []

        return await generator(prompt, score)

    async def _generate_clarity_improvements(self, prompt: str, score: QualityScore) -> List[Improvement]:
        """生成清晰度改进建议"""
        improvements = []

        # 检查指令词
        instruction_words = ['请', '帮我', '生成', '创建', '分析']
        if not any(word in prompt for word in instruction_words):
            improvements.append(Improvement(
                category=ImprovementCategory.CLARITY,
                priority=ImprovementPriority.HIGH,
                title="添加明确的指令词",
                description="使用明确的动作词来表达你的需求",
                before_example="写一个程序",
                after_example="请为我创建一个Python程序",
                impact_score=0.8,
                difficulty="easy",
                estimated_improvement=0.2,
                rationale="明确的指令词能让AI更好地理解任务要求"
            ))

        # 检查结构
        if '.' not in prompt and ',' not in prompt:
            improvements.append(Improvement(
                category=ImprovementCategory.STRUCTURE,
                priority=ImprovementPriority.MEDIUM,
                title="改善句子结构",
                description="使用标点符号分隔不同的要求",
                before_example="帮我分析数据生成报告",
                after_example="帮我分析数据，然后生成详细报告。",
                impact_score=0.6,
                difficulty="easy",
                estimated_improvement=0.15,
                rationale="良好的句子结构提高表达清晰度"
            ))

        # 检查长度
        if len(prompt) < 50:
            improvements.append(Improvement(
                category=ImprovementCategory.CLARITY,
                priority=ImprovementPriority.HIGH,
                title="增加描述详细程度",
                description="提供更多上下文和具体要求",
                before_example="写代码",
                after_example="请为我编写一个Python函数，用于计算两个数字的平均值",
                impact_score=0.9,
                difficulty="medium",
                estimated_improvement=0.3,
                rationale="详细的描述有助于明确表达需求"
            ))

        return improvements

    async def _generate_specificity_improvements(self, prompt: str, score: QualityScore) -> List[Improvement]:
        """生成具体性改进建议"""
        improvements = []

        # 检查具体数值
        import re
        if not re.findall(r'\d+', prompt):
            improvements.append(Improvement(
                category=ImprovementCategory.SPECIFICITY,
                priority=ImprovementPriority.HIGH,
                title="添加具体的数值或指标",
                description="指定数量、大小、时间等具体参数",
                before_example="生成一些测试数据",
                after_example="生成100条用户测试数据，包含姓名、年龄、邮箱字段",
                impact_score=0.8,
                difficulty="easy",
                estimated_improvement=0.25,
                rationale="具体的数值使要求更加明确"
            ))

        # 检查示例
        example_indicators = ['例如', '比如', '示例']
        if not any(indicator in prompt for indicator in example_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.EXAMPLES,
                priority=ImprovementPriority.MEDIUM,
                title="提供具体示例",
                description="添加具体的例子来说明预期结果",
                before_example="分析销售数据",
                after_example="分析销售数据，例如：计算月度增长率、识别热销产品、预测下季度趋势",
                impact_score=0.7,
                difficulty="medium",
                estimated_improvement=0.2,
                rationale="具体示例帮助明确期望的输出类型"
            ))

        # 检查技术规范
        tech_terms = ['Python', 'JSON', 'API', 'SQL']
        if len(prompt) > 20 and not any(term in prompt for term in tech_terms):
            improvements.append(Improvement(
                category=ImprovementCategory.SPECIFICITY,
                priority=ImprovementPriority.MEDIUM,
                title="指定技术栈或工具",
                description="明确使用的编程语言、框架或工具",
                before_example="创建一个网站",
                after_example="使用Python Flask框架创建一个简单的博客网站",
                impact_score=0.6,
                difficulty="easy",
                estimated_improvement=0.15,
                rationale="技术规范确保输出符合实际需求"
            ))

        return improvements

    async def _generate_completeness_improvements(self, prompt: str, score: QualityScore) -> List[Improvement]:
        """生成完整性改进建议"""
        improvements = []

        # 检查上下文
        context_indicators = ['背景', '目的', '场景']
        if not any(indicator in prompt for indicator in context_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.CONTEXT,
                priority=ImprovementPriority.HIGH,
                title="添加背景上下文",
                description="说明任务的背景、目的和使用场景",
                before_example="优化这段代码",
                after_example="为了提高网站性能，请优化这段数据查询代码，预期处理10万条记录",
                impact_score=0.8,
                difficulty="medium",
                estimated_improvement=0.25,
                rationale="背景信息帮助生成更符合实际需求的解决方案"
            ))

        # 检查输入输出规范
        io_indicators = ['输入', '输出', '返回', '格式']
        if not any(indicator in prompt for indicator in io_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.COMPLETENESS,
                priority=ImprovementPriority.MEDIUM,
                title="明确输入输出规范",
                description="说明预期的输入格式和输出要求",
                before_example="处理用户数据",
                after_example="处理CSV格式的用户数据，输出JSON格式的统计报告",
                impact_score=0.7,
                difficulty="easy",
                estimated_improvement=0.2,
                rationale="明确的输入输出规范确保结果符合预期"
            ))

        # 检查约束条件
        constraint_indicators = ['要求', '限制', '条件']
        if not any(indicator in prompt for indicator in constraint_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.CONSTRAINTS,
                priority=ImprovementPriority.MEDIUM,
                title="添加约束条件",
                description="指定性能要求、资源限制或其他约束",
                before_example="设计数据库",
                after_example="设计用户管理数据库，要求支持百万级用户，响应时间<100ms",
                impact_score=0.6,
                difficulty="medium",
                estimated_improvement=0.15,
                rationale="约束条件确保解决方案的可行性"
            ))

        return improvements

    async def _generate_effectiveness_improvements(self, prompt: str, score: QualityScore) -> List[Improvement]:
        """生成有效性改进建议"""
        improvements = []

        # 检查目标明确性
        goal_indicators = ['目标', '目的', '实现']
        if not any(indicator in prompt for indicator in goal_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.EFFECTIVENESS,
                priority=ImprovementPriority.HIGH,
                title="明确目标和期望结果",
                description="清楚地说明你想要达成的目标",
                before_example="改进用户体验",
                after_example="目标是将用户注册流程的完成率提升20%，请提供UX改进方案",
                impact_score=0.9,
                difficulty="medium",
                estimated_improvement=0.3,
                rationale="明确的目标确保解决方案针对性强"
            ))

        # 检查可操作性
        action_words = ['创建', '生成', '分析', '设计']
        if not any(word in prompt for word in action_words):
            improvements.append(Improvement(
                category=ImprovementCategory.EFFECTIVENESS,
                priority=ImprovementPriority.HIGH,
                title="使用具体的动作词",
                description="使用明确的动作词来表达需要执行的操作",
                before_example="关于机器学习的内容",
                after_example="请创建一个机器学习入门教程，包含代码示例",
                impact_score=0.8,
                difficulty="easy",
                estimated_improvement=0.25,
                rationale="具体的动作词让任务更加明确可执行"
            ))

        return improvements

    async def _generate_robustness_improvements(self, prompt: str, score: QualityScore) -> List[Improvement]:
        """生成鲁棒性改进建议"""
        improvements = []

        # 检查错误处理
        error_indicators = ['错误', '异常', '失败']
        if not any(indicator in prompt for indicator in error_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.ROBUSTNESS,
                priority=ImprovementPriority.MEDIUM,
                title="考虑错误处理",
                description="说明如何处理可能出现的错误情况",
                before_example="读取文件内容",
                after_example="读取文件内容，如果文件不存在则显示友好的错误提示",
                impact_score=0.6,
                difficulty="medium",
                estimated_improvement=0.15,
                rationale="错误处理提高解决方案的健壮性"
            ))

        # 检查边界情况
        boundary_indicators = ['边界', '极限', '空值']
        if not any(indicator in prompt for indicator in boundary_indicators):
            improvements.append(Improvement(
                category=ImprovementCategory.ROBUSTNESS,
                priority=ImprovementPriority.LOW,
                title="考虑边界情况",
                description="说明如何处理极值或特殊输入",
                before_example="计算平均值",
                after_example="计算平均值，处理空数据集和异常值的情况",
                impact_score=0.5,
                difficulty="medium",
                estimated_improvement=0.1,
                rationale="边界情况处理提高代码的鲁棒性"
            ))

        return improvements

    def _assign_priorities(self, improvements: List[Improvement]) -> None:
        """分配优先级"""
        # 根据影响分数分配优先级
        for improvement in improvements:
            if improvement.impact_score >= 0.8:
                improvement.priority = ImprovementPriority.CRITICAL
            elif improvement.impact_score >= 0.6:
                improvement.priority = ImprovementPriority.HIGH
            elif improvement.impact_score >= 0.4:
                improvement.priority = ImprovementPriority.MEDIUM
            else:
                improvement.priority = ImprovementPriority.LOW

    async def create_improvement_plan(self, improvements: List[Improvement]) -> Dict[str, Any]:
        """创建改进实施计划"""
        plan = {
            "total_improvements": len(improvements),
            "priority_breakdown": {
                "critical": len([i for i in improvements if i.priority == ImprovementPriority.CRITICAL]),
                "high": len([i for i in improvements if i.priority == ImprovementPriority.HIGH]),
                "medium": len([i for i in improvements if i.priority == ImprovementPriority.MEDIUM]),
                "low": len([i for i in improvements if i.priority == ImprovementPriority.LOW])
            },
            "estimated_total_improvement": sum(i.estimated_improvement for i in improvements),
            "implementation_order": [i.improvement_id for i in improvements],
            "quick_wins": [i for i in improvements if i.difficulty == "easy" and i.impact_score > 0.5],
            "high_impact_changes": [i for i in improvements if i.impact_score > 0.7]
        }
        return plan