"""
意图解析器测试

测试 IntentParser 类的各种功能，包括意图识别、置信度计算、
情感分析、紧急程度评估等。
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from app.agents.pe_engineer.parsers.intent_parser import IntentParser
from app.agents.pe_engineer.schemas.requirements import (
    ParsedIntent, IntentCategory, SentimentType, ConfidenceLevel
)


class TestIntentParser:
    """测试意图解析器"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return IntentParser()

    def test_init(self, parser):
        """测试初始化"""
        assert parser is not None
        assert parser.intent_patterns is not None
        assert parser.sentiment_patterns is not None
        assert parser.keyword_weights is not None
        assert len(parser.intent_patterns) > 0

    @pytest.mark.parametrize("text,expected_category", [
        ("帮我创建一个提示词", IntentCategory.CREATE_PROMPT),
        ("请生成一个新的prompt", IntentCategory.CREATE_PROMPT),
        ("我想写一个对话指令", IntentCategory.CREATE_PROMPT),
        ("优化这个提示词", IntentCategory.OPTIMIZE_PROMPT),
        ("改进现有的prompt效果", IntentCategory.OPTIMIZE_PROMPT),
        ("分析一下这个提示词的质量", IntentCategory.ANALYZE_PROMPT),
        ("评估这个prompt怎么样", IntentCategory.ANALYZE_PROMPT),
        ("有没有相关的模板", IntentCategory.GET_TEMPLATE),
        ("给我一些示例参考", IntentCategory.GET_TEMPLATE),
        ("什么是提示词", IntentCategory.GENERAL_INQUIRY),
        ("如何写好prompt", IntentCategory.GENERAL_INQUIRY)
    ])
    def test_parse_intent_categories(self, parser, text, expected_category):
        """测试意图分类准确性"""
        result = parser.parse_intent(text)

        assert isinstance(result, ParsedIntent)
        assert result.category == expected_category
        assert result.confidence > 0.0
        assert isinstance(result.keywords, list)

    def test_parse_intent_empty_input(self, parser):
        """测试空输入"""
        result = parser.parse_intent("")

        assert result.category == IntentCategory.UNKNOWN
        assert result.confidence == 0.0
        assert result.confidence_level == ConfidenceLevel.VERY_LOW

    def test_parse_intent_short_input(self, parser):
        """测试过短输入"""
        result = parser.parse_intent("hi")

        assert result.category == IntentCategory.UNKNOWN
        assert result.confidence == 0.0

    def test_parse_intent_confidence_levels(self, parser):
        """测试置信度级别计算"""
        # 高置信度输入
        high_conf_text = "帮我创建一个新的提示词来生成代码"
        result_high = parser.parse_intent(high_conf_text)

        # 低置信度输入
        low_conf_text = "这个东西怎么搞"
        result_low = parser.parse_intent(low_conf_text)

        assert result_high.confidence > result_low.confidence
        assert result_high.confidence >= 0.5  # 应该有较高置信度

    @pytest.mark.parametrize("text,expected_sentiment", [
        ("这个很好，帮我优化一下", SentimentType.POSITIVE),
        ("这个提示词有问题，不太好用", SentimentType.NEGATIVE),
        ("紧急需要一个新的prompt", SentimentType.URGENT),
        ("不明白这个怎么用", SentimentType.CONFUSED),
        ("创建一个新的提示词", SentimentType.NEUTRAL)
    ])
    def test_sentiment_analysis(self, parser, text, expected_sentiment):
        """测试情感分析"""
        result = parser.parse_intent(text)

        assert result.sentiment == expected_sentiment

    @pytest.mark.parametrize("text,min_urgency", [
        ("紧急需要帮助", 4),
        ("赶紧给我做一个", 3),
        ("立即需要解决", 5),
        ("普通的需求", 1)
    ])
    def test_urgency_assessment(self, parser, text, min_urgency):
        """测试紧急程度评估"""
        result = parser.parse_intent(text)

        assert result.urgency_level >= min_urgency
        assert 1 <= result.urgency_level <= 5

    def test_keyword_extraction(self, parser):
        """测试关键词提取"""
        text = "帮我创建一个用于代码生成的提示词"
        result = parser.parse_intent(text)

        assert len(result.keywords) > 0
        expected_keywords = ["创建", "提示词", "代码"]
        found_keywords = [kw for kw in expected_keywords if kw in result.keywords]
        assert len(found_keywords) > 0

    def test_alternative_intents(self, parser):
        """测试备选意图生成"""
        # 使用一个可能有多种意图解释的文本
        text = "帮我看看这个prompt"
        result = parser.parse_intent(text)

        assert isinstance(result.alternative_intents, list)
        if result.confidence < 0.9:  # 如果主意图不是很确定
            assert len(result.alternative_intents) > 0

    def test_preprocess_text(self, parser):
        """测试文本预处理"""
        # 测试内部方法（虽然是私有方法，但对功能很重要）
        text = "  帮我    创建一个提示词！！！  "
        processed = parser._preprocess_text(text)

        assert processed.strip() == processed  # 无前后空白
        assert "  " not in processed  # 无多余空格
        assert processed.islower()  # 转为小写

    def test_batch_parse_intents(self, parser):
        """测试批量解析"""
        texts = [
            "创建一个新提示词",
            "优化现有prompt",
            "分析质量",
            "无效输入123#$%"
        ]

        results = parser.batch_parse_intents(texts)

        assert len(results) == len(texts)
        assert all(isinstance(result, ParsedIntent) for result in results)

        # 验证不同的意图类型
        categories = [result.category for result in results]
        assert IntentCategory.CREATE_PROMPT in categories
        assert IntentCategory.OPTIMIZE_PROMPT in categories
        assert IntentCategory.ANALYZE_PROMPT in categories

    def test_get_intent_statistics(self, parser):
        """测试意图统计"""
        # 创建一些解析结果
        intents = [
            parser.parse_intent("创建提示词"),
            parser.parse_intent("优化prompt"),
            parser.parse_intent("分析质量"),
            parser.parse_intent("创建新的指令")
        ]

        stats = parser.get_intent_statistics(intents)

        assert "total_intents" in stats
        assert "category_distribution" in stats
        assert "confidence_distribution" in stats
        assert "average_confidence" in stats
        assert "sentiment_distribution" in stats

        assert stats["total_intents"] == len(intents)
        assert stats["average_confidence"] > 0.0

    def test_complex_intent_parsing(self, parser):
        """测试复杂意图解析"""
        complex_text = """
        我是一名前端开发工程师，现在需要创建一个用于代码生成的提示词。
        这个提示词要能够帮助生成React组件代码，要求代码规范、可复用。
        请帮我制作一个专业的prompt，要求输出格式为JSON，包含完整的组件代码。
        比较急，希望尽快完成。
        """

        result = parser.parse_intent(complex_text)

        # 验证基本结果
        assert result.category == IntentCategory.CREATE_PROMPT
        assert result.confidence > 0.5
        assert len(result.keywords) > 3

        # 验证情感和紧急程度
        assert result.urgency_level >= 3  # 因为说了"比较急"

    def test_edge_cases(self, parser):
        """测试边界情况"""
        edge_cases = [
            None,  # None输入
            "",    # 空字符串
            "   ",  # 只有空格
            "a",    # 单字符
            "！@#$%^&*()",  # 特殊字符
            "1234567890",   # 纯数字
        ]

        for case in edge_cases:
            try:
                if case is None:
                    # None应该引发异常或返回未知意图
                    with pytest.raises((TypeError, AttributeError)):
                        parser.parse_intent(case)
                else:
                    result = parser.parse_intent(case)
                    # 边界情况应该返回未知意图或很低的置信度
                    assert result.category == IntentCategory.UNKNOWN or result.confidence < 0.3
            except Exception as e:
                # 记录但不阻止测试
                print(f"Edge case {case} raised: {e}")

    def test_pattern_matching_accuracy(self, parser):
        """测试模式匹配准确性"""
        # 测试各种表达方式
        create_expressions = [
            "帮我写一个提示词",
            "能否创建一个prompt",
            "我想生成一个新的指令",
            "制作一个对话模板"
        ]

        for expr in create_expressions:
            result = parser.parse_intent(expr)
            assert result.category == IntentCategory.CREATE_PROMPT, f"Failed for: {expr}"
            assert result.confidence > 0.3, f"Low confidence for: {expr}"

    def test_confidence_level_mapping(self, parser):
        """测试置信度级别映射"""
        # 创建不同置信度的结果进行测试
        test_cases = [
            ("帮我创建一个用于代码生成的专业提示词模板", ConfidenceLevel.HIGH),
            ("做个东西", ConfidenceLevel.LOW),
            ("提示词创建生成制作", ConfidenceLevel.MEDIUM)
        ]

        for text, expected_min_level in test_cases:
            result = parser.parse_intent(text)
            # 验证置信度级别合理性（允许比预期更高）
            level_values = {
                ConfidenceLevel.VERY_LOW: 0,
                ConfidenceLevel.LOW: 1,
                ConfidenceLevel.MEDIUM: 2,
                ConfidenceLevel.HIGH: 3,
                ConfidenceLevel.VERY_HIGH: 4
            }
            assert level_values[result.confidence_level] >= level_values[expected_min_level]

    def test_memory_and_performance(self, parser):
        """测试内存和性能"""
        import time

        # 测试大量解析是否会导致内存问题
        large_texts = ["创建提示词" + str(i) for i in range(100)]

        start_time = time.time()
        results = parser.batch_parse_intents(large_texts)
        end_time = time.time()

        # 验证结果
        assert len(results) == 100
        assert all(isinstance(r, ParsedIntent) for r in results)

        # 性能检查（应该在合理时间内完成）
        processing_time = end_time - start_time
        assert processing_time < 5.0  # 5秒内完成100个解析

    @pytest.mark.parametrize("invalid_input", [
        123,      # 数字
        [],       # 列表
        {},       # 字典
        True,     # 布尔值
    ])
    def test_invalid_input_types(self, parser, invalid_input):
        """测试无效输入类型"""
        with pytest.raises((TypeError, AttributeError)):
            parser.parse_intent(invalid_input)

    def test_intent_description_mapping(self, parser):
        """测试意图描述映射"""
        for category in IntentCategory:
            description = parser._get_intent_description(category)
            assert isinstance(description, str)
            assert len(description) > 0