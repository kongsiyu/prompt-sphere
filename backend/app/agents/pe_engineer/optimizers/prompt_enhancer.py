"""
提示词增强器

实现各种提示词增强算法，包括结构优化、内容增强、
语言改进和质量提升等功能。
"""

import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from ..schemas.prompts import (
    OptimizedPrompt, OptimizationSuggestion, OptimizationStrategy,
    OptimizationLevel, QualityDimension, PromptElement
)

logger = logging.getLogger(__name__)


class PromptEnhancer:
    """
    提示词增强器

    提供多种提示词增强和改进算法，包括：
    - 结构优化
    - 清晰度提升
    - 内容增强
    - 语言改进
    """

    def __init__(self):
        """初始化增强器"""
        # 优化策略实现映射
        self.strategy_implementations = {
            OptimizationStrategy.STRUCTURE_IMPROVEMENT: self._improve_structure,
            OptimizationStrategy.CLARITY_ENHANCEMENT: self._enhance_clarity,
            OptimizationStrategy.CONTEXT_ENRICHMENT: self._enrich_context,
            OptimizationStrategy.SPECIFICITY_INCREASE: self._increase_specificity,
            OptimizationStrategy.BIAS_REDUCTION: self._reduce_bias,
            OptimizationStrategy.INSTRUCTION_REFINEMENT: self._refine_instructions,
            OptimizationStrategy.EXAMPLE_ADDITION: self._add_examples
        }

        # 语言改进词汇库
        self.clarity_improvements = {
            # 模糊词汇 -> 清晰替换
            "一些": "具体的",
            "某些": "特定的",
            "可能": "应该",
            "大概": "大约",
            "差不多": "接近",
            "相关": "相关的具体",
            "适当": "合适的",
            "合理": "恰当的",
            "不错": "良好",
            "很好": "优秀"
        }

        # 结构化模板
        self.structure_templates = {
            "instruction_context_example": """
{context}

{instruction}

{examples}

{constraints}
""".strip(),

            "step_by_step": """
目标：{objective}

请按照以下步骤完成：
{steps}

要求：
{requirements}

示例：
{examples}
""".strip(),

            "role_based": """
作为一个{role}，{context}

请{instruction}

具体要求：
{requirements}

输出格式：
{format}
""".strip()
        }

        # 示例模板库
        self.example_templates = {
            "text_generation": [
                "输入：{input_example}\n输出：{output_example}",
                "示例1：{example1}\n示例2：{example2}"
            ],
            "analysis": [
                "分析示例：{analysis_example}",
                "参考格式：{format_example}"
            ],
            "creative": [
                "创作参考：{creative_example}",
                "风格示例：{style_example}"
            ]
        }

        logger.info("提示词增强器已初始化")

    async def enhance_prompt(
        self,
        original_prompt: str,
        suggestions: List[OptimizationSuggestion],
        optimization_level: OptimizationLevel
    ) -> Optional[OptimizedPrompt]:
        """
        增强提示词

        Args:
            original_prompt: 原始提示词
            suggestions: 优化建议列表
            optimization_level: 优化级别

        Returns:
            增强后的提示词，如果增强失败则返回None
        """
        try:
            start_time = datetime.now()

            # 根据优化级别确定处理策略
            strategies_to_apply = await self._select_strategies(suggestions, optimization_level)

            # 应用优化策略
            enhanced_prompt = original_prompt
            applied_strategies = []
            quality_improvements = {}

            for suggestion in suggestions:
                if suggestion.strategy in strategies_to_apply:
                    try:
                        # 应用特定策略
                        enhanced_text, improvements = await self._apply_strategy(
                            enhanced_prompt, suggestion
                        )

                        if enhanced_text and enhanced_text != enhanced_prompt:
                            enhanced_prompt = enhanced_text
                            applied_strategies.append(suggestion.strategy)
                            quality_improvements.update(improvements)

                            logger.debug(f"应用策略 {suggestion.strategy.value}")

                    except Exception as e:
                        logger.warning(f"应用策略 {suggestion.strategy.value} 失败: {e}")
                        continue

            # 如果没有任何改进，返回None
            if enhanced_prompt == original_prompt:
                logger.info("没有生成有效的增强版本")
                return None

            # 计算总体改进分数
            overall_improvement = await self._calculate_improvement_score(
                original_prompt, enhanced_prompt, quality_improvements
            )

            # 生成分析结果
            improvement_analysis = {
                "strategies_applied": [s.value for s in applied_strategies],
                "character_change": len(enhanced_prompt) - len(original_prompt),
                "structure_improved": self._has_structure_improved(original_prompt, enhanced_prompt),
                "clarity_improved": self._has_clarity_improved(original_prompt, enhanced_prompt),
                "completeness_improved": self._has_completeness_improved(original_prompt, enhanced_prompt)
            }

            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return OptimizedPrompt(
                original_prompt=original_prompt,
                optimized_prompt=enhanced_prompt,
                optimization_level=optimization_level,
                applied_strategies=applied_strategies,
                suggestions_used=suggestions,
                improvement_analysis=improvement_analysis,
                quality_improvement=quality_improvements,
                overall_improvement_score=overall_improvement,
                optimization_time_ms=processing_time,
                confidence_score=min(overall_improvement / 2.0, 1.0)
            )

        except Exception as e:
            logger.error(f"增强提示词时发生错误: {e}", exc_info=True)
            return None

    async def _select_strategies(
        self,
        suggestions: List[OptimizationSuggestion],
        optimization_level: OptimizationLevel
    ) -> List[OptimizationStrategy]:
        """根据优化级别选择策略"""

        # 所有建议的策略
        all_strategies = [s.strategy for s in suggestions]

        if optimization_level == OptimizationLevel.LIGHT:
            # 轻度优化：只选择低风险、高影响的策略
            priority_strategies = [
                OptimizationStrategy.CLARITY_ENHANCEMENT,
                OptimizationStrategy.INSTRUCTION_REFINEMENT
            ]
            return [s for s in all_strategies if s in priority_strategies][:2]

        elif optimization_level == OptimizationLevel.MODERATE:
            # 中度优化：平衡改进和保持原意
            return all_strategies[:4]

        elif optimization_level == OptimizationLevel.HEAVY:
            # 重度优化：应用所有建议
            return all_strategies

        elif optimization_level == OptimizationLevel.COMPLETE_REWRITE:
            # 完全重写：使用结构化方法
            return [
                OptimizationStrategy.STRUCTURE_IMPROVEMENT,
                OptimizationStrategy.CONTEXT_ENRICHMENT,
                OptimizationStrategy.CLARITY_ENHANCEMENT,
                OptimizationStrategy.SPECIFICITY_INCREASE,
                OptimizationStrategy.EXAMPLE_ADDITION
            ]

        return all_strategies[:3]  # 默认

    async def _apply_strategy(
        self,
        prompt: str,
        suggestion: OptimizationSuggestion
    ) -> Tuple[str, Dict[QualityDimension, float]]:
        """应用特定的优化策略"""

        strategy_func = self.strategy_implementations.get(suggestion.strategy)
        if not strategy_func:
            logger.warning(f"未找到策略实现: {suggestion.strategy.value}")
            return prompt, {}

        try:
            enhanced_text = await strategy_func(prompt, suggestion)
            improvements = await self._estimate_improvements(suggestion.strategy)

            return enhanced_text, improvements

        except Exception as e:
            logger.error(f"应用策略 {suggestion.strategy.value} 时发生错误: {e}")
            return prompt, {}

    # 具体策略实现方法
    async def _improve_structure(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """改进结构"""
        # 解析现有内容
        sections = await self._parse_prompt_sections(prompt)

        # 检测缺失的结构元素
        missing_elements = []

        if not sections.get("context"):
            missing_elements.append("背景说明")

        if not sections.get("instruction"):
            # 如果没有明确指令，添加一个
            if not re.search(r'请|要求|需要', prompt):
                missing_elements.append("明确指令")

        if not sections.get("examples"):
            missing_elements.append("示例说明")

        if not sections.get("constraints"):
            missing_elements.append("约束条件")

        # 使用结构化模板重组
        if missing_elements:
            structured_prompt = await self._restructure_with_template(prompt, sections)
            return structured_prompt

        return prompt

    async def _enhance_clarity(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """提升清晰度"""
        enhanced = prompt

        # 替换模糊词汇
        for vague_word, clear_word in self.clarity_improvements.items():
            enhanced = re.sub(rf'\b{vague_word}\b', clear_word, enhanced)

        # 简化复杂句子
        enhanced = await self._simplify_complex_sentences(enhanced)

        # 添加标点符号
        enhanced = await self._improve_punctuation(enhanced)

        # 分段优化
        enhanced = await self._optimize_paragraphs(enhanced)

        return enhanced

    async def _enrich_context(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """丰富上下文"""
        # 检测是否已有上下文
        if re.search(r'背景|情况|场景|上下文', prompt):
            return prompt

        # 添加上下文引导
        context_starters = [
            "背景：",
            "在以下情况下：",
            "考虑到以下背景：",
            "基于以下场景："
        ]

        # 尝试识别隐含上下文
        implicit_context = await self._extract_implicit_context(prompt)

        if implicit_context:
            context_intro = context_starters[0]  # 使用简单的"背景："
            enhanced = f"{context_intro}{implicit_context}\n\n{prompt}"
            return enhanced

        return prompt

    async def _increase_specificity(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """增加具体性"""
        enhanced = prompt

        # 替换通用词汇为具体词汇
        specificity_improvements = {
            r'\b很多\b': '5个以上',
            r'\b一些\b': '几个具体的',
            r'\b相关\b': '直接相关的',
            r'\b合适\b': '最适合的',
            r'\b不错\b': '高质量的',
            r'\b好的\b': '优秀的'
        }

        for pattern, replacement in specificity_improvements.items():
            enhanced = re.sub(pattern, replacement, enhanced)

        # 添加具体要求
        if not re.search(r'\d+', enhanced):
            # 如果没有数字，尝试添加具体要求
            enhanced = await self._add_specific_requirements(enhanced)

        return enhanced

    async def _reduce_bias(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """减少偏见"""
        enhanced = prompt

        # 性别中性化
        gender_neutral_replacements = {
            r'\b他\b': '这个人',
            r'\b她\b': '这个人',
            r'\b男性\b': '人员',
            r'\b女性\b': '人员'
        }

        for pattern, replacement in gender_neutral_replacements.items():
            enhanced = re.sub(pattern, replacement, enhanced)

        # 年龄中性化
        age_neutral_replacements = {
            r'\b年轻人\b': '人员',
            r'\b老人\b': '经验丰富的人员',
            r'\b小孩\b': '儿童'
        }

        for pattern, replacement in age_neutral_replacements.items():
            enhanced = re.sub(pattern, replacement, enhanced)

        return enhanced

    async def _refine_instructions(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """精炼指令"""
        # 查找指令部分
        instructions = re.findall(r'请.*?[。！？\n]', prompt)

        if not instructions:
            # 如果没有明确指令，尝试添加
            if not re.search(r'请|要求|需要', prompt):
                enhanced = f"请{prompt}"
                return enhanced
            return prompt

        enhanced = prompt

        # 改进指令的表达
        instruction_improvements = {
            r'请你': '请',
            r'请您': '请',
            r'能不能': '请',
            r'可以吗': '',
            r'请帮我': '请',
            r'帮忙': '请'
        }

        for pattern, replacement in instruction_improvements.items():
            enhanced = re.sub(pattern, replacement, enhanced)

        return enhanced

    async def _add_examples(
        self, prompt: str, suggestion: OptimizationSuggestion
    ) -> str:
        """添加示例"""
        # 如果已有示例，不重复添加
        if re.search(r'例如|比如|示例|举例', prompt):
            return prompt

        # 根据提示词类型添加适当的示例
        prompt_type = await self._detect_prompt_type(prompt)

        example_text = ""
        if prompt_type == "creative_writing":
            example_text = "\n\n示例：如果要求写一个故事开头，可以从描述场景或人物开始。"

        elif prompt_type == "analysis":
            example_text = "\n\n示例：分析时请包括关键要点、支持证据和结论。"

        elif prompt_type == "summarization":
            example_text = "\n\n示例：总结应包括主要观点、重要细节和核心结论。"

        elif prompt_type == "translation":
            example_text = "\n\n示例：翻译时请保持原文的语调和含义。"

        else:
            example_text = "\n\n示例：请确保输出内容清晰、准确、完整。"

        return prompt + example_text

    # 辅助方法
    async def _parse_prompt_sections(self, prompt: str) -> Dict[str, str]:
        """解析提示词的各个部分"""
        sections = {
            "context": "",
            "instruction": "",
            "examples": "",
            "constraints": "",
            "other": ""
        }

        # 查找上下文
        context_match = re.search(r'(背景|情况|场景|上下文)[:：]([^。！？\n]*)', prompt)
        if context_match:
            sections["context"] = context_match.group(2).strip()

        # 查找指令
        instruction_matches = re.findall(r'请.*?[。！？\n]', prompt)
        if instruction_matches:
            sections["instruction"] = " ".join(instruction_matches)

        # 查找示例
        example_match = re.search(r'(例如|比如|示例)[:：]([^。！？\n]*)', prompt)
        if example_match:
            sections["examples"] = example_match.group(2).strip()

        # 查找约束
        constraint_matches = re.findall(r'(不要|避免|禁止).*?[。！？\n]', prompt)
        if constraint_matches:
            sections["constraints"] = " ".join(constraint_matches)

        return sections

    async def _restructure_with_template(
        self, prompt: str, sections: Dict[str, str]
    ) -> str:
        """使用模板重构提示词"""
        # 选择最适合的模板
        if sections.get("context") and sections.get("instruction"):
            template = self.structure_templates["instruction_context_example"]

            return template.format(
                context=sections.get("context", ""),
                instruction=sections.get("instruction", prompt),
                examples=sections.get("examples", ""),
                constraints=sections.get("constraints", "")
            ).strip()

        else:
            # 简单的结构化
            parts = []

            if sections.get("context"):
                parts.append(f"背景：{sections['context']}")

            parts.append(sections.get("instruction", prompt))

            if sections.get("examples"):
                parts.append(f"示例：{sections['examples']}")

            if sections.get("constraints"):
                parts.append(f"注意：{sections['constraints']}")

            return "\n\n".join(parts)

    async def _simplify_complex_sentences(self, text: str) -> str:
        """简化复杂句子"""
        # 分割长句
        sentences = re.split(r'[。！？]', text)
        simplified_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 如果句子过长（>50字），尝试分割
            if len(sentence) > 50:
                # 在连接词处分割
                conjunctions = ['并且', '而且', '同时', '另外', '此外', '因此', '所以']
                for conj in conjunctions:
                    if conj in sentence:
                        parts = sentence.split(conj, 1)
                        if len(parts) == 2:
                            simplified_sentences.extend([
                                parts[0].strip() + '。',
                                parts[1].strip()
                            ])
                            break
                else:
                    simplified_sentences.append(sentence)
            else:
                simplified_sentences.append(sentence)

        # 重组文本
        result = '。'.join([s for s in simplified_sentences if s])
        if result and not result.endswith(('。', '！', '？')):
            result += '。'

        return result

    async def _improve_punctuation(self, text: str) -> str:
        """改进标点符号"""
        # 确保句子以适当的标点符号结尾
        text = re.sub(r'([^。！？\n])\n', r'\1。\n', text)

        # 添加缺失的句号
        if text and not text.endswith(('。', '！', '？', '\n')):
            text += '。'

        return text

    async def _optimize_paragraphs(self, text: str) -> str:
        """优化段落结构"""
        # 如果文本很长且没有分段，添加适当的分段
        if len(text) > 200 and '\n' not in text:
            # 在句号后的空格处添加换行
            sentences = text.split('。')
            if len(sentences) > 3:
                # 每2-3句分一段
                paragraphs = []
                current_paragraph = []

                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        current_paragraph.append(sentence.strip())

                        if len(current_paragraph) >= 2 and i < len(sentences) - 1:
                            paragraphs.append('。'.join(current_paragraph) + '。')
                            current_paragraph = []

                if current_paragraph:
                    paragraphs.append('。'.join(current_paragraph))

                text = '\n\n'.join(paragraphs)

        return text

    async def _extract_implicit_context(self, prompt: str) -> str:
        """提取隐含上下文"""
        # 简单的隐含上下文提取
        context_indicators = {
            r'写.*?文章|写.*?内容': '需要创作文本内容',
            r'分析.*?数据|分析.*?情况': '需要进行数据或情况分析',
            r'总结.*?|概括.*?': '需要对信息进行总结',
            r'翻译.*?|转换.*?': '需要语言翻译或格式转换',
            r'设计.*?|创建.*?': '需要设计或创建新内容'
        }

        for pattern, context in context_indicators.items():
            if re.search(pattern, prompt):
                return context

        return ""

    async def _add_specific_requirements(self, prompt: str) -> str:
        """添加具体要求"""
        # 如果提示词缺乏具体性，添加一些通用的具体要求
        if not re.search(r'字|个|项|条|点', prompt):
            # 基于内容类型添加具体要求
            if re.search(r'写|创作', prompt):
                return prompt + "（字数300-500字）"
            elif re.search(r'列出|罗列', prompt):
                return prompt + "（至少列出5个要点）"
            elif re.search(r'分析|评估', prompt):
                return prompt + "（请从3个不同角度分析）"

        return prompt

    async def _detect_prompt_type(self, prompt: str) -> str:
        """检测提示词类型"""
        if re.search(r'写|创作|编写', prompt):
            return "creative_writing"
        elif re.search(r'分析|评估|研究', prompt):
            return "analysis"
        elif re.search(r'总结|摘要|概括', prompt):
            return "summarization"
        elif re.search(r'翻译|转换', prompt):
            return "translation"
        else:
            return "general"

    async def _estimate_improvements(
        self, strategy: OptimizationStrategy
    ) -> Dict[QualityDimension, float]:
        """估算策略带来的质量改进"""
        improvement_map = {
            OptimizationStrategy.CLARITY_ENHANCEMENT: {
                QualityDimension.CLARITY: 1.5,
                QualityDimension.COHERENCE: 0.8
            },
            OptimizationStrategy.STRUCTURE_IMPROVEMENT: {
                QualityDimension.COHERENCE: 2.0,
                QualityDimension.COMPLETENESS: 1.2,
                QualityDimension.ACTIONABILITY: 1.0
            },
            OptimizationStrategy.CONTEXT_ENRICHMENT: {
                QualityDimension.COMPLETENESS: 1.8,
                QualityDimension.RELEVANCE: 1.0
            },
            OptimizationStrategy.SPECIFICITY_INCREASE: {
                QualityDimension.SPECIFICITY: 2.0,
                QualityDimension.ACTIONABILITY: 1.2
            },
            OptimizationStrategy.EXAMPLE_ADDITION: {
                QualityDimension.CLARITY: 1.0,
                QualityDimension.EFFECTIVENESS: 1.5
            },
            OptimizationStrategy.BIAS_REDUCTION: {
                QualityDimension.BIAS_FREE: 2.0,
                QualityDimension.SAFETY: 1.0
            }
        }

        return improvement_map.get(strategy, {})

    async def _calculate_improvement_score(
        self,
        original: str,
        enhanced: str,
        quality_improvements: Dict[QualityDimension, float]
    ) -> float:
        """计算总体改进分数"""
        # 基于质量改进计算
        quality_score = sum(quality_improvements.values()) / max(len(quality_improvements), 1)

        # 基于结构改进
        structure_score = 1.0 if self._has_structure_improved(original, enhanced) else 0.0

        # 基于长度变化（适度增长是好的）
        length_ratio = len(enhanced) / max(len(original), 1)
        length_score = 1.0 if 1.1 <= length_ratio <= 1.5 else 0.5

        # 综合评分
        total_score = (quality_score * 0.6 + structure_score * 0.3 + length_score * 0.1)

        return min(total_score, 3.0)  # 最大改进分数为3.0

    def _has_structure_improved(self, original: str, enhanced: str) -> bool:
        """检查结构是否改进"""
        original_structure_score = self._calculate_structure_score(original)
        enhanced_structure_score = self._calculate_structure_score(enhanced)

        return enhanced_structure_score > original_structure_score

    def _has_clarity_improved(self, original: str, enhanced: str) -> bool:
        """检查清晰度是否改进"""
        # 简单的清晰度指标：平均句子长度
        original_avg_length = len(original.split()) / max(len(re.split(r'[。！？]', original)), 1)
        enhanced_avg_length = len(enhanced.split()) / max(len(re.split(r'[。！？]', enhanced)), 1)

        # 适中的句子长度是最好的
        optimal_length = 15
        original_clarity = 1 / (1 + abs(original_avg_length - optimal_length))
        enhanced_clarity = 1 / (1 + abs(enhanced_avg_length - optimal_length))

        return enhanced_clarity > original_clarity

    def _has_completeness_improved(self, original: str, enhanced: str) -> bool:
        """检查完整性是否改进"""
        # 检查结构元素的完整性
        structure_elements = ['背景', '要求', '示例', '注意']

        original_elements = sum(1 for elem in structure_elements if elem in original)
        enhanced_elements = sum(1 for elem in structure_elements if elem in enhanced)

        return enhanced_elements > original_elements

    def _calculate_structure_score(self, text: str) -> float:
        """计算结构评分"""
        score = 0.0

        # 检查各种结构元素
        if re.search(r'背景|情况|场景', text):
            score += 0.25

        if re.search(r'请|要求|需要', text):
            score += 0.25

        if re.search(r'例如|比如|示例', text):
            score += 0.25

        if re.search(r'不要|避免|注意', text):
            score += 0.25

        # 检查分段
        if '\n' in text:
            score += 0.2

        # 检查标点符号
        if re.search(r'[。！？]', text):
            score += 0.1

        return min(score, 1.0)