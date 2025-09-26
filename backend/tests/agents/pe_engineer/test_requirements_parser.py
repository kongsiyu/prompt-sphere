"""
需求解析器测试

测试 RequirementsParser 类的完整功能，包括需求解析流程、
质量评估、缓存机制等。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from app.agents.pe_engineer.RequirementsParser import RequirementsParser
from app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, ExtractedContext, DomainInfo,
    TechnicalRequirement, IntentCategory, ContextType, PromptType,
    ComplexityLevel, RequirementsParsingConfig, RequirementsValidationError
)


class TestRequirementsParser:
    """测试需求解析器"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RequirementsParsingConfig(
            min_input_length=5,
            max_input_length=1000,
            intent_confidence_threshold=0.3,
            enable_caching=True
        )

    @pytest.fixture
    def parser(self, config):
        """创建解析器实例"""
        return RequirementsParser(config)

    @pytest.mark.asyncio
    async def test_init(self, parser):
        """测试初始化"""
        assert parser is not None
        assert parser.config is not None
        assert parser.intent_parser is not None
        assert parser.context_extractor is not None
        assert isinstance(parser._parsing_cache, dict)

    @pytest.mark.asyncio
    async def test_parse_requirements_basic(self, parser):
        """测试基本需求解析"""
        text = "帮我创建一个用于代码生成的提示词"
        result = await parser.parse_requirements(text)

        # 验证基本结构
        assert isinstance(result, ParsedRequirements)
        assert result.request_id is not None
        assert result.original_input == text
        assert isinstance(result.parsed_at, datetime)

        # 验证意图解析
        assert result.intent is not None
        assert result.intent.category == IntentCategory.CREATE_PROMPT

        # 验证主要目标
        assert result.main_objective is not None
        assert len(result.main_objective) > 0

        # 验证置信度
        assert 0.0 <= result.overall_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_parse_requirements_complex(self, parser):
        """测试复杂需求解析"""
        complex_text = """
        我是一名前端开发工程师，使用React和TypeScript技术栈。
        需要创建一个代码生成提示词，用于生成React组件。
        要求：
        1. 代码符合ESLint规范
        2. 包含PropTypes类型定义
        3. 支持响应式设计
        4. 输出JSON格式
        不能包含第三方库依赖，必须是纯React代码。
        比如生成一个用户卡片组件。
        """

        result = await parser.parse_requirements(complex_text)

        # 验证基本结构
        assert isinstance(result, ParsedRequirements)
        assert result.intent.category == IntentCategory.CREATE_PROMPT

        # 验证上下文提取
        assert len(result.extracted_contexts) > 0
        context_types = set(ctx.context_type for ctx in result.extracted_contexts)
        expected_types = {ContextType.TECHNICAL, ContextType.CONSTRAINT}
        assert len(context_types.intersection(expected_types)) > 0

        # 验证领域识别
        assert result.domain_info is not None
        assert result.domain_info.name == "软件开发"

        # 验证技术需求
        assert len(result.technical_requirements) > 0

        # 验证关键需求
        assert len(result.key_requirements) > 0

        # 验证约束条件
        assert len(result.constraints) > 0

        # 验证提示词类型建议
        assert result.suggested_prompt_type in [PromptType.CODE_GENERATION, PromptType.TASK_SPECIFIC]

        # 验证复杂度评估
        assert result.complexity_estimate in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]

        # 验证示例提取
        assert len(result.provided_examples) > 0

    @pytest.mark.asyncio
    async def test_input_validation(self, parser):
        """测试输入验证"""
        # 空输入
        with pytest.raises(RequirementsValidationError):
            await parser.parse_requirements("")

        # 过短输入
        with pytest.raises(RequirementsValidationError):
            await parser.parse_requirements("hi")

        # 过长输入
        long_text = "a" * 2000
        with pytest.raises(RequirementsValidationError):
            await parser.parse_requirements(long_text)

        # None输入
        with pytest.raises(RequirementsValidationError):
            await parser.parse_requirements(None)

    @pytest.mark.asyncio
    async def test_caching_mechanism(self, parser):
        """测试缓存机制"""
        text = "创建一个简单的提示词"

        # 第一次解析
        result1 = await parser.parse_requirements(text)
        stats1 = parser.get_parsing_statistics()

        # 第二次解析相同内容（应该使用缓存）
        result2 = await parser.parse_requirements(text)
        stats2 = parser.get_parsing_statistics()

        # 验证缓存生效
        assert stats2["cache_hits"] > stats1["cache_hits"]
        assert result1.request_id != result2.request_id  # 缓存结果会更新时间戳

    @pytest.mark.asyncio
    async def test_different_intent_categories(self, parser):
        """测试不同意图类别的解析"""
        test_cases = [
            ("帮我创建一个新的提示词", IntentCategory.CREATE_PROMPT),
            ("优化这个现有的prompt", IntentCategory.OPTIMIZE_PROMPT),
            ("分析一下这个提示词的质量", IntentCategory.ANALYZE_PROMPT),
            ("有没有相关的模板参考", IntentCategory.GET_TEMPLATE),
            ("什么是提示词工程", IntentCategory.GENERAL_INQUIRY),
        ]

        for text, expected_category in test_cases:
            result = await parser.parse_requirements(text)
            assert result.intent.category == expected_category

    @pytest.mark.asyncio
    async def test_prompt_type_suggestion(self, parser):
        """测试提示词类型建议"""
        test_cases = [
            ("创建一个代码生成的提示词", PromptType.CODE_GENERATION),
            ("写一个创意文案的prompt", PromptType.CREATIVE),
            ("分析数据的提示词", PromptType.ANALYTICAL),
            ("对话机器人的指令", PromptType.CONVERSATIONAL),
            ("翻译任务的prompt", PromptType.TRANSLATION),
        ]

        for text, expected_type in test_cases:
            result = await parser.parse_requirements(text)
            # 允许一定的灵活性，因为类型推断可能有多种合理结果
            assert result.suggested_prompt_type in [expected_type, PromptType.TASK_SPECIFIC, PromptType.GENERAL]

    @pytest.mark.asyncio
    async def test_complexity_assessment(self, parser):
        """测试复杂度评估"""
        # 简单需求
        simple_text = "创建一个简单的提示词"
        simple_result = await parser.parse_requirements(simple_text)

        # 复杂需求
        complex_text = """
        创建一个高级的多步骤代码生成提示词，需要支持多种编程语言，
        包含错误处理、性能优化、安全检查、文档生成等功能，
        要求输出格式为结构化JSON，支持增量更新和版本控制，
        需要集成测试用例生成和代码审查建议。
        """
        complex_result = await parser.parse_requirements(complex_text)

        # 验证复杂度差异
        complexity_levels = {
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.COMPLEX: 3,
            ComplexityLevel.ADVANCED: 4
        }

        simple_level = complexity_levels[simple_result.complexity_estimate]
        complex_level = complexity_levels[complex_result.complexity_estimate]

        assert complex_level > simple_level

    @pytest.mark.asyncio
    async def test_target_audience_identification(self, parser):
        """测试目标受众识别"""
        test_cases = [
            "为初学者创建一个简单的提示词",
            "给专业开发者提供高级prompt",
            "面向学生的教学用提示词",
            "针对企业用户的业务prompt"
        ]

        for text in test_cases:
            result = await parser.parse_requirements(text)
            # 如果识别到目标受众，应该是字符串
            if result.target_audience:
                assert isinstance(result.target_audience, str)
                assert len(result.target_audience) > 0

    @pytest.mark.asyncio
    async def test_output_format_identification(self, parser):
        """测试输出格式识别"""
        test_cases = [
            ("输出JSON格式的结果", "JSON"),
            ("生成表格形式的数据", "表格"),
            ("返回列表格式", "列表"),
            ("使用markdown格式", "Markdown"),
        ]

        for text, expected_format in test_cases:
            result = await parser.parse_requirements(text)
            if result.expected_output_format:
                assert expected_format.lower() in result.expected_output_format.lower()

    @pytest.mark.asyncio
    async def test_tone_preferences_identification(self, parser):
        """测试语调偏好识别"""
        test_cases = [
            "使用正式专业的语调",
            "保持友好亲切的风格",
            "简洁直接的表达方式",
            "创意活泼的语言风格"
        ]

        for text in test_cases:
            result = await parser.parse_requirements(text)
            assert isinstance(result.tone_preferences, list)

    @pytest.mark.asyncio
    async def test_quality_assessment(self, parser):
        """测试解析质量评估"""
        high_quality_text = """
        我是一名资深Python开发工程师，专门从事Web API开发。
        需要创建一个代码生成提示词，用于生成RESTful API接口。
        具体要求包括：使用Flask框架，包含JWT认证，支持CRUD操作，
        返回JSON格式，符合OpenAPI 3.0规范。
        例如：用户管理接口，包含注册、登录、查询、更新功能。
        """

        result = await parser.parse_requirements(high_quality_text)

        # 验证质量指标
        assert len(result.parsing_quality) > 0
        for metric in result.parsing_quality:
            assert 0.0 <= metric.score <= 1.0
            assert metric.metric_name is not None
            assert metric.description is not None

        # 高质量输入应该有较高的整体置信度
        assert result.overall_confidence > 0.5

    @pytest.mark.asyncio
    async def test_suggestions_and_warnings(self, parser):
        """测试建议和警告生成"""
        # 低质量输入应该生成建议和警告
        low_quality_text = "做个东西"
        result = await parser.parse_requirements(low_quality_text)

        # 应该有建议或警告
        assert len(result.suggestions) > 0 or len(result.warnings) > 0 or len(result.missing_info) > 0

    @pytest.mark.asyncio
    async def test_batch_parse_requirements(self, parser):
        """测试批量解析"""
        texts = [
            "创建代码生成提示词",
            "优化现有prompt",
            "分析提示词质量",
            "无效输入测试"
        ]

        results = await parser.batch_parse_requirements(texts)

        assert len(results) == len(texts)
        assert all(isinstance(result, ParsedRequirements) for result in results)

        # 验证不同的意图类型
        categories = [result.intent.category for result in results]
        assert len(set(categories)) > 1  # 应该有多种不同的意图

    @pytest.mark.asyncio
    async def test_parsing_session_context_manager(self, parser):
        """测试解析会话上下文管理器"""
        async with parser.parsing_session() as session_parser:
            result = await session_parser.parse_requirements("创建提示词")
            assert isinstance(result, ParsedRequirements)

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, parser):
        """测试统计信息跟踪"""
        # 初始统计
        initial_stats = parser.get_parsing_statistics()

        # 执行一些解析
        await parser.parse_requirements("创建提示词")
        await parser.parse_requirements("优化prompt")

        # 尝试一个失败的解析
        try:
            await parser.parse_requirements("")
        except RequirementsValidationError:
            pass

        # 检查统计更新
        final_stats = parser.get_parsing_statistics()

        assert final_stats["total_parsed"] > initial_stats["total_parsed"]
        assert final_stats["failures"] > initial_stats["failures"]
        assert "success_rate" in final_stats
        assert "average_processing_time" in final_stats

    @pytest.mark.asyncio
    async def test_cache_management(self, parser):
        """测试缓存管理"""
        # 添加一些缓存
        await parser.parse_requirements("测试缓存1")
        await parser.parse_requirements("测试缓存2")

        # 检查缓存大小
        stats = parser.get_parsing_statistics()
        initial_cache_size = stats["cache_size"]
        assert initial_cache_size > 0

        # 清空缓存
        parser.clear_cache()

        # 验证缓存已清空
        stats = parser.get_parsing_statistics()
        assert stats["cache_size"] == 0

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, parser):
        """测试处理时间跟踪"""
        result = await parser.parse_requirements("创建一个复杂的多步骤提示词")

        assert result.processing_time_ms > 0
        assert isinstance(result.processing_time_ms, int)

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, parser):
        """测试错误处理和恢复"""
        # 模拟内部组件错误
        with patch.object(parser.intent_parser, 'parse_intent', side_effect=Exception("测试错误")):
            with pytest.raises(RequirementsValidationError):
                await parser.parse_requirements("测试错误处理")

        # 验证系统仍然可以处理正常请求
        result = await parser.parse_requirements("正常请求")
        assert isinstance(result, ParsedRequirements)

    @pytest.mark.asyncio
    async def test_metadata_handling(self, parser):
        """测试元数据处理"""
        context = {"user_id": "test_user", "session_id": "test_session"}
        result = await parser.parse_requirements("创建提示词", context=context)

        # 验证基本结构（元数据处理是可选功能）
        assert isinstance(result, ParsedRequirements)
        assert hasattr(result, 'metadata')
        assert isinstance(result.metadata, dict)

    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, parser):
        """测试并发解析"""
        texts = [f"创建提示词{i}" for i in range(10)]

        # 并发执行解析
        tasks = [parser.parse_requirements(text) for text in texts]
        results = await asyncio.gather(*tasks)

        # 验证所有解析都成功
        assert len(results) == len(texts)
        assert all(isinstance(result, ParsedRequirements) for result in results)

        # 验证request_id的唯一性
        request_ids = [result.request_id for result in results]
        assert len(set(request_ids)) == len(request_ids)

    @pytest.mark.asyncio
    async def test_configuration_impact(self):
        """测试配置对解析的影响"""
        # 严格配置
        strict_config = RequirementsParsingConfig(
            min_input_length=20,
            intent_confidence_threshold=0.8,
            min_quality_score=0.8
        )
        strict_parser = RequirementsParser(strict_config)

        # 宽松配置
        lenient_config = RequirementsParsingConfig(
            min_input_length=5,
            intent_confidence_threshold=0.2,
            min_quality_score=0.2
        )
        lenient_parser = RequirementsParser(lenient_config)

        test_text = "做个简单的东西"

        # 严格配置可能拒绝
        try:
            strict_result = await strict_parser.parse_requirements(test_text)
        except RequirementsValidationError:
            strict_result = None

        # 宽松配置应该接受
        lenient_result = await lenient_parser.parse_requirements(test_text)

        assert isinstance(lenient_result, ParsedRequirements)

    @pytest.mark.asyncio
    async def test_edge_case_inputs(self, parser):
        """测试边界情况输入"""
        edge_cases = [
            "a" * 500,  # 长重复字符
            "123456789",  # 纯数字
            "！@#￥%…&*（）",  # 特殊字符
            "English only text without Chinese",  # 纯英文
            "混合 mixed 语言 language 文本",  # 混合语言
        ]

        for case in edge_cases:
            try:
                result = await parser.parse_requirements(case)
                assert isinstance(result, ParsedRequirements)
                # 边界情况可能有较低的置信度
                assert 0.0 <= result.overall_confidence <= 1.0
            except RequirementsValidationError:
                # 某些边界情况可能被验证拒绝，这是正常的
                pass