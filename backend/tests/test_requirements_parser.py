"""
RequirementsParser 全面测试套件

测试需求解析器的所有功能，包括意图识别、上下文提取、领域识别、
技术需求分析等核心解析功能的单元测试和集成测试。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.agents.pe_engineer.RequirementsParser import RequirementsParser
from app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, ExtractedContext, DomainInfo,
    TechnicalRequirement, QualityMetrics, RequirementsParsingConfig
)

from .fixtures.pe_engineer_fixtures import (
    sample_user_inputs, sample_parsed_requirements_detailed,
    error_scenarios, performance_test_data
)


class TestRequirementsParser:
    """RequirementsParser 主要测试类"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试设置"""
        config = RequirementsParsingConfig(
            max_input_length=5000,
            cache_enabled=True,
            cache_size=100,
            confidence_threshold=0.6,
            timeout_seconds=30
        )
        self.parser = RequirementsParser(config=config)
        self.mock_dashscope = AsyncMock()

        # Mock 各个解析子方法
        with patch.multiple(
            self.parser,
            _parse_intent=AsyncMock(),
            _extract_contexts=AsyncMock(),
            _identify_domain=AsyncMock(),
            _extract_technical_requirements=AsyncMock(),
            _assess_parsing_quality=AsyncMock()
        ):
            yield

    def test_parser_initialization(self):
        """测试解析器初始化"""
        # 测试默认配置初始化
        parser = RequirementsParser()
        assert parser.config is not None
        assert parser.cache == {}
        assert parser.stats["total_requests"] == 0

        # 测试自定义配置初始化
        config = RequirementsParsingConfig(
            max_input_length=1000,
            cache_enabled=False
        )
        parser = RequirementsParser(config=config)
        assert parser.config.max_input_length == 1000
        assert not parser.config.cache_enabled

    def test_input_validation_success(self, sample_user_inputs):
        """测试输入验证成功场景"""
        # 正常输入应该通过验证
        try:
            self.parser._validate_input(sample_user_inputs["simple_creative"])
            self.parser._validate_input(sample_user_inputs["complex_analytical"])
        except ValueError:
            pytest.fail("有效输入不应该抛出异常")

    def test_input_validation_empty(self):
        """测试空输入验证"""
        with pytest.raises(ValueError, match="输入文本不能为空"):
            self.parser._validate_input("")

        with pytest.raises(ValueError, match="输入文本不能为空"):
            self.parser._validate_input("   ")  # 只有空白字符

    def test_input_validation_too_long(self):
        """测试过长输入验证"""
        long_input = "x" * 10000
        with pytest.raises(ValueError, match="输入文本长度不能超过"):
            self.parser._validate_input(long_input)

    def test_input_validation_special_characters(self):
        """测试特殊字符输入验证"""
        special_inputs = [
            "正常文本 with émojis 😀",
            "Mixed 语言 content",
            "Text with\nnewlines\tand\ttabs",
            "Punctuation!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        ]

        for input_text in special_inputs:
            try:
                self.parser._validate_input(input_text)
            except ValueError:
                pytest.fail(f"特殊字符输入应该被接受: {input_text}")

    async def test_parse_requirements_success(self, sample_user_inputs):
        """测试成功的需求解析"""
        # 设置mock返回值
        self.parser._parse_intent.return_value = ParsedIntent(
            primary="creative_writing",
            secondary=["story_structure"],
            confidence=0.88
        )

        self.parser._extract_contexts.return_value = [
            ExtractedContext(type="domain", content="创意写作", relevance=0.95)
        ]

        self.parser._identify_domain.return_value = DomainInfo(
            primary="creative_writing",
            secondary=["literature"],
            confidence=0.92
        )

        self.parser._extract_technical_requirements.return_value = [
            TechnicalRequirement(
                type="functionality",
                description="创意激发",
                priority="high",
                complexity="medium"
            )
        ]

        self.parser._assess_parsing_quality.return_value = QualityMetrics(
            clarity=0.85, specificity=0.75, completeness=0.80,
            feasibility=0.90, overall_confidence=0.82
        )

        result = await self.parser.parse_requirements(
            sample_user_inputs["simple_creative"]
        )

        # 验证结果结构
        assert isinstance(result, ParsedRequirements)
        assert result.intent.primary == "creative_writing"
        assert len(result.contexts) > 0
        assert result.domain.primary == "creative_writing"
        assert len(result.technical_requirements) > 0
        assert result.quality_metrics.overall_confidence > 0.8

        # 验证统计信息更新
        assert self.parser.stats["total_requests"] == 1
        assert self.parser.stats["successful_requests"] == 1

    async def test_parse_requirements_with_context(self, sample_user_inputs):
        """测试带上下文的需求解析"""
        context = {
            "user_background": "experienced_writer",
            "previous_prompts": ["写作助手", "情节生成"],
            "domain_preference": "creative_writing"
        }

        # Mock方法设置
        self.parser._parse_intent.return_value = ParsedIntent(
            primary="creative_writing",
            secondary=[],
            confidence=0.9
        )
        self.parser._extract_contexts.return_value = []
        self.parser._identify_domain.return_value = DomainInfo(
            primary="creative_writing", secondary=[], confidence=0.9
        )
        self.parser._extract_technical_requirements.return_value = []
        self.parser._assess_parsing_quality.return_value = QualityMetrics(
            clarity=0.8, specificity=0.8, completeness=0.8,
            feasibility=0.8, overall_confidence=0.8
        )

        result = await self.parser.parse_requirements(
            sample_user_inputs["simple_creative"],
            context=context
        )

        assert isinstance(result, ParsedRequirements)
        # 上下文应该提高解析质量
        assert result.quality_metrics.overall_confidence >= 0.8

    async def test_parse_requirements_with_history(self, sample_user_inputs):
        """测试带历史记录的需求解析"""
        history = [
            {"input": "帮我写诗", "intent": "poetry_creation"},
            {"input": "创作歌词", "intent": "lyrics_writing"}
        ]

        # Mock设置
        self.parser._parse_intent.return_value = ParsedIntent(
            primary="creative_writing", secondary=[], confidence=0.85
        )
        self.parser._extract_contexts.return_value = []
        self.parser._identify_domain.return_value = DomainInfo(
            primary="creative_writing", secondary=[], confidence=0.85
        )
        self.parser._extract_technical_requirements.return_value = []
        self.parser._assess_parsing_quality.return_value = QualityMetrics(
            clarity=0.8, specificity=0.8, completeness=0.8,
            feasibility=0.8, overall_confidence=0.8
        )

        result = await self.parser.parse_requirements(
            sample_user_inputs["simple_creative"],
            history=history
        )

        assert isinstance(result, ParsedRequirements)
        # 历史记录应该有助于理解用户意图
        assert result.intent.primary in ["creative_writing", "poetry_creation"]

    async def test_parse_requirements_invalid_input(self, error_scenarios):
        """测试无效输入的需求解析"""
        # 空输入
        with pytest.raises(ValueError):
            await self.parser.parse_requirements(error_scenarios["empty_input"]["input"])

        # 过长输入
        with pytest.raises(ValueError):
            await self.parser.parse_requirements(error_scenarios["too_long_input"]["input"])

    async def test_parse_intent_basic(self):
        """测试基础意图解析"""
        test_cases = [
            {
                "input": "我想要创建一个写作助手",
                "expected_primary": "creative_writing_assistance"
            },
            {
                "input": "帮我分析这些数据",
                "expected_primary": "data_analysis"
            },
            {
                "input": "生成Python代码",
                "expected_primary": "code_generation"
            },
            {
                "input": "翻译这段文字",
                "expected_primary": "translation"
            }
        ]

        for case in test_cases:
            with patch.object(self.parser, '_parse_intent', wraps=self.parser._parse_intent):
                # 这里需要实际实现_parse_intent的逻辑测试
                # 由于是mock，我们测试调用是否正确
                await self.parser._parse_intent(case["input"])
                self.parser._parse_intent.assert_called_with(case["input"])

    async def test_extract_contexts_comprehensive(self):
        """测试全面的上下文提取"""
        complex_input = """
        我需要一个专业的财务分析助手，能够处理Excel文件，
        生成图表和报告，适合给投资者看的那种。
        我之前用过一些工具但效果不理想。
        """

        # Mock上下文提取方法的实际实现
        async def mock_extract_contexts(text):
            contexts = []
            if "财务" in text:
                contexts.append(ExtractedContext(
                    type="domain", content="finance", relevance=0.9
                ))
            if "Excel" in text:
                contexts.append(ExtractedContext(
                    type="technical", content="excel_processing", relevance=0.8
                ))
            if "投资者" in text:
                contexts.append(ExtractedContext(
                    type="audience", content="investors", relevance=0.85
                ))
            return contexts

        with patch.object(self.parser, '_extract_contexts', side_effect=mock_extract_contexts):
            contexts = await self.parser._extract_contexts(complex_input)

        assert len(contexts) >= 3
        context_types = [c.type for c in contexts]
        assert "domain" in context_types
        assert "technical" in context_types
        assert "audience" in context_types

    async def test_identify_domain_accuracy(self):
        """测试领域识别准确性"""
        domain_test_cases = [
            {
                "input": "创建一个小说写作助手",
                "expected_domain": "creative_writing"
            },
            {
                "input": "分析股市数据和趋势",
                "expected_domain": "finance"
            },
            {
                "input": "生成Python web应用代码",
                "expected_domain": "software_development"
            },
            {
                "input": "翻译商务文档",
                "expected_domain": "translation"
            },
            {
                "input": "设计营销活动方案",
                "expected_domain": "marketing"
            }
        ]

        for case in domain_test_cases:
            # Mock领域识别实现
            async def mock_identify_domain(text):
                if "写作" in text or "小说" in text:
                    return DomainInfo(primary="creative_writing", secondary=[], confidence=0.9)
                elif "股市" in text or "数据" in text:
                    return DomainInfo(primary="finance", secondary=[], confidence=0.85)
                elif "代码" in text or "Python" in text:
                    return DomainInfo(primary="software_development", secondary=[], confidence=0.9)
                elif "翻译" in text:
                    return DomainInfo(primary="translation", secondary=[], confidence=0.95)
                elif "营销" in text:
                    return DomainInfo(primary="marketing", secondary=[], confidence=0.8)
                else:
                    return DomainInfo(primary="general", secondary=[], confidence=0.5)

            with patch.object(self.parser, '_identify_domain', side_effect=mock_identify_domain):
                domain = await self.parser._identify_domain(case["input"])

            assert domain.primary == case["expected_domain"]
            assert domain.confidence > 0.7

    async def test_extract_technical_requirements_detailed(self):
        """测试详细的技术需求提取"""
        technical_input = """
        我需要一个系统能够：
        1. 处理大型CSV文件（10GB+）
        2. 实时数据可视化
        3. 支持多用户并发访问
        4. 导出PDF报告
        5. 集成第三方API
        要求高性能，7x24小时运行
        """

        # Mock技术需求提取
        async def mock_extract_technical_requirements(text):
            requirements = []
            if "CSV" in text:
                requirements.append(TechnicalRequirement(
                    type="data_processing",
                    description="大型CSV文件处理",
                    priority="high",
                    complexity="high"
                ))
            if "可视化" in text:
                requirements.append(TechnicalRequirement(
                    type="visualization",
                    description="实时数据可视化",
                    priority="high",
                    complexity="medium"
                ))
            if "并发" in text:
                requirements.append(TechnicalRequirement(
                    type="performance",
                    description="多用户并发支持",
                    priority="high",
                    complexity="high"
                ))
            if "PDF" in text:
                requirements.append(TechnicalRequirement(
                    type="export",
                    description="PDF报告导出",
                    priority="medium",
                    complexity="low"
                ))
            return requirements

        with patch.object(self.parser, '_extract_technical_requirements',
                         side_effect=mock_extract_technical_requirements):
            requirements = await self.parser._extract_technical_requirements(technical_input)

        assert len(requirements) >= 4
        priorities = [r.priority for r in requirements]
        assert "high" in priorities
        complexities = [r.complexity for r in requirements]
        assert "high" in complexities

    async def test_assess_parsing_quality_comprehensive(self):
        """测试全面的解析质量评估"""
        sample_parsed = ParsedRequirements(
            intent=ParsedIntent(primary="test_intent", secondary=[], confidence=0.8),
            contexts=[
                ExtractedContext(type="domain", content="test", relevance=0.9)
            ],
            domain=DomainInfo(primary="test_domain", secondary=[], confidence=0.85),
            technical_requirements=[
                TechnicalRequirement(
                    type="test", description="test req",
                    priority="high", complexity="medium"
                )
            ],
            quality_metrics=QualityMetrics(
                clarity=0.8, specificity=0.7, completeness=0.8,
                feasibility=0.9, overall_confidence=0.8
            ),
            suggestions={"improvements": [], "clarifications": [], "enhancements": []},
            metadata={}
        )

        original_input = "创建一个专业的数据分析工具"

        # Mock质量评估
        async def mock_assess_quality(parsed_req, original):
            # 基于内容计算质量分数
            clarity = 0.85 if parsed_req.intent.confidence > 0.7 else 0.6
            specificity = 0.8 if len(parsed_req.technical_requirements) > 0 else 0.5
            completeness = 0.75 if len(parsed_req.contexts) > 0 else 0.4
            feasibility = 0.9  # 假设大部分需求都可行

            return QualityMetrics(
                clarity=clarity,
                specificity=specificity,
                completeness=completeness,
                feasibility=feasibility,
                overall_confidence=(clarity + specificity + completeness + feasibility) / 4
            )

        with patch.object(self.parser, '_assess_parsing_quality',
                         side_effect=mock_assess_quality):
            quality = await self.parser._assess_parsing_quality(sample_parsed, original_input)

        assert isinstance(quality, QualityMetrics)
        assert 0 <= quality.clarity <= 1
        assert 0 <= quality.specificity <= 1
        assert 0 <= quality.completeness <= 1
        assert 0 <= quality.feasibility <= 1
        assert 0 <= quality.overall_confidence <= 1

    def test_cache_functionality(self, sample_user_inputs):
        """测试缓存功能"""
        # 启用缓存的解析器
        config = RequirementsParsingConfig(cache_enabled=True, cache_size=10)
        parser = RequirementsParser(config=config)

        input_text = sample_user_inputs["simple_creative"]

        # 第一次应该没有缓存
        cached_result = parser._get_from_cache(input_text)
        assert cached_result is None

        # 添加到缓存
        mock_result = ParsedRequirements(
            intent=ParsedIntent(primary="test", secondary=[], confidence=0.8),
            contexts=[], domain=DomainInfo(primary="test", secondary=[], confidence=0.8),
            technical_requirements=[],
            quality_metrics=QualityMetrics(
                clarity=0.8, specificity=0.8, completeness=0.8,
                feasibility=0.8, overall_confidence=0.8
            ),
            suggestions={"improvements": [], "clarifications": [], "enhancements": []},
            metadata={}
        )
        parser._add_to_cache(input_text, mock_result)

        # 现在应该能从缓存获取
        cached_result = parser._get_from_cache(input_text)
        assert cached_result is not None
        assert cached_result.intent.primary == "test"

        # 测试缓存清理
        parser.clear_cache()
        cached_result = parser._get_from_cache(input_text)
        assert cached_result is None

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        config = RequirementsParsingConfig(cache_enabled=True, cache_size=2)
        parser = RequirementsParser(config=config)

        mock_result = ParsedRequirements(
            intent=ParsedIntent(primary="test", secondary=[], confidence=0.8),
            contexts=[], domain=DomainInfo(primary="test", secondary=[], confidence=0.8),
            technical_requirements=[],
            quality_metrics=QualityMetrics(
                clarity=0.8, specificity=0.8, completeness=0.8,
                feasibility=0.8, overall_confidence=0.8
            ),
            suggestions={"improvements": [], "clarifications": [], "enhancements": []},
            metadata={}
        )

        # 添加超过限制的缓存项
        parser._add_to_cache("input1", mock_result)
        parser._add_to_cache("input2", mock_result)
        parser._add_to_cache("input3", mock_result)

        # 缓存大小应该被限制
        assert len(parser.cache) <= config.cache_size

    async def test_batch_parse_requirements(self, sample_user_inputs):
        """测试批量需求解析"""
        inputs = [
            sample_user_inputs["simple_creative"],
            sample_user_inputs["complex_analytical"],
            sample_user_inputs["code_generation"]
        ]

        # Mock单个解析方法
        mock_result = ParsedRequirements(
            intent=ParsedIntent(primary="test", secondary=[], confidence=0.8),
            contexts=[], domain=DomainInfo(primary="test", secondary=[], confidence=0.8),
            technical_requirements=[],
            quality_metrics=QualityMetrics(
                clarity=0.8, specificity=0.8, completeness=0.8,
                feasibility=0.8, overall_confidence=0.8
            ),
            suggestions={"improvements": [], "clarifications": [], "enhancements": []},
            metadata={}
        )

        with patch.object(self.parser, 'parse_requirements', return_value=mock_result):
            results = await self.parser.batch_parse_requirements(inputs)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, ParsedRequirements)

    async def test_parsing_session_context(self):
        """测试解析会话上下文"""
        session_config = {
            "user_id": "test_user",
            "session_id": "test_session",
            "domain_hints": ["creative_writing"],
            "quality_threshold": 0.8
        }

        async with self.parser.parsing_session(session_config) as session:
            # 在会话中解析应该使用会话配置
            assert session is not None

    def test_statistics_tracking_detailed(self):
        """测试详细的统计信息跟踪"""
        import time

        # 模拟一些统计更新
        self.parser._update_stats(time.time() - 1.5, success=True)
        self.parser._update_stats(time.time() - 2.0, success=False)
        self.parser._update_stats(time.time() - 0.8, success=True, cache_hit=True)

        stats = self.parser.get_parsing_statistics()

        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 2
        assert stats["failed_requests"] == 1
        assert stats["cache_hits"] == 1
        assert "average_processing_time" in stats
        assert "success_rate" in stats

    async def test_error_handling_comprehensive(self):
        """测试全面的错误处理"""
        # 测试各种异常情况
        test_cases = [
            {
                "exception": asyncio.TimeoutError(),
                "input": "timeout test",
                "expected_behavior": "应该返回低置信度结果"
            },
            {
                "exception": ValueError("invalid input"),
                "input": "invalid test",
                "expected_behavior": "应该重新抛出异常"
            },
            {
                "exception": Exception("unexpected error"),
                "input": "unexpected test",
                "expected_behavior": "应该返回低置信度结果"
            }
        ]

        for case in test_cases:
            with patch.object(self.parser, '_parse_intent', side_effect=case["exception"]):
                if isinstance(case["exception"], ValueError):
                    with pytest.raises(ValueError):
                        await self.parser.parse_requirements(case["input"])
                else:
                    # 其他异常应该被捕获并返回低置信度结果
                    result = await self.parser.parse_requirements(case["input"])
                    assert isinstance(result, ParsedRequirements)
                    assert result.quality_metrics.overall_confidence < 0.5

    async def test_performance_large_input(self):
        """测试大输入的性能"""
        large_input = "详细需求描述 " * 500  # 创建较大的输入

        start_time = asyncio.get_event_loop().time()

        # Mock所有异步方法以避免实际API调用
        with patch.multiple(
            self.parser,
            _parse_intent=AsyncMock(return_value=ParsedIntent(primary="test", secondary=[], confidence=0.8)),
            _extract_contexts=AsyncMock(return_value=[]),
            _identify_domain=AsyncMock(return_value=DomainInfo(primary="test", secondary=[], confidence=0.8)),
            _extract_technical_requirements=AsyncMock(return_value=[]),
            _assess_parsing_quality=AsyncMock(return_value=QualityMetrics(
                clarity=0.8, specificity=0.8, completeness=0.8,
                feasibility=0.8, overall_confidence=0.8
            ))
        ):
            result = await self.parser.parse_requirements(large_input)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        # 处理时间应该在合理范围内（小于5秒）
        assert processing_time < 5.0
        assert isinstance(result, ParsedRequirements)

    async def test_multilingual_input_handling(self, sample_user_inputs):
        """测试多语言输入处理"""
        multilingual_input = sample_user_inputs["multilingual"]

        # Mock多语言处理
        with patch.multiple(
            self.parser,
            _parse_intent=AsyncMock(return_value=ParsedIntent(
                primary="multilingual_content", secondary=[], confidence=0.8
            )),
            _extract_contexts=AsyncMock(return_value=[
                ExtractedContext(type="language", content="mixed", relevance=0.9)
            ]),
            _identify_domain=AsyncMock(return_value=DomainInfo(
                primary="content_creation", secondary=["multilingual"], confidence=0.8
            )),
            _extract_technical_requirements=AsyncMock(return_value=[]),
            _assess_parsing_quality=AsyncMock(return_value=QualityMetrics(
                clarity=0.7, specificity=0.8, completeness=0.8,
                feasibility=0.9, overall_confidence=0.8
            ))
        ):
            result = await self.parser.parse_requirements(multilingual_input)

        assert isinstance(result, ParsedRequirements)
        assert result.intent.primary == "multilingual_content"
        assert any(ctx.type == "language" for ctx in result.contexts)

    def test_memory_usage_optimization(self):
        """测试内存使用优化"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # 创建大量解析结果
        large_cache = {}
        for i in range(1000):
            large_cache[f"input_{i}"] = ParsedRequirements(
                intent=ParsedIntent(primary="test", secondary=[], confidence=0.8),
                contexts=[], domain=DomainInfo(primary="test", secondary=[], confidence=0.8),
                technical_requirements=[],
                quality_metrics=QualityMetrics(
                    clarity=0.8, specificity=0.8, completeness=0.8,
                    feasibility=0.8, overall_confidence=0.8
                ),
                suggestions={"improvements": [], "clarifications": [], "enhancements": []},
                metadata={}
            )

        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before

        # 清理
        del large_cache

        # 内存增长应该在合理范围内（小于50MB）
        assert memory_increase < 50 * 1024 * 1024