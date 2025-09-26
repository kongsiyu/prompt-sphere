"""
提示词优化器主类

负责统筹整个提示词优化流程，集成各种优化策略和技术，
提供统一的优化接口和质量评估功能。
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import json

from .schemas.prompts import (
    PromptAnalysis, OptimizedPrompt, PromptOptimizationRequest,
    PromptOptimizationResult, OptimizationStrategy, QualityDimension,
    QualityScore, OptimizationSuggestion, PromptElement, OptimizationLevel,
    TemplateMatch, OptimizationConfig, PromptOptimizationError,
    InvalidPromptError
)
from .schemas.requirements import ParsedRequirements
from .optimizers.prompt_enhancer import PromptEnhancer
from .optimizers.template_matcher import TemplateMatcher

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """
    提示词优化器主类

    集成多种优化技术和策略，提供完整的提示词优化解决方案。
    包括结构分析、质量评估、策略选择和优化建议生成。
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        初始化优化器

        Args:
            config: 优化配置，如果为None则使用默认配置
        """
        self.config = config or OptimizationConfig()

        # 初始化子组件
        self.enhancer = PromptEnhancer()
        self.template_matcher = TemplateMatcher()

        # 质量评估权重
        self.quality_weights = {
            QualityDimension.CLARITY: 0.15,
            QualityDimension.SPECIFICITY: 0.15,
            QualityDimension.COMPLETENESS: 0.12,
            QualityDimension.RELEVANCE: 0.12,
            QualityDimension.COHERENCE: 0.10,
            QualityDimension.EFFECTIVENESS: 0.10,
            QualityDimension.CREATIVITY: 0.08,
            QualityDimension.SAFETY: 0.08,
            QualityDimension.BIAS_FREE: 0.05,
            QualityDimension.ACTIONABILITY: 0.05
        }

        # 优化策略优先级
        self.strategy_priorities = {
            OptimizationStrategy.STRUCTURE_IMPROVEMENT: 1,
            OptimizationStrategy.CLARITY_ENHANCEMENT: 2,
            OptimizationStrategy.CONTEXT_ENRICHMENT: 3,
            OptimizationStrategy.SPECIFICITY_INCREASE: 4,
            OptimizationStrategy.INSTRUCTION_REFINEMENT: 5,
            OptimizationStrategy.EXAMPLE_ADDITION: 6,
            OptimizationStrategy.BIAS_REDUCTION: 7,
            OptimizationStrategy.TEMPLATE_MATCHING: 8
        }

        logger.info("提示词优化器已初始化")

    async def optimize_prompt(
        self,
        request: PromptOptimizationRequest,
        requirements: Optional[ParsedRequirements] = None
    ) -> PromptOptimizationResult:
        """
        优化提示词

        Args:
            request: 优化请求
            requirements: 解析后的需求（可选）

        Returns:
            优化结果
        """
        start_time = datetime.now()
        processing_summary = {
            "request_id": request.request_id,
            "started_at": start_time.isoformat(),
            "strategies_attempted": [],
            "quality_improvements": {},
            "processing_steps": []
        }

        try:
            # 验证输入
            await self._validate_prompt(request.prompt_to_optimize)

            # 1. 分析原始提示词
            analysis = await self.analyze_prompt(request.prompt_to_optimize)
            processing_summary["processing_steps"].append("prompt_analysis_completed")

            # 2. 生成优化建议
            suggestions = await self._generate_optimization_suggestions(
                analysis, request, requirements
            )
            processing_summary["processing_steps"].append("suggestions_generated")

            # 3. 查找匹配的模板（如果启用）
            template_matches = []
            if request.use_templates and self.config.enable_template_matching:
                template_matches = await self.template_matcher.find_matching_templates(
                    request.prompt_to_optimize,
                    requirements=requirements
                )
                processing_summary["processing_steps"].append("template_matching_completed")

            # 4. 执行优化
            optimized_versions = await self._execute_optimization(
                request, suggestions, template_matches, analysis
            )
            processing_summary["processing_steps"].append("optimization_executed")

            # 5. 选择最佳版本
            best_version = await self._select_best_version(optimized_versions)
            alternative_versions = [v for v in optimized_versions if v != best_version]

            # 6. 生成处理摘要
            if best_version:
                processing_summary["strategies_attempted"] = [
                    s.value for s in best_version.applied_strategies
                ]
                processing_summary["quality_improvements"] = best_version.quality_improvement

            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            processing_summary["completed_at"] = datetime.now().isoformat()
            processing_summary["processing_time_ms"] = processing_time

            return PromptOptimizationResult(
                request_id=request.request_id,
                success=True,
                optimized_prompt=best_version,
                alternative_versions=alternative_versions[:self.config.max_alternative_versions],
                analysis=analysis if self.config.include_analysis else None,
                template_matches=template_matches,
                processing_summary=processing_summary,
                processing_time_ms=processing_time
            )

        except Exception as e:
            error_msg = f"优化过程中发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            processing_summary["completed_at"] = datetime.now().isoformat()
            processing_summary["processing_time_ms"] = processing_time
            processing_summary["error"] = str(e)

            return PromptOptimizationResult(
                request_id=request.request_id,
                success=False,
                errors=[error_msg],
                processing_summary=processing_summary,
                processing_time_ms=processing_time
            )

    async def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        分析提示词

        Args:
            prompt: 要分析的提示词

        Returns:
            分析结果
        """
        start_time = datetime.now()

        try:
            # 1. 基本属性分析
            length_analysis = await self._analyze_length(prompt)
            structure_analysis = await self._analyze_structure(prompt)

            # 2. 提取提示词元素
            elements = await self._extract_prompt_elements(prompt)

            # 3. 质量评估
            quality_scores = await self._assess_quality(prompt, elements)
            overall_score = await self._calculate_overall_score(quality_scores)

            # 4. 问题识别
            issues, warnings = await self._identify_issues(prompt, quality_scores)

            # 5. 类型和复杂度检测
            detected_type = await self._detect_prompt_type(prompt)
            detected_complexity = await self._detect_complexity(prompt)

            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return PromptAnalysis(
                prompt_content=prompt,
                length_analysis=length_analysis,
                structure_analysis=structure_analysis,
                elements=elements,
                quality_scores=quality_scores,
                overall_score=overall_score,
                issues=issues,
                warnings=warnings,
                detected_type=detected_type,
                detected_complexity=detected_complexity,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"分析提示词时发生错误: {e}", exc_info=True)
            raise PromptOptimizationError(
                f"提示词分析失败: {str(e)}",
                error_code="ANALYSIS_FAILED"
            )

    async def create_prompt_from_requirements(
        self, requirements: ParsedRequirements
    ) -> PromptOptimizationResult:
        """
        从需求创建提示词

        Args:
            requirements: 解析后的需求

        Returns:
            优化结果（包含创建的提示词）
        """
        start_time = datetime.now()

        try:
            # 1. 基于需求生成初始提示词
            initial_prompt = await self._generate_initial_prompt(requirements)

            # 2. 创建优化请求
            optimization_request = PromptOptimizationRequest(
                prompt_to_optimize=initial_prompt,
                optimization_level=OptimizationLevel.MODERATE,
                use_templates=True
            )

            # 3. 优化生成的提示词
            result = await self.optimize_prompt(optimization_request, requirements)

            return result

        except Exception as e:
            error_msg = f"从需求创建提示词时发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return PromptOptimizationResult(
                request_id=f"create_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                errors=[error_msg],
                processing_time_ms=processing_time
            )

    # 私有方法 - 验证和预处理
    async def _validate_prompt(self, prompt: str) -> None:
        """验证提示词有效性"""
        if not prompt or not prompt.strip():
            raise InvalidPromptError(prompt, "提示词不能为空")

        if len(prompt.strip()) < 10:
            raise InvalidPromptError(prompt, "提示词过短，至少需要10个字符")

        if len(prompt) > 10000:
            raise InvalidPromptError(prompt, "提示词过长，最多10000个字符")

    # 私有方法 - 分析功能
    async def _analyze_length(self, prompt: str) -> Dict[str, Any]:
        """分析长度相关指标"""
        words = prompt.split()
        sentences = re.split(r'[.!?。！？]+', prompt)
        sentences = [s.strip() for s in sentences if s.strip()]

        return {
            "total_characters": len(prompt),
            "total_words": len(words),
            "total_sentences": len(sentences),
            "avg_words_per_sentence": len(words) / max(len(sentences), 1),
            "avg_chars_per_word": len(prompt.replace(' ', '')) / max(len(words), 1),
            "length_category": self._categorize_length(len(prompt))
        }

    async def _analyze_structure(self, prompt: str) -> Dict[str, Any]:
        """分析结构相关指标"""
        # 检测结构元素
        has_instructions = bool(re.search(r'请|请您|要求|需要|应该|必须', prompt))
        has_examples = bool(re.search(r'例如|比如|示例|举例', prompt))
        has_constraints = bool(re.search(r'不要|不能|避免|禁止|限制', prompt))
        has_context = bool(re.search(r'背景|情况|场景|上下文', prompt))

        # 检测格式化
        has_bullet_points = bool(re.search(r'[•·\-\*]\s', prompt))
        has_numbered_lists = bool(re.search(r'\d+\.\s', prompt))
        has_sections = bool(re.search(r'^\s*#+\s', prompt, re.MULTILINE))

        return {
            "has_instructions": has_instructions,
            "has_examples": has_examples,
            "has_constraints": has_constraints,
            "has_context": has_context,
            "has_bullet_points": has_bullet_points,
            "has_numbered_lists": has_numbered_lists,
            "has_sections": has_sections,
            "structure_score": sum([
                has_instructions, has_examples, has_constraints,
                has_context, has_bullet_points, has_numbered_lists
            ]) / 6
        }

    async def _extract_prompt_elements(self, prompt: str) -> List[PromptElement]:
        """提取提示词元素"""
        elements = []

        # 提取指令部分
        instruction_patterns = [
            r'请.*?[。！？\n]',
            r'要求.*?[。！？\n]',
            r'需要.*?[。！？\n]'
        ]
        for pattern in instruction_patterns:
            matches = re.findall(pattern, prompt)
            for i, match in enumerate(matches):
                elements.append(PromptElement(
                    element_type="instruction",
                    content=match.strip(),
                    importance=0.9,
                    position=i
                ))

        # 提取上下文部分
        context_patterns = [
            r'背景.*?[。！？\n]',
            r'情况.*?[。！？\n]',
            r'场景.*?[。！？\n]'
        ]
        for pattern in context_patterns:
            matches = re.findall(pattern, prompt)
            for i, match in enumerate(matches):
                elements.append(PromptElement(
                    element_type="context",
                    content=match.strip(),
                    importance=0.7,
                    position=i
                ))

        # 提取示例部分
        example_patterns = [
            r'例如.*?[。！？\n]',
            r'比如.*?[。！？\n]',
            r'示例.*?[。！？\n]'
        ]
        for pattern in example_patterns:
            matches = re.findall(pattern, prompt)
            for i, match in enumerate(matches):
                elements.append(PromptElement(
                    element_type="example",
                    content=match.strip(),
                    importance=0.8,
                    position=i
                ))

        # 提取约束部分
        constraint_patterns = [
            r'不要.*?[。！？\n]',
            r'避免.*?[。！？\n]',
            r'禁止.*?[。！？\n]'
        ]
        for pattern in constraint_patterns:
            matches = re.findall(pattern, prompt)
            for i, match in enumerate(matches):
                elements.append(PromptElement(
                    element_type="constraint",
                    content=match.strip(),
                    importance=0.6,
                    position=i
                ))

        return elements

    async def _assess_quality(
        self, prompt: str, elements: List[PromptElement]
    ) -> List[QualityScore]:
        """评估提示词质量"""
        quality_scores = []

        # 清晰度评估
        clarity_score = await self._assess_clarity(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.CLARITY,
            score=clarity_score,
            reasoning="基于语言简洁性、术语使用和结构清晰度评估"
        ))

        # 具体性评估
        specificity_score = await self._assess_specificity(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.SPECIFICITY,
            score=specificity_score,
            reasoning="基于具体指令、明确要求和详细描述评估"
        ))

        # 完整性评估
        completeness_score = await self._assess_completeness(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            reasoning="基于信息完整度、必要元素覆盖度评估"
        ))

        # 相关性评估
        relevance_score = await self._assess_relevance(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.RELEVANCE,
            score=relevance_score,
            reasoning="基于内容相关性和目标一致性评估"
        ))

        # 连贯性评估
        coherence_score = await self._assess_coherence(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.COHERENCE,
            score=coherence_score,
            reasoning="基于逻辑连贯性和结构一致性评估"
        ))

        # 有效性评估
        effectiveness_score = await self._assess_effectiveness(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.EFFECTIVENESS,
            score=effectiveness_score,
            reasoning="基于预期效果和可执行性评估"
        ))

        # 创意性评估
        creativity_score = await self._assess_creativity(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.CREATIVITY,
            score=creativity_score,
            reasoning="基于创新性和启发性评估"
        ))

        # 安全性评估
        safety_score = await self._assess_safety(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.SAFETY,
            score=safety_score,
            reasoning="基于内容安全性和伦理合规性评估"
        ))

        # 无偏见评估
        bias_free_score = await self._assess_bias_free(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.BIAS_FREE,
            score=bias_free_score,
            reasoning="基于公平性和无偏见性评估"
        ))

        # 可操作性评估
        actionability_score = await self._assess_actionability(prompt, elements)
        quality_scores.append(QualityScore(
            dimension=QualityDimension.ACTIONABILITY,
            score=actionability_score,
            reasoning="基于可操作性和实用性评估"
        ))

        return quality_scores

    # 质量评估的具体方法
    async def _assess_clarity(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估清晰度"""
        score = 5.0

        # 检查语言简洁性
        avg_sentence_length = len(prompt.split()) / max(len(re.split(r'[.!?。！？]+', prompt)), 1)
        if avg_sentence_length > 25:
            score -= 1.0
        elif avg_sentence_length < 8:
            score += 0.5

        # 检查专业术语使用
        technical_terms = len(re.findall(r'[A-Z]{2,}|API|SQL|HTTP|JSON|XML', prompt))
        if technical_terms > 5:
            score -= 0.5

        # 检查结构清晰度
        if any(e.element_type == "instruction" for e in elements):
            score += 1.0

        return max(0.0, min(10.0, score))

    async def _assess_specificity(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估具体性"""
        score = 5.0

        # 检查具体数量和指标
        specific_numbers = len(re.findall(r'\d+', prompt))
        score += min(specific_numbers * 0.2, 1.0)

        # 检查具体例子
        if any(e.element_type == "example" for e in elements):
            score += 1.5

        # 检查模糊词汇
        vague_words = len(re.findall(r'一些|某些|可能|大概|差不多|相关', prompt))
        score -= vague_words * 0.3

        return max(0.0, min(10.0, score))

    async def _assess_completeness(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估完整性"""
        score = 5.0

        # 检查必要元素
        element_types = set(e.element_type for e in elements)
        if "instruction" in element_types:
            score += 1.0
        if "context" in element_types:
            score += 0.8
        if "example" in element_types:
            score += 0.7
        if "constraint" in element_types:
            score += 0.5

        # 检查长度适当性
        if len(prompt) < 50:
            score -= 2.0
        elif len(prompt) > 2000:
            score -= 1.0

        return max(0.0, min(10.0, score))

    async def _assess_relevance(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估相关性"""
        score = 7.0

        # 简单的相关性检查（实际应用中可能需要更复杂的NLP分析）
        # 检查是否有明确的主题
        if len(elements) > 0:
            score += 1.0

        # 检查内容一致性
        instruction_elements = [e for e in elements if e.element_type == "instruction"]
        if len(instruction_elements) > 1:
            # 检查指令之间的一致性（简化版本）
            score += 0.5

        return max(0.0, min(10.0, score))

    async def _assess_coherence(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估连贯性"""
        score = 6.0

        # 检查逻辑顺序
        if elements:
            # 检查元素顺序是否合理（context -> instruction -> example -> constraint）
            type_order = [e.element_type for e in elements]
            if self._check_logical_order(type_order):
                score += 1.5

        # 检查转折词和连接词
        transition_words = len(re.findall(r'因此|所以|但是|然而|另外|此外|首先|其次|最后', prompt))
        score += min(transition_words * 0.2, 1.0)

        return max(0.0, min(10.0, score))

    async def _assess_effectiveness(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估有效性"""
        score = 6.0

        # 检查可执行性
        action_verbs = len(re.findall(r'写|创建|生成|分析|总结|列出|描述|解释', prompt))
        score += min(action_verbs * 0.3, 1.5)

        # 检查目标明确性
        if any("目标" in e.content or "目的" in e.content for e in elements):
            score += 1.0

        return max(0.0, min(10.0, score))

    async def _assess_creativity(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估创意性"""
        score = 5.0

        # 检查创意词汇
        creative_words = len(re.findall(r'创新|创意|独特|原创|新颖|想象', prompt))
        score += min(creative_words * 0.5, 2.0)

        # 检查开放性问题
        open_questions = len(re.findall(r'如何|怎样|什么样', prompt))
        score += min(open_questions * 0.3, 1.0)

        return max(0.0, min(10.0, score))

    async def _assess_safety(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估安全性"""
        score = 9.0

        # 检查敏感内容
        sensitive_patterns = [
            r'暴力|血腥|仇恨|歧视',
            r'色情|淫秽|不雅',
            r'违法|犯罪|欺诈',
            r'伤害|攻击|威胁'
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                score -= 2.0

        return max(0.0, min(10.0, score))

    async def _assess_bias_free(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估无偏见性"""
        score = 8.0

        # 检查可能的偏见词汇
        bias_patterns = [
            r'男人|女人(?!性)|男性|女性(?!化)',
            r'老人|年轻人|小孩',
            r'富人|穷人|贫困',
            r'聪明|笨|愚蠢'
        ]

        for pattern in bias_patterns:
            matches = len(re.findall(pattern, prompt))
            if matches > 0:
                score -= matches * 0.5

        return max(0.0, min(10.0, score))

    async def _assess_actionability(self, prompt: str, elements: List[PromptElement]) -> float:
        """评估可操作性"""
        score = 6.0

        # 检查具体的动作指令
        action_instructions = sum(1 for e in elements if e.element_type == "instruction")
        score += min(action_instructions * 0.5, 2.0)

        # 检查步骤化描述
        steps = len(re.findall(r'步骤|第\d+|首先|然后|接着|最后', prompt))
        score += min(steps * 0.2, 1.0)

        return max(0.0, min(10.0, score))

    # 辅助方法
    def _categorize_length(self, length: int) -> str:
        """根据长度分类"""
        if length < 100:
            return "very_short"
        elif length < 300:
            return "short"
        elif length < 800:
            return "medium"
        elif length < 1500:
            return "long"
        else:
            return "very_long"

    def _check_logical_order(self, type_order: List[str]) -> bool:
        """检查元素逻辑顺序"""
        # 简化的逻辑顺序检查
        ideal_order = ["context", "instruction", "example", "constraint"]

        # 提取出现的类型并保持顺序
        unique_types = []
        for t in type_order:
            if t not in unique_types:
                unique_types.append(t)

        # 检查是否符合理想顺序
        for i, t in enumerate(unique_types):
            if t in ideal_order:
                expected_index = ideal_order.index(t)
                if i > expected_index:
                    return False

        return True

    async def _calculate_overall_score(self, quality_scores: List[QualityScore]) -> float:
        """计算总体质量分数"""
        if not quality_scores:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for score in quality_scores:
            weight = self.quality_weights.get(score.dimension, 0.1)
            weighted_sum += score.score * weight
            total_weight += weight

        return weighted_sum / max(total_weight, 1.0) if total_weight > 0 else 0.0

    async def _identify_issues(
        self, prompt: str, quality_scores: List[QualityScore]
    ) -> Tuple[List[str], List[str]]:
        """识别问题和警告"""
        issues = []
        warnings = []

        # 基于质量分数识别问题
        for score in quality_scores:
            if score.score < 3.0:
                issues.append(f"{score.dimension.value}评分过低 ({score.score:.1f}/10)")
            elif score.score < 5.0:
                warnings.append(f"{score.dimension.value}评分较低 ({score.score:.1f}/10)")

        # 检查常见问题
        if len(prompt.strip()) < 50:
            issues.append("提示词过短，缺少必要信息")

        if not re.search(r'[。！？.!?]', prompt):
            warnings.append("缺少句号等标点符号，可能影响理解")

        if len(re.findall(r'请|要求', prompt)) == 0:
            warnings.append("缺少明确的请求或要求表述")

        return issues, warnings

    async def _detect_prompt_type(self, prompt: str):
        """检测提示词类型"""
        # 简化的类型检测逻辑
        if re.search(r'写|创作|编写', prompt):
            return "creative_writing"
        elif re.search(r'分析|评估|研究', prompt):
            return "analytical"
        elif re.search(r'总结|摘要|概括', prompt):
            return "summarization"
        elif re.search(r'翻译|转换', prompt):
            return "translation"
        else:
            return "general"

    async def _detect_complexity(self, prompt: str):
        """检测复杂度"""
        complexity_indicators = 0

        # 基于长度
        if len(prompt) > 500:
            complexity_indicators += 1

        # 基于结构
        if re.search(r'步骤|流程|阶段', prompt):
            complexity_indicators += 1

        # 基于要求数量
        requirements = len(re.findall(r'请|要求|需要', prompt))
        if requirements > 3:
            complexity_indicators += 1

        # 基于专业术语
        technical_terms = len(re.findall(r'[A-Z]{2,}|API|SQL|HTTP', prompt))
        if technical_terms > 2:
            complexity_indicators += 1

        if complexity_indicators >= 3:
            return "complex"
        elif complexity_indicators >= 2:
            return "intermediate"
        else:
            return "simple"

    # 优化相关方法
    async def _generate_optimization_suggestions(
        self,
        analysis: PromptAnalysis,
        request: PromptOptimizationRequest,
        requirements: Optional[ParsedRequirements]
    ) -> List[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []

        # 基于质量分数生成建议
        for quality_score in analysis.quality_scores:
            if quality_score.score < request.target_score_improvement + 5.0:
                suggestion = await self._create_suggestion_for_dimension(
                    quality_score.dimension, analysis, request
                )
                if suggestion:
                    suggestions.append(suggestion)

        # 基于结构分析生成建议
        if not analysis.structure_analysis.get("has_examples", False):
            suggestions.append(OptimizationSuggestion(
                strategy=OptimizationStrategy.EXAMPLE_ADDITION,
                priority=2,
                description="添加具体示例以提高清晰度和可理解性",
                impact_score=0.7,
                implementation_effort="medium",
                rationale="示例可以帮助用户更好地理解期望的输出格式"
            ))

        if not analysis.structure_analysis.get("has_context", False):
            suggestions.append(OptimizationSuggestion(
                strategy=OptimizationStrategy.CONTEXT_ENRICHMENT,
                priority=1,
                description="添加背景上下文以提供更多信息",
                impact_score=0.8,
                implementation_effort="low",
                rationale="上下文有助于AI更好地理解任务需求"
            ))

        # 按优先级排序
        suggestions.sort(key=lambda x: (x.priority, -x.impact_score))

        return suggestions[:10]  # 限制建议数量

    async def _create_suggestion_for_dimension(
        self,
        dimension: QualityDimension,
        analysis: PromptAnalysis,
        request: PromptOptimizationRequest
    ) -> Optional[OptimizationSuggestion]:
        """为特定质量维度创建建议"""

        suggestion_map = {
            QualityDimension.CLARITY: OptimizationSuggestion(
                strategy=OptimizationStrategy.CLARITY_ENHANCEMENT,
                priority=1,
                description="简化语言表达，使用更清晰的词汇",
                impact_score=0.8,
                implementation_effort="medium",
                rationale="清晰的表达是有效提示词的基础"
            ),
            QualityDimension.SPECIFICITY: OptimizationSuggestion(
                strategy=OptimizationStrategy.SPECIFICITY_INCREASE,
                priority=2,
                description="增加具体的细节和明确的要求",
                impact_score=0.7,
                implementation_effort="medium",
                rationale="具体性有助于获得更准确的结果"
            ),
            QualityDimension.COMPLETENESS: OptimizationSuggestion(
                strategy=OptimizationStrategy.STRUCTURE_IMPROVEMENT,
                priority=1,
                description="补充缺失的信息和必要的上下文",
                impact_score=0.9,
                implementation_effort="high",
                rationale="完整的信息确保任务能被正确理解"
            )
        }

        return suggestion_map.get(dimension)

    async def _execute_optimization(
        self,
        request: PromptOptimizationRequest,
        suggestions: List[OptimizationSuggestion],
        template_matches: List[TemplateMatch],
        analysis: PromptAnalysis
    ) -> List[OptimizedPrompt]:
        """执行优化"""
        optimized_versions = []

        try:
            # 基于建议优化
            if suggestions:
                enhanced_prompt = await self.enhancer.enhance_prompt(
                    request.prompt_to_optimize,
                    suggestions,
                    request.optimization_level
                )
                if enhanced_prompt:
                    optimized_versions.append(enhanced_prompt)

            # 基于模板优化
            if template_matches and request.use_templates:
                for match in template_matches[:3]:  # 最多使用3个模板
                    template_optimized = await self._optimize_with_template(
                        request.prompt_to_optimize,
                        match,
                        analysis
                    )
                    if template_optimized:
                        optimized_versions.append(template_optimized)

            return optimized_versions

        except Exception as e:
            logger.error(f"执行优化时发生错误: {e}", exc_info=True)
            return []

    async def _optimize_with_template(
        self,
        original_prompt: str,
        template_match: TemplateMatch,
        analysis: PromptAnalysis
    ) -> Optional[OptimizedPrompt]:
        """使用模板优化提示词"""
        try:
            # 简化的模板应用逻辑
            template_content = template_match.template.template_content

            # 这里应该有更复杂的模板应用逻辑
            # 目前使用简化版本
            optimized_content = f"{original_prompt}\n\n基于模板优化:\n{template_content}"

            return OptimizedPrompt(
                original_prompt=original_prompt,
                optimized_prompt=optimized_content,
                optimization_level=OptimizationLevel.MODERATE,
                applied_strategies=[OptimizationStrategy.TEMPLATE_MATCHING],
                template_used=template_match.template,
                overall_improvement_score=template_match.similarity_score * 0.5,
                confidence_score=template_match.similarity_score
            )

        except Exception as e:
            logger.error(f"模板优化失败: {e}", exc_info=True)
            return None

    async def _select_best_version(
        self, versions: List[OptimizedPrompt]
    ) -> Optional[OptimizedPrompt]:
        """选择最佳版本"""
        if not versions:
            return None

        # 基于综合评分选择
        return max(versions, key=lambda v: (
            v.overall_improvement_score * 0.6 +
            v.confidence_score * 0.4
        ))

    async def _generate_initial_prompt(
        self, requirements: ParsedRequirements
    ) -> str:
        """从需求生成初始提示词"""
        # 构建基本提示词结构
        prompt_parts = []

        # 添加主要目标
        if requirements.main_objective:
            prompt_parts.append(f"目标: {requirements.main_objective}")

        # 添加关键需求
        if requirements.key_requirements:
            prompt_parts.append("要求:")
            for req in requirements.key_requirements:
                prompt_parts.append(f"- {req}")

        # 添加上下文
        domain_contexts = requirements.get_context_by_type("domain")
        if domain_contexts:
            prompt_parts.append("背景:")
            for ctx in domain_contexts:
                prompt_parts.append(f"- {ctx.content}")

        # 添加约束
        if requirements.constraints:
            prompt_parts.append("约束:")
            for constraint in requirements.constraints:
                prompt_parts.append(f"- {constraint}")

        # 添加示例
        if requirements.provided_examples:
            prompt_parts.append("示例:")
            for example in requirements.provided_examples:
                prompt_parts.append(f"- {example}")

        # 添加输出格式要求
        if requirements.expected_output_format:
            prompt_parts.append(f"输出格式: {requirements.expected_output_format}")

        return "\n\n".join(prompt_parts)