"""
需求解析器

主要的需求解析模块，整合意图解析器和上下文提取器，
提供完整的自然语言需求解析功能，支持与 DashScope API 集成。
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

from .parsers.intent_parser import IntentParser
from .parsers.context_extractor import ContextExtractor
from .schemas.requirements import (
    ParsedRequirements, ParsedIntent, ExtractedContext, DomainInfo,
    TechnicalRequirement, IntentCategory, ContextType, SentimentType,
    ComplexityLevel, PromptType, QualityMetric, RequirementsParsingConfig,
    RequirementsValidationError
)
from .types import PromptType

logger = logging.getLogger(__name__)


class RequirementsParser:
    """
    需求解析器

    整合多个解析组件，提供完整的需求解析功能：
    1. 意图识别
    2. 上下文提取
    3. 需求分析
    4. 质量评估
    5. DashScope API 集成（可选）
    """

    def __init__(self, config: Optional[RequirementsParsingConfig] = None):
        self.config = config or RequirementsParsingConfig()

        # 初始化解析器组件
        self.intent_parser = IntentParser()
        self.context_extractor = ContextExtractor()

        # DashScope 客户端（可选）
        self.dashscope_client = None

        # 缓存
        self._parsing_cache: Dict[str, ParsedRequirements] = {}

        # 统计信息
        self._parsing_stats = {
            "total_parsed": 0,
            "cache_hits": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0,
            "failures": 0
        }

    async def parse_requirements(self, user_input: str,
                               context: Optional[Dict[str, Any]] = None) -> ParsedRequirements:
        """
        解析用户需求

        Args:
            user_input: 用户输入的自然语言文本
            context: 额外的上下文信息

        Returns:
            ParsedRequirements: 完整的解析结果

        Raises:
            RequirementsValidationError: 验证失败时抛出
        """
        start_time = time.time()
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            # 输入验证
            self._validate_input(user_input)

            # 检查缓存
            if self.config.enable_caching:
                cached_result = self._get_from_cache(user_input)
                if cached_result:
                    self._update_stats(start_time, True, cache_hit=True)
                    return cached_result

            # 创建基础解析结果对象
            parsed_requirements = ParsedRequirements(
                request_id=request_id,
                original_input=user_input,
                parsed_at=datetime.now()
            )

            # 1. 意图解析
            intent = await self._parse_intent(user_input)
            parsed_requirements.intent = intent

            # 2. 上下文提取
            contexts = await self._extract_contexts(user_input)
            parsed_requirements.extracted_contexts = contexts

            # 3. 领域识别
            domain_info = await self._identify_domain(user_input)
            parsed_requirements.domain_info = domain_info

            # 4. 技术需求提取
            tech_requirements = await self._extract_technical_requirements(user_input)
            parsed_requirements.technical_requirements = tech_requirements

            # 5. 主要目标识别
            main_objective = await self._identify_main_objective(user_input, intent, contexts)
            parsed_requirements.main_objective = main_objective

            # 6. 关键需求提取
            key_requirements = await self._extract_key_requirements(user_input, contexts)
            parsed_requirements.key_requirements = key_requirements

            # 7. 约束条件提取
            constraints = await self._extract_constraints(user_input, contexts)
            parsed_requirements.constraints = constraints

            # 8. 提示词类型建议
            suggested_type = await self._suggest_prompt_type(intent, contexts, domain_info)
            parsed_requirements.suggested_prompt_type = suggested_type

            # 9. 复杂度评估
            complexity = await self._assess_complexity(user_input, key_requirements, tech_requirements)
            parsed_requirements.complexity_estimate = complexity

            # 10. 目标受众识别
            target_audience = await self._identify_target_audience(user_input, contexts)
            parsed_requirements.target_audience = target_audience

            # 11. 输出格式识别
            output_format = await self._identify_output_format(user_input, contexts)
            parsed_requirements.expected_output_format = output_format

            # 12. 语调偏好识别
            tone_preferences = await self._identify_tone_preferences(user_input, contexts)
            parsed_requirements.tone_preferences = tone_preferences

            # 13. 示例和参考材料提取
            examples = await self._extract_examples(user_input, contexts)
            references = await self._extract_references(user_input, contexts)
            parsed_requirements.provided_examples = examples
            parsed_requirements.reference_materials = references

            # 14. 质量评估
            quality_metrics = await self._assess_parsing_quality(parsed_requirements, user_input)
            parsed_requirements.parsing_quality = quality_metrics

            # 15. 整体置信度计算
            overall_confidence = await self._calculate_overall_confidence(parsed_requirements)
            parsed_requirements.overall_confidence = overall_confidence

            # 16. 生成建议和警告
            suggestions, warnings, missing_info = await self._generate_suggestions(parsed_requirements)
            parsed_requirements.suggestions = suggestions
            parsed_requirements.warnings = warnings
            parsed_requirements.missing_info = missing_info

            # 17. 处理时间记录
            processing_time = int((time.time() - start_time) * 1000)
            parsed_requirements.processing_time_ms = processing_time

            # 18. 最终验证
            await self._validate_parsed_requirements(parsed_requirements)

            # 更新缓存
            if self.config.enable_caching:
                self._add_to_cache(user_input, parsed_requirements)

            # 更新统计信息
            self._update_stats(start_time, True)

            return parsed_requirements

        except Exception as e:
            # 更新统计信息
            self._update_stats(start_time, False)

            # 记录错误
            logger.error(f"需求解析失败 - Request ID: {request_id}, Error: {str(e)}")

            # 如果是验证错误，直接抛出
            if isinstance(e, RequirementsValidationError):
                raise

            # 其他错误包装为验证错误
            raise RequirementsValidationError(
                f"需求解析过程中发生错误: {str(e)}",
                validation_errors=[str(e)]
            )

    async def _parse_intent(self, text: str) -> ParsedIntent:
        """解析用户意图"""
        return self.intent_parser.parse_intent(text)

    async def _extract_contexts(self, text: str) -> List[ExtractedContext]:
        """提取上下文信息"""
        return self.context_extractor.extract_contexts(text)

    async def _identify_domain(self, text: str) -> Optional[DomainInfo]:
        """识别领域信息"""
        return self.context_extractor.extract_domain_info(text)

    async def _extract_technical_requirements(self, text: str) -> List[TechnicalRequirement]:
        """提取技术需求"""
        return self.context_extractor.extract_technical_requirements(text)

    async def _identify_main_objective(self, text: str, intent: ParsedIntent,
                                     contexts: List[ExtractedContext]) -> str:
        """识别主要目标"""
        # 基于意图类型确定主要目标
        objective_templates = {
            IntentCategory.CREATE_PROMPT: "创建一个新的提示词",
            IntentCategory.OPTIMIZE_PROMPT: "优化现有提示词的效果",
            IntentCategory.ANALYZE_PROMPT: "分析提示词的质量和性能",
            IntentCategory.GET_TEMPLATE: "获取相关的提示词模板",
            IntentCategory.CUSTOM_REQUEST: "处理自定义的提示词需求",
            IntentCategory.GENERAL_INQUIRY: "回答关于提示词的一般性问题"
        }

        base_objective = objective_templates.get(intent.category, "处理用户的提示词相关需求")

        # 从业务上下文中提取更具体的目标
        business_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.BUSINESS]
        if business_contexts:
            most_important_business = max(business_contexts, key=lambda x: x.importance)
            base_objective += f"，用于{most_important_business.content}"

        return base_objective

    async def _extract_key_requirements(self, text: str,
                                      contexts: List[ExtractedContext]) -> List[str]:
        """提取关键需求"""
        requirements = []

        # 从约束上下文中提取需求
        constraint_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.CONSTRAINT]
        for ctx in constraint_contexts:
            requirements.append(f"约束条件: {ctx.content}")

        # 从技术上下文中提取需求
        tech_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.TECHNICAL]
        for ctx in tech_contexts:
            requirements.append(f"技术要求: {ctx.content}")

        # 从业务上下文中提取需求
        business_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.BUSINESS]
        for ctx in business_contexts:
            requirements.append(f"业务需求: {ctx.content}")

        # 基于关键词提取额外需求
        keyword_requirements = await self._extract_keyword_requirements(text)
        requirements.extend(keyword_requirements)

        return list(set(requirements))  # 去重

    async def _extract_keyword_requirements(self, text: str) -> List[str]:
        """基于关键词提取需求"""
        requirements = []

        requirement_patterns = [
            (r"(准确|精确|正确)", "需要高准确性"),
            (r"(快速|迅速|及时)", "需要快速响应"),
            (r"(详细|全面|完整)", "需要详细完整的回答"),
            (r"(简洁|简短|简单)", "需要简洁明了的表达"),
            (r"(创意|创新|新颖)", "需要创意和创新性"),
            (r"(专业|权威|可信)", "需要专业性和权威性")
        ]

        for pattern, requirement in requirement_patterns:
            if re.search(pattern, text):
                requirements.append(requirement)

        return requirements

    async def _extract_constraints(self, text: str,
                                 contexts: List[ExtractedContext]) -> List[str]:
        """提取约束条件"""
        constraints = []

        # 从约束上下文中直接提取
        constraint_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.CONSTRAINT]
        for ctx in constraint_contexts:
            constraints.append(ctx.content)

        # 基于模式匹配提取约束
        constraint_patterns = [
            (r"长度不超过(\d+)", "长度限制"),
            (r"字数限制(\d+)", "字数限制"),
            (r"时间要求(\d+)", "时间限制"),
            (r"不能包含", "内容限制"),
            (r"必须包含", "内容要求")
        ]

        for pattern, constraint_type in constraint_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                constraints.append(f"{constraint_type}: {match}")

        return list(set(constraints))

    async def _suggest_prompt_type(self, intent: ParsedIntent,
                                 contexts: List[ExtractedContext],
                                 domain_info: Optional[DomainInfo]) -> PromptType:
        """建议提示词类型"""
        # 基于意图的基础映射
        intent_type_mapping = {
            IntentCategory.CREATE_PROMPT: PromptType.GENERAL,
            IntentCategory.OPTIMIZE_PROMPT: PromptType.ANALYTICAL,
            IntentCategory.ANALYZE_PROMPT: PromptType.ANALYTICAL,
            IntentCategory.GET_TEMPLATE: PromptType.GENERAL,
            IntentCategory.CUSTOM_REQUEST: PromptType.TASK_SPECIFIC,
            IntentCategory.GENERAL_INQUIRY: PromptType.CONVERSATIONAL
        }

        base_type = intent_type_mapping.get(intent.category, PromptType.GENERAL)

        # 基于领域信息调整
        if domain_info:
            domain_type_mapping = {
                "软件开发": PromptType.CODE_GENERATION,
                "人工智能": PromptType.ANALYTICAL,
                "数据分析": PromptType.ANALYTICAL,
                "产品设计": PromptType.CREATIVE,
                "市场营销": PromptType.CREATIVE,
                "教育培训": PromptType.CONVERSATIONAL,
                "翻译": PromptType.TRANSLATION
            }

            if domain_info.name in domain_type_mapping:
                return domain_type_mapping[domain_info.name]

        # 基于上下文调整
        tech_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.TECHNICAL]
        if any("代码" in ctx.content or "编程" in ctx.content for ctx in tech_contexts):
            return PromptType.CODE_GENERATION

        business_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.BUSINESS]
        if any("创意" in ctx.content or "设计" in ctx.content for ctx in business_contexts):
            return PromptType.CREATIVE

        return base_type

    async def _assess_complexity(self, text: str, key_requirements: List[str],
                               tech_requirements: List[TechnicalRequirement]) -> ComplexityLevel:
        """评估复杂度"""
        complexity_score = 0

        # 文本长度因子
        text_length = len(text)
        if text_length > 500:
            complexity_score += 3
        elif text_length > 200:
            complexity_score += 2
        elif text_length > 100:
            complexity_score += 1

        # 需求数量因子
        requirements_count = len(key_requirements)
        if requirements_count > 8:
            complexity_score += 3
        elif requirements_count > 5:
            complexity_score += 2
        elif requirements_count > 3:
            complexity_score += 1

        # 技术需求因子
        tech_count = len(tech_requirements)
        if tech_count > 5:
            complexity_score += 2
        elif tech_count > 2:
            complexity_score += 1

        # 复杂度关键词
        complexity_keywords = {
            "复杂": 2, "高级": 2, "专业": 1, "详细": 1,
            "全面": 1, "深入": 2, "系统": 1, "完整": 1
        }

        for keyword, score in complexity_keywords.items():
            if keyword in text:
                complexity_score += score

        # 根据总分确定复杂度级别
        if complexity_score >= 8:
            return ComplexityLevel.ADVANCED
        elif complexity_score >= 5:
            return ComplexityLevel.COMPLEX
        elif complexity_score >= 3:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.SIMPLE

    async def _identify_target_audience(self, text: str,
                                      contexts: List[ExtractedContext]) -> Optional[str]:
        """识别目标受众"""
        audience_patterns = [
            (r"(面向|针对|为了)[\s]*([^\s，。！？；]+)(用户|人群|群体)", "目标用户"),
            (r"(初学者|新手|入门)", "初学者"),
            (r"(专家|专业人士|资深)", "专业人士"),
            (r"(开发者|程序员|工程师)", "技术人员"),
            (r"(学生|教师|教育)", "教育领域"),
            (r"(客户|用户|消费者)", "终端用户")
        ]

        for pattern, audience_type in audience_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) >= 2:
                    return f"{audience_type}: {match.group(2)}"
                else:
                    return audience_type

        # 从个人上下文中提取
        personal_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.PERSONAL]
        if personal_contexts:
            return f"基于用户偏好: {personal_contexts[0].content}"

        return None

    async def _identify_output_format(self, text: str,
                                    contexts: List[ExtractedContext]) -> Optional[str]:
        """识别期望的输出格式"""
        format_patterns = [
            (r"JSON", "JSON格式"),
            (r"(表格|table)", "表格格式"),
            (r"(列表|清单)", "列表格式"),
            (r"(段落|文章)", "段落文本"),
            (r"(步骤|流程)", "步骤化"),
            (r"markdown", "Markdown格式"),
            (r"(代码|code)", "代码格式")
        ]

        for pattern, format_type in format_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return format_type

        return None

    async def _identify_tone_preferences(self, text: str,
                                       contexts: List[ExtractedContext]) -> List[str]:
        """识别语调偏好"""
        tone_patterns = [
            (r"(正式|严肃|庄重)", "正式"),
            (r"(友好|亲切|温和)", "友好"),
            (r"(专业|权威|严谨)", "专业"),
            (r"(轻松|随意|自然)", "轻松"),
            (r"(创意|活泼|有趣)", "创意"),
            (r"(简洁|直接|明确)", "简洁")
        ]

        preferences = []
        for pattern, tone in tone_patterns:
            if re.search(pattern, text):
                preferences.append(tone)

        return list(set(preferences))

    async def _extract_examples(self, text: str,
                              contexts: List[ExtractedContext]) -> List[str]:
        """提取用户提供的示例"""
        examples = []

        # 从示例上下文中提取
        example_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.EXAMPLE]
        for ctx in example_contexts:
            examples.append(ctx.content)

        return examples

    async def _extract_references(self, text: str,
                                contexts: List[ExtractedContext]) -> List[str]:
        """提取参考材料"""
        references = []

        # 从参考上下文中提取
        reference_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.REFERENCE]
        for ctx in reference_contexts:
            references.append(ctx.content)

        # 使用模式匹配提取URL或文档引用
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        references.extend(urls)

        return list(set(references))

    async def _assess_parsing_quality(self, parsed_requirements: ParsedRequirements,
                                    original_text: str) -> List[QualityMetric]:
        """评估解析质量"""
        metrics = []

        # 意图识别质量
        intent_quality = parsed_requirements.intent.confidence
        metrics.append(QualityMetric(
            metric_name="intent_recognition",
            score=intent_quality,
            description="意图识别准确性"
        ))

        # 上下文覆盖度
        context_coverage = min(1.0, len(parsed_requirements.extracted_contexts) / 5)
        metrics.append(QualityMetric(
            metric_name="context_coverage",
            score=context_coverage,
            description="上下文信息覆盖度"
        ))

        # 需求完整性
        requirement_completeness = min(1.0, len(parsed_requirements.key_requirements) / 3)
        metrics.append(QualityMetric(
            metric_name="requirement_completeness",
            score=requirement_completeness,
            description="需求提取完整性"
        ))

        # 信息密度
        info_density = min(1.0, (len(parsed_requirements.key_requirements) +
                                len(parsed_requirements.constraints) +
                                len(parsed_requirements.extracted_contexts)) / len(original_text) * 100)
        metrics.append(QualityMetric(
            metric_name="information_density",
            score=info_density,
            description="信息提取密度"
        ))

        return metrics

    async def _calculate_overall_confidence(self, parsed_requirements: ParsedRequirements) -> float:
        """计算整体置信度"""
        factors = []

        # 意图置信度权重 40%
        factors.append(parsed_requirements.intent.confidence * 0.4)

        # 质量指标平均分权重 30%
        if parsed_requirements.parsing_quality:
            quality_avg = sum(m.score for m in parsed_requirements.parsing_quality) / len(parsed_requirements.parsing_quality)
            factors.append(quality_avg * 0.3)

        # 领域识别置信度权重 20%
        if parsed_requirements.domain_info:
            factors.append(parsed_requirements.domain_info.confidence * 0.2)
        else:
            factors.append(0.5 * 0.2)  # 没有领域信息时给中等分

        # 信息完整性权重 10%
        completeness = min(1.0, (len(parsed_requirements.key_requirements) / 3 +
                                len(parsed_requirements.extracted_contexts) / 5) / 2)
        factors.append(completeness * 0.1)

        return sum(factors)

    async def _generate_suggestions(self, parsed_requirements: ParsedRequirements) -> Tuple[List[str], List[str], List[str]]:
        """生成改进建议、警告和缺失信息提示"""
        suggestions = []
        warnings = []
        missing_info = []

        # 基于置信度生成建议
        if parsed_requirements.overall_confidence < 0.7:
            suggestions.append("建议提供更具体的需求描述以提高解析准确性")

        if parsed_requirements.intent.confidence < 0.5:
            warnings.append("用户意图识别置信度较低，可能需要进一步确认")

        # 检查关键信息缺失
        if not parsed_requirements.key_requirements:
            missing_info.append("缺少明确的功能需求描述")

        if not parsed_requirements.target_audience:
            missing_info.append("未指定目标受众")

        if not parsed_requirements.expected_output_format:
            missing_info.append("未指定期望的输出格式")

        if not parsed_requirements.domain_info:
            missing_info.append("未识别到特定领域信息")

        # 基于复杂度生成建议
        if parsed_requirements.complexity_estimate == ComplexityLevel.ADVANCED:
            suggestions.append("需求较为复杂，建议分步骤实现")

        if parsed_requirements.complexity_estimate == ComplexityLevel.SIMPLE:
            suggestions.append("需求相对简单，可以考虑添加更多具体要求")

        return suggestions, warnings, missing_info

    def _validate_input(self, text: str) -> None:
        """验证输入"""
        if not text:
            raise RequirementsValidationError("输入文本不能为空")

        text = text.strip()
        if len(text) < self.config.min_input_length:
            raise RequirementsValidationError(
                f"输入文本过短，至少需要 {self.config.min_input_length} 个字符"
            )

        if len(text) > self.config.max_input_length:
            raise RequirementsValidationError(
                f"输入文本过长，不能超过 {self.config.max_input_length} 个字符"
            )

    async def _validate_parsed_requirements(self, parsed_requirements: ParsedRequirements) -> None:
        """验证解析结果"""
        validation_errors = []

        # 检查是否识别了主要目标
        if self.config.require_main_objective and not parsed_requirements.main_objective:
            validation_errors.append("未能识别主要目标")

        # 检查整体质量
        if parsed_requirements.overall_confidence < self.config.min_quality_score:
            validation_errors.append(f"解析质量过低: {parsed_requirements.overall_confidence:.2f}")

        # 检查意图置信度
        if parsed_requirements.intent.confidence < self.config.intent_confidence_threshold:
            validation_errors.append(f"意图识别置信度过低: {parsed_requirements.intent.confidence:.2f}")

        if validation_errors:
            raise RequirementsValidationError(
                "解析结果验证失败",
                validation_errors=validation_errors
            )

    def _get_from_cache(self, text: str) -> Optional[ParsedRequirements]:
        """从缓存获取解析结果"""
        cache_key = self._generate_cache_key(text)
        return self._parsing_cache.get(cache_key)

    def _add_to_cache(self, text: str, result: ParsedRequirements) -> None:
        """添加到缓存"""
        cache_key = self._generate_cache_key(text)
        self._parsing_cache[cache_key] = result

        # 简单的缓存大小限制
        if len(self._parsing_cache) > 100:
            # 删除最旧的条目（简化实现）
            oldest_key = next(iter(self._parsing_cache))
            del self._parsing_cache[oldest_key]

    def _generate_cache_key(self, text: str) -> str:
        """生成缓存键"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _update_stats(self, start_time: float, success: bool, cache_hit: bool = False) -> None:
        """更新统计信息"""
        processing_time = time.time() - start_time

        self._parsing_stats["total_parsed"] += 1

        if cache_hit:
            self._parsing_stats["cache_hits"] += 1

        if success:
            # 更新平均处理时间
            current_avg = self._parsing_stats["average_processing_time"]
            total_count = self._parsing_stats["total_parsed"] - self._parsing_stats["failures"]
            self._parsing_stats["average_processing_time"] = (
                (current_avg * (total_count - 1) + processing_time) / total_count
            )
        else:
            self._parsing_stats["failures"] += 1

        # 更新成功率
        total = self._parsing_stats["total_parsed"]
        failures = self._parsing_stats["failures"]
        self._parsing_stats["success_rate"] = (total - failures) / total if total > 0 else 0.0

    def get_parsing_statistics(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        stats = self._parsing_stats.copy()
        stats["cache_size"] = len(self._parsing_cache)
        stats["cache_hit_rate"] = (stats["cache_hits"] / stats["total_parsed"]
                                  if stats["total_parsed"] > 0 else 0.0)
        return stats

    def clear_cache(self) -> None:
        """清空缓存"""
        self._parsing_cache.clear()

    async def batch_parse_requirements(self, texts: List[str]) -> List[ParsedRequirements]:
        """批量解析需求"""
        tasks = [self.parse_requirements(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量解析第 {i+1} 项失败: {str(result)}")
                # 创建错误结果
                error_result = ParsedRequirements(
                    original_input=texts[i],
                    main_objective="解析失败",
                    overall_confidence=0.0
                )
                error_result.warnings = [f"解析失败: {str(result)}"]
                final_results.append(error_result)
            else:
                final_results.append(result)

        return final_results

    @asynccontextmanager
    async def parsing_session(self, session_config: Optional[Dict[str, Any]] = None):
        """解析会话上下文管理器"""
        session_start = time.time()
        session_stats = {"parsed_count": 0, "errors": 0}

        try:
            yield self
        finally:
            session_duration = time.time() - session_start
            logger.info(f"解析会话结束 - 时长: {session_duration:.2f}s, "
                       f"解析数量: {session_stats['parsed_count']}, "
                       f"错误数量: {session_stats['errors']}")

# 导入缺失的模块
import re