"""
需求解析 Schema 测试

测试需求解析相关的数据模式定义，包括数据验证、序列化等功能。
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from typing import Dict, Any

from app.agents.pe_engineer.schemas.requirements import (
    ParsedIntent, ExtractedContext, DomainInfo, TechnicalRequirement,
    ParsedRequirements, QualityMetric, RequirementsParsingConfig,
    IntentCategory, ContextType, SentimentType, ConfidenceLevel,
    RequirementsValidationError
)


class TestParsedIntent:
    """测试解析意图数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        intent = ParsedIntent(
            category=IntentCategory.CREATE_PROMPT,
            confidence=0.85,
            keywords=["创建", "提示词"],
            sentiment=SentimentType.POSITIVE
        )

        assert intent.category == IntentCategory.CREATE_PROMPT
        assert intent.confidence == 0.85
        assert intent.confidence_level == ConfidenceLevel.HIGH
        assert intent.keywords == ["创建", "提示词"]
        assert intent.sentiment == SentimentType.POSITIVE
        assert intent.urgency_level == 3  # 默认值

    def test_confidence_level_auto_calculation(self):
        """测试置信度级别自动计算"""
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.80, ConfidenceLevel.HIGH),
            (0.60, ConfidenceLevel.MEDIUM),
            (0.35, ConfidenceLevel.LOW),
            (0.15, ConfidenceLevel.VERY_LOW)
        ]

        for confidence, expected_level in test_cases:
            intent = ParsedIntent(
                category=IntentCategory.CREATE_PROMPT,
                confidence=confidence
            )
            assert intent.confidence_level == expected_level

    def test_invalid_confidence(self):
        """测试无效置信度值"""
        with pytest.raises(ValidationError):
            ParsedIntent(
                category=IntentCategory.CREATE_PROMPT,
                confidence=1.5  # 超出范围
            )

        with pytest.raises(ValidationError):
            ParsedIntent(
                category=IntentCategory.CREATE_PROMPT,
                confidence=-0.1  # 小于0
            )

    def test_invalid_urgency_level(self):
        """测试无效紧急程度"""
        with pytest.raises(ValidationError):
            ParsedIntent(
                category=IntentCategory.CREATE_PROMPT,
                confidence=0.8,
                urgency_level=6  # 超出范围
            )

    def test_default_values(self):
        """测试默认值"""
        intent = ParsedIntent(
            category=IntentCategory.CREATE_PROMPT,
            confidence=0.8
        )

        assert intent.keywords == []
        assert intent.sentiment == SentimentType.NEUTRAL
        assert intent.urgency_level == 3
        assert intent.alternative_intents == []


class TestExtractedContext:
    """测试提取的上下文数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        context = ExtractedContext(
            context_type=ContextType.TECHNICAL,
            content="使用Python开发",
            importance=0.8,
            source_position=10,
            related_keywords=["Python", "开发"]
        )

        assert context.context_type == ContextType.TECHNICAL
        assert context.content == "使用Python开发"
        assert context.importance == 0.8
        assert context.source_position == 10
        assert context.related_keywords == ["Python", "开发"]

    def test_default_values(self):
        """测试默认值"""
        context = ExtractedContext(
            context_type=ContextType.DOMAIN,
            content="软件开发",
            source_position=0
        )

        assert context.importance == 0.5
        assert context.related_keywords == []

    def test_invalid_importance(self):
        """测试无效重要性值"""
        with pytest.raises(ValidationError):
            ExtractedContext(
                context_type=ContextType.TECHNICAL,
                content="测试",
                importance=1.5,  # 超出范围
                source_position=0
            )


class TestDomainInfo:
    """测试领域信息数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        domain = DomainInfo(
            name="软件开发",
            confidence=0.9,
            keywords=["Python", "React", "API"],
            subcategory="前端开发"
        )

        assert domain.name == "软件开发"
        assert domain.confidence == 0.9
        assert domain.keywords == ["Python", "React", "API"]
        assert domain.subcategory == "前端开发"

    def test_default_values(self):
        """测试默认值"""
        domain = DomainInfo(
            name="数据分析",
            confidence=0.7
        )

        assert domain.keywords == []
        assert domain.subcategory is None


class TestTechnicalRequirement:
    """测试技术需求数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        req = TechnicalRequirement(
            requirement_type="framework",
            description="使用React框架",
            priority=4,
            examples=["React 18", "TypeScript"]
        )

        assert req.requirement_type == "framework"
        assert req.description == "使用React框架"
        assert req.priority == 4
        assert req.examples == ["React 18", "TypeScript"]

    def test_default_values(self):
        """测试默认值"""
        req = TechnicalRequirement(
            requirement_type="performance",
            description="高性能要求"
        )

        assert req.priority == 3
        assert req.examples == []

    def test_invalid_priority(self):
        """测试无效优先级"""
        with pytest.raises(ValidationError):
            TechnicalRequirement(
                requirement_type="test",
                description="测试",
                priority=6  # 超出范围
            )


class TestQualityMetric:
    """测试质量指标数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        metric = QualityMetric(
            metric_name="accuracy",
            score=0.85,
            description="解析准确性"
        )

        assert metric.metric_name == "accuracy"
        assert metric.score == 0.85
        assert metric.description == "解析准确性"

    def test_invalid_score(self):
        """测试无效评分"""
        with pytest.raises(ValidationError):
            QualityMetric(
                metric_name="test",
                score=1.5  # 超出范围
            )


class TestParsedRequirements:
    """测试完整解析结果数据结构"""

    @pytest.fixture
    def sample_intent(self):
        """示例意图"""
        return ParsedIntent(
            category=IntentCategory.CREATE_PROMPT,
            confidence=0.8
        )

    def test_valid_creation(self, sample_intent):
        """测试有效创建"""
        requirements = ParsedRequirements(
            original_input="创建一个提示词",
            intent=sample_intent,
            main_objective="创建新的提示词"
        )

        assert requirements.original_input == "创建一个提示词"
        assert requirements.intent == sample_intent
        assert requirements.main_objective == "创建新的提示词"
        assert isinstance(requirements.parsed_at, datetime)
        assert requirements.request_id.startswith("req_")

    def test_default_values(self, sample_intent):
        """测试默认值"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试目标"
        )

        assert requirements.extracted_contexts == []
        assert requirements.key_requirements == []
        assert requirements.constraints == []
        assert requirements.suggestions == []
        assert requirements.warnings == []
        assert requirements.missing_info == []
        assert requirements.parsing_quality == []
        assert requirements.overall_confidence == 0.0
        assert requirements.processing_time_ms == 0
        assert isinstance(requirements.metadata, dict)

    def test_add_context_method(self, sample_intent):
        """测试添加上下文方法"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试"
        )

        requirements.add_context(
            ContextType.TECHNICAL,
            "使用Python",
            importance=0.8,
            source_position=5
        )

        assert len(requirements.extracted_contexts) == 1
        context = requirements.extracted_contexts[0]
        assert context.context_type == ContextType.TECHNICAL
        assert context.content == "使用Python"
        assert context.importance == 0.8
        assert context.source_position == 5

    def test_get_context_by_type_method(self, sample_intent):
        """测试按类型获取上下文方法"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试"
        )

        # 添加不同类型的上下文
        requirements.add_context(ContextType.TECHNICAL, "技术内容")
        requirements.add_context(ContextType.BUSINESS, "业务内容")
        requirements.add_context(ContextType.TECHNICAL, "另一个技术内容")

        tech_contexts = requirements.get_context_by_type(ContextType.TECHNICAL)
        business_contexts = requirements.get_context_by_type(ContextType.BUSINESS)

        assert len(tech_contexts) == 2
        assert len(business_contexts) == 1
        assert all(ctx.context_type == ContextType.TECHNICAL for ctx in tech_contexts)

    def test_add_quality_metric_method(self, sample_intent):
        """测试添加质量指标方法"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试"
        )

        requirements.add_quality_metric("accuracy", 0.85, "准确性评估")

        assert len(requirements.parsing_quality) == 1
        metric = requirements.parsing_quality[0]
        assert metric.metric_name == "accuracy"
        assert metric.score == 0.85
        assert metric.description == "准确性评估"

    def test_get_quality_score_method(self, sample_intent):
        """测试获取质量评分方法"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试"
        )

        requirements.add_quality_metric("accuracy", 0.85)
        requirements.add_quality_metric("completeness", 0.75)

        assert requirements.get_quality_score("accuracy") == 0.85
        assert requirements.get_quality_score("completeness") == 0.75
        assert requirements.get_quality_score("non_existent") is None

    def test_is_high_confidence_method(self, sample_intent):
        """测试高置信度判断方法"""
        requirements = ParsedRequirements(
            original_input="测试",
            intent=sample_intent,
            main_objective="测试"
        )

        # 低置信度
        requirements.overall_confidence = 0.6
        assert not requirements.is_high_confidence()

        # 高置信度
        requirements.overall_confidence = 0.8
        assert requirements.is_high_confidence()

        # 自定义阈值
        assert not requirements.is_high_confidence(threshold=0.9)

    def test_get_summary_method(self, sample_intent):
        """测试获取摘要方法"""
        requirements = ParsedRequirements(
            original_input="测试输入",
            intent=sample_intent,
            main_objective="创建提示词"
        )

        requirements.key_requirements = ["需求1", "需求2", "需求3"]
        requirements.add_context(ContextType.TECHNICAL, "技术内容")
        requirements.add_quality_metric("accuracy", 0.8)
        requirements.overall_confidence = 0.85

        summary = requirements.get_summary()

        expected_keys = [
            "request_id", "intent", "confidence", "prompt_type",
            "complexity", "main_objective", "key_requirements_count",
            "has_domain", "context_count", "quality_score"
        ]

        for key in expected_keys:
            assert key in summary

        assert summary["key_requirements_count"] == 3
        assert summary["context_count"] == 1
        assert summary["has_domain"] is False  # 没有设置domain_info
        assert summary["quality_score"] == 0.8


class TestRequirementsParsingConfig:
    """测试需求解析配置数据结构"""

    def test_valid_creation(self):
        """测试有效创建"""
        config = RequirementsParsingConfig(
            min_input_length=20,
            max_input_length=2000,
            intent_confidence_threshold=0.6,
            context_importance_threshold=0.4,
            min_quality_score=0.7
        )

        assert config.min_input_length == 20
        assert config.max_input_length == 2000
        assert config.intent_confidence_threshold == 0.6
        assert config.context_importance_threshold == 0.4
        assert config.min_quality_score == 0.7

    def test_default_values(self):
        """测试默认值"""
        config = RequirementsParsingConfig()

        assert config.min_input_length == 10
        assert config.max_input_length == 5000
        assert config.intent_confidence_threshold == 0.5
        assert config.enable_sentiment_analysis is True
        assert config.enable_caching is True

    def test_threshold_validation(self):
        """测试阈值验证"""
        # 有效阈值
        config = RequirementsParsingConfig(intent_confidence_threshold=0.5)
        assert config.intent_confidence_threshold == 0.5

        # 无效阈值
        with pytest.raises(ValidationError):
            RequirementsParsingConfig(intent_confidence_threshold=1.5)

        with pytest.raises(ValidationError):
            RequirementsParsingConfig(context_importance_threshold=-0.1)

        with pytest.raises(ValidationError):
            RequirementsParsingConfig(min_quality_score=1.2)


class TestRequirementsValidationError:
    """测试需求验证错误"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = RequirementsValidationError("测试错误")

        assert str(error) == "测试错误"
        assert error.message == "测试错误"
        assert error.field is None
        assert error.validation_errors == []

    def test_full_creation(self):
        """测试完整创建"""
        error = RequirementsValidationError(
            message="验证失败",
            field="intent",
            validation_errors=["错误1", "错误2"]
        )

        assert error.message == "验证失败"
        assert error.field == "intent"
        assert error.validation_errors == ["错误1", "错误2"]


class TestSchemaIntegration:
    """测试数据结构集成"""

    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 创建意图
        intent = ParsedIntent(
            category=IntentCategory.CREATE_PROMPT,
            confidence=0.85,
            keywords=["创建", "代码", "提示词"]
        )

        # 创建上下文
        context = ExtractedContext(
            context_type=ContextType.TECHNICAL,
            content="使用Python和Django开发",
            importance=0.9,
            source_position=15,
            related_keywords=["Python", "Django"]
        )

        # 创建领域信息
        domain = DomainInfo(
            name="软件开发",
            confidence=0.9,
            keywords=["Python", "Django", "API"],
            subcategory="后端开发"
        )

        # 创建技术需求
        tech_req = TechnicalRequirement(
            requirement_type="framework",
            description="使用Django框架开发RESTful API",
            priority=4,
            examples=["Django REST Framework"]
        )

        # 创建完整需求
        requirements = ParsedRequirements(
            original_input="创建一个用于Python Django API开发的代码生成提示词",
            intent=intent,
            main_objective="生成高质量的Django API代码",
            extracted_contexts=[context],
            domain_info=domain,
            technical_requirements=[tech_req],
            key_requirements=["符合PEP8规范", "包含错误处理", "支持JWT认证"],
            overall_confidence=0.85
        )

        # 验证完整结构
        assert isinstance(requirements, ParsedRequirements)
        assert requirements.intent.category == IntentCategory.CREATE_PROMPT
        assert len(requirements.extracted_contexts) == 1
        assert requirements.domain_info.name == "软件开发"
        assert len(requirements.technical_requirements) == 1
        assert len(requirements.key_requirements) == 3

        # 测试方法调用
        tech_contexts = requirements.get_context_by_type(ContextType.TECHNICAL)
        assert len(tech_contexts) == 1

        summary = requirements.get_summary()
        assert summary["intent"] == IntentCategory.CREATE_PROMPT.value
        assert summary["has_domain"] is True

    def test_serialization(self):
        """测试序列化功能"""
        intent = ParsedIntent(
            category=IntentCategory.CREATE_PROMPT,
            confidence=0.8
        )

        requirements = ParsedRequirements(
            original_input="测试序列化",
            intent=intent,
            main_objective="测试目标"
        )

        # 测试转换为字典
        data = requirements.model_dump()
        assert isinstance(data, dict)
        assert "original_input" in data
        assert "intent" in data
        assert "main_objective" in data

        # 测试从字典创建
        new_requirements = ParsedRequirements.model_validate(data)
        assert new_requirements.original_input == requirements.original_input
        assert new_requirements.intent.category == requirements.intent.category
        assert new_requirements.main_objective == requirements.main_objective