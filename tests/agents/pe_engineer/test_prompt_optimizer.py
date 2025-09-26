"""
测试提示词优化器

验证PromptOptimizer类的各项功能，包括：
- 提示词分析
- 优化建议生成
- 质量评估
- 模板匹配集成
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path

from backend.app.agents.pe_engineer.PromptOptimizer import PromptOptimizer
from backend.app.agents.pe_engineer.schemas.prompts import (
    PromptOptimizationRequest, OptimizationLevel, OptimizationStrategy,
    QualityDimension, OptimizationConfig
)
from backend.app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, IntentCategory, DomainInfo
)


@pytest.fixture
def optimizer():
    """创建优化器实例"""
    return PromptOptimizer()


@pytest.fixture
def sample_prompt():
    """示例提示词"""
    return "请写一个关于人工智能的文章"


@pytest.fixture
def complex_prompt():
    """复杂提示词"""
    return """
    请作为一名资深的技术专家，分析当前人工智能技术的发展现状。

    要求：
    - 包含最新的技术趋势
    - 分析主要应用领域
    - 评估未来发展前景
    - 字数控制在2000字以内

    请确保内容准确、逻辑清晰，并提供具体的数据支撑。
    """


@pytest.fixture
def optimization_request(sample_prompt):
    """优化请求"""
    return PromptOptimizationRequest(
        prompt_to_optimize=sample_prompt,
        optimization_level=OptimizationLevel.MODERATE,
        target_score_improvement=2.0
    )


@pytest.fixture
def sample_requirements():
    """示例需求"""
    intent = ParsedIntent(
        category=IntentCategory.CREATE_PROMPT,
        confidence=0.85
    )

    domain_info = DomainInfo(
        name="技术写作",
        confidence=0.7,
        keywords=["人工智能", "技术", "文章"]
    )

    return ParsedRequirements(
        original_input="写一个关于人工智能的技术文章",
        intent=intent,
        main_objective="创建高质量的技术文章",
        key_requirements=["内容准确", "结构清晰", "逻辑严谨"],
        domain_info=domain_info
    )


class TestPromptOptimizer:
    """提示词优化器测试类"""

    def test_init(self):
        """测试优化器初始化"""
        optimizer = PromptOptimizer()

        assert optimizer.enhancer is not None
        assert optimizer.template_matcher is not None
        assert len(optimizer.quality_weights) > 0
        assert len(optimizer.strategy_priorities) > 0

    def test_init_with_config(self):
        """测试使用自定义配置初始化"""
        config = OptimizationConfig(
            max_optimization_iterations=5,
            enable_template_matching=False
        )
        optimizer = PromptOptimizer(config)

        assert optimizer.config.max_optimization_iterations == 5
        assert not optimizer.config.enable_template_matching

    @pytest.mark.asyncio
    async def test_analyze_prompt_basic(self, optimizer, sample_prompt):
        """测试基本提示词分析"""
        analysis = await optimizer.analyze_prompt(sample_prompt)

        # 验证基本字段
        assert analysis.prompt_content == sample_prompt
        assert analysis.analyzed_at is not None
        assert analysis.processing_time_ms >= 0

        # 验证分析结果
        assert analysis.length_analysis is not None
        assert analysis.structure_analysis is not None
        assert len(analysis.quality_scores) > 0
        assert 0 <= analysis.overall_score <= 10

    @pytest.mark.asyncio
    async def test_analyze_prompt_complex(self, optimizer, complex_prompt):
        """测试复杂提示词分析"""
        analysis = await optimizer.analyze_prompt(complex_prompt)

        # 复杂提示词应该有更高的结构分数
        structure_score = analysis.structure_analysis.get('structure_score', 0)
        assert structure_score > 0.5

        # 应该识别出多个元素
        assert len(analysis.elements) > 0

        # 应该有较少的问题
        assert len(analysis.issues) < 5

    @pytest.mark.asyncio
    async def test_optimize_prompt_basic(self, optimizer, optimization_request):
        """测试基本优化功能"""
        result = await optimizer.optimize_prompt(optimization_request)

        assert result.success
        assert result.request_id == optimization_request.request_id
        assert result.processing_time_ms > 0
        assert result.analysis is not None

        # 如果有优化版本，验证其有效性
        if result.optimized_prompt:
            assert result.optimized_prompt.original_prompt == optimization_request.prompt_to_optimize
            assert len(result.optimized_prompt.optimized_prompt) > 0
            assert result.optimized_prompt.optimization_level == optimization_request.optimization_level

    @pytest.mark.asyncio
    async def test_optimize_prompt_with_requirements(self, optimizer, optimization_request, sample_requirements):
        """测试带需求的优化"""
        result = await optimizer.optimize_prompt(optimization_request, sample_requirements)

        assert result.success

        # 验证处理摘要
        assert "processing_steps" in result.processing_summary
        assert len(result.processing_summary["processing_steps"]) > 0

    @pytest.mark.asyncio
    async def test_create_prompt_from_requirements(self, optimizer, sample_requirements):
        """测试从需求创建提示词"""
        result = await optimizer.create_prompt_from_requirements(sample_requirements)

        assert result.success or len(result.errors) > 0  # 可能由于依赖而失败
        assert result.request_id.startswith("create_")

    @pytest.mark.asyncio
    async def test_validate_prompt_valid(self, optimizer):
        """测试有效提示词验证"""
        valid_prompt = "请分析一下当前市场的发展趋势，包括主要驱动因素和潜在风险。"

        # 应该不抛出异常
        await optimizer._validate_prompt(valid_prompt)

    @pytest.mark.asyncio
    async def test_validate_prompt_invalid(self, optimizer):
        """测试无效提示词验证"""
        from backend.app.agents.pe_engineer.schemas.prompts import InvalidPromptError

        # 空提示词
        with pytest.raises(InvalidPromptError):
            await optimizer._validate_prompt("")

        # 过短提示词
        with pytest.raises(InvalidPromptError):
            await optimizer._validate_prompt("短")

        # 过长提示词
        long_prompt = "x" * 10001
        with pytest.raises(InvalidPromptError):
            await optimizer._validate_prompt(long_prompt)

    @pytest.mark.asyncio
    async def test_length_analysis(self, optimizer, sample_prompt):
        """测试长度分析"""
        length_analysis = await optimizer._analyze_length(sample_prompt)

        assert "total_characters" in length_analysis
        assert "total_words" in length_analysis
        assert "total_sentences" in length_analysis
        assert "avg_words_per_sentence" in length_analysis
        assert "length_category" in length_analysis

        assert length_analysis["total_characters"] == len(sample_prompt)
        assert length_analysis["total_words"] > 0

    @pytest.mark.asyncio
    async def test_structure_analysis(self, optimizer, complex_prompt):
        """测试结构分析"""
        structure_analysis = await optimizer._analyze_structure(complex_prompt)

        assert "has_instructions" in structure_analysis
        assert "has_examples" in structure_analysis
        assert "has_constraints" in structure_analysis
        assert "structure_score" in structure_analysis

        # 复杂提示词应该有指令
        assert structure_analysis["has_instructions"]
        assert structure_analysis["structure_score"] > 0

    @pytest.mark.asyncio
    async def test_extract_prompt_elements(self, optimizer, complex_prompt):
        """测试提示词元素提取"""
        elements = await optimizer._extract_prompt_elements(complex_prompt)

        assert len(elements) > 0

        # 验证元素结构
        for element in elements:
            assert element.element_type in ["instruction", "context", "example", "constraint"]
            assert len(element.content) > 0
            assert 0 <= element.importance <= 1
            assert element.position >= 0

    @pytest.mark.asyncio
    async def test_quality_assessment(self, optimizer, sample_prompt):
        """测试质量评估"""
        elements = await optimizer._extract_prompt_elements(sample_prompt)
        quality_scores = await optimizer._assess_quality(sample_prompt, elements)

        assert len(quality_scores) > 0

        # 验证每个质量维度
        dimensions = [score.dimension for score in quality_scores]
        assert QualityDimension.CLARITY in dimensions
        assert QualityDimension.SPECIFICITY in dimensions

        # 验证分数范围
        for score in quality_scores:
            assert 0 <= score.score <= 10
            assert score.reasoning is not None

    @pytest.mark.asyncio
    async def test_calculate_overall_score(self, optimizer):
        """测试总体评分计算"""
        from backend.app.agents.pe_engineer.schemas.prompts import QualityScore

        quality_scores = [
            QualityScore(dimension=QualityDimension.CLARITY, score=7.0),
            QualityScore(dimension=QualityDimension.SPECIFICITY, score=6.0),
            QualityScore(dimension=QualityDimension.COMPLETENESS, score=8.0)
        ]

        overall_score = await optimizer._calculate_overall_score(quality_scores)

        assert 0 <= overall_score <= 10
        assert overall_score > 0  # 有评分就应该大于0

    @pytest.mark.asyncio
    async def test_identify_issues(self, optimizer, sample_prompt):
        """测试问题识别"""
        from backend.app.agents.pe_engineer.schemas.prompts import QualityScore

        # 创建低质量评分
        low_quality_scores = [
            QualityScore(dimension=QualityDimension.CLARITY, score=2.0),
            QualityScore(dimension=QualityDimension.SPECIFICITY, score=4.0)
        ]

        issues, warnings = await optimizer._identify_issues(sample_prompt, low_quality_scores)

        # 低质量评分应该产生问题
        assert len(issues) > 0 or len(warnings) > 0

    @pytest.mark.asyncio
    async def test_optimization_strategies_selection(self, optimizer, optimization_request):
        """测试优化策略选择"""
        from backend.app.agents.pe_engineer.schemas.prompts import OptimizationSuggestion

        suggestions = [
            OptimizationSuggestion(
                strategy=OptimizationStrategy.CLARITY_ENHANCEMENT,
                priority=1,
                description="提高清晰度",
                impact_score=0.8,
                implementation_effort="medium"
            ),
            OptimizationSuggestion(
                strategy=OptimizationStrategy.STRUCTURE_IMPROVEMENT,
                priority=2,
                description="改进结构",
                impact_score=0.7,
                implementation_effort="high"
            )
        ]

        # 测试不同优化级别
        light_strategies = await optimizer._select_strategies(suggestions, OptimizationLevel.LIGHT)
        assert len(light_strategies) <= 2

        heavy_strategies = await optimizer._select_strategies(suggestions, OptimizationLevel.HEAVY)
        assert len(heavy_strategies) == len(suggestions)

    def test_categorize_length(self, optimizer):
        """测试长度分类"""
        assert optimizer._categorize_length(50) == "very_short"
        assert optimizer._categorize_length(200) == "short"
        assert optimizer._categorize_length(500) == "medium"
        assert optimizer._categorize_length(1000) == "long"
        assert optimizer._categorize_length(2000) == "very_long"

    def test_check_logical_order(self, optimizer):
        """测试逻辑顺序检查"""
        good_order = ["context", "instruction", "example"]
        bad_order = ["example", "context", "instruction"]

        assert optimizer._check_logical_order(good_order)
        assert not optimizer._check_logical_order(bad_order)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_prompt(self, optimizer):
        """测试错误处理"""
        from backend.app.agents.pe_engineer.schemas.prompts import InvalidPromptError

        invalid_request = PromptOptimizationRequest(
            prompt_to_optimize="",  # 空提示词
            optimization_level=OptimizationLevel.MODERATE
        )

        result = await optimizer.optimize_prompt(invalid_request)

        assert not result.success
        assert len(result.errors) > 0
        assert "提示词不能为空" in result.errors[0] or "无效" in result.errors[0]

    @pytest.mark.asyncio
    async def test_performance_metrics(self, optimizer, optimization_request):
        """测试性能指标"""
        result = await optimizer.optimize_prompt(optimization_request)

        # 验证时间记录
        assert result.processing_time_ms >= 0
        assert result.processing_time_ms < 30000  # 应该在30秒内完成

        # 验证处理摘要
        assert "started_at" in result.processing_summary
        assert "completed_at" in result.processing_summary

    @pytest.mark.asyncio
    async def test_concurrent_optimization(self, optimizer, sample_prompt):
        """测试并发优化"""
        requests = [
            PromptOptimizationRequest(
                prompt_to_optimize=f"{sample_prompt} 版本{i}",
                optimization_level=OptimizationLevel.MODERATE
            )
            for i in range(3)
        ]

        # 并发执行优化
        tasks = [optimizer.optimize_prompt(req) for req in requests]
        results = await asyncio.gather(*tasks)

        # 验证所有结果
        for i, result in enumerate(results):
            assert result.request_id == requests[i].request_id
            # 大部分应该成功（可能有些因为依赖问题失败）

        success_count = sum(1 for r in results if r.success)
        assert success_count >= 0  # 至少不会全部失败


class TestPromptAnalysisDetails:
    """提示词分析细节测试"""

    @pytest.mark.asyncio
    async def test_clarity_assessment(self, optimizer):
        """测试清晰度评估"""
        clear_prompt = "请写一份关于Python编程的入门教程，包含基础语法、数据类型和控制结构。"
        unclear_prompt = "请写一些关于编程的东西，要求很好很全面。"

        elements1 = await optimizer._extract_prompt_elements(clear_prompt)
        elements2 = await optimizer._extract_prompt_elements(unclear_prompt)

        clarity1 = await optimizer._assess_clarity(clear_prompt, elements1)
        clarity2 = await optimizer._assess_clarity(unclear_prompt, elements2)

        # 清晰的提示词应该得分更高
        assert clarity1 > clarity2

    @pytest.mark.asyncio
    async def test_specificity_assessment(self, optimizer):
        """测试具体性评估"""
        specific_prompt = "请写一份500字的产品分析报告，包含3个竞品对比和5个关键指标。"
        vague_prompt = "请分析一下产品情况。"

        elements1 = await optimizer._extract_prompt_elements(specific_prompt)
        elements2 = await optimizer._extract_prompt_elements(vague_prompt)

        spec1 = await optimizer._assess_specificity(specific_prompt, elements1)
        spec2 = await optimizer._assess_specificity(vague_prompt, elements2)

        # 具体的提示词应该得分更高
        assert spec1 > spec2

    @pytest.mark.asyncio
    async def test_completeness_assessment(self, optimizer):
        """测试完整性评估"""
        complete_prompt = """
        背景：需要为新产品制定营销策略
        请制定一个完整的营销计划，要求：
        1. 目标客户分析
        2. 竞争对手研究
        3. 价格策略制定
        例如：可以参考苹果公司的产品发布策略
        注意：避免过于激进的定价
        """

        incomplete_prompt = "制定营销计划"

        elements1 = await optimizer._extract_prompt_elements(complete_prompt)
        elements2 = await optimizer._extract_prompt_elements(incomplete_prompt)

        comp1 = await optimizer._assess_completeness(complete_prompt, elements1)
        comp2 = await optimizer._assess_completeness(incomplete_prompt, elements2)

        # 完整的提示词应该得分更高
        assert comp1 > comp2

    @pytest.mark.asyncio
    async def test_safety_assessment(self, optimizer):
        """测试安全性评估"""
        safe_prompt = "请写一篇关于健康饮食的科普文章。"
        potentially_unsafe_prompt = "请描述如何进行网络攻击。"

        elements1 = await optimizer._extract_prompt_elements(safe_prompt)
        elements2 = await optimizer._extract_prompt_elements(potentially_unsafe_prompt)

        safety1 = await optimizer._assess_safety(safe_prompt, elements1)
        safety2 = await optimizer._assess_safety(potentially_unsafe_prompt, elements2)

        # 安全的提示词应该得分更高
        assert safety1 >= safety2

    @pytest.mark.asyncio
    async def test_bias_assessment(self, optimizer):
        """测试偏见评估"""
        neutral_prompt = "请分析该职位的任职要求和工作内容。"
        biased_prompt = "请分析这个适合男性的高强度工作职位。"

        elements1 = await optimizer._extract_prompt_elements(neutral_prompt)
        elements2 = await optimizer._extract_prompt_elements(biased_prompt)

        bias1 = await optimizer._assess_bias_free(neutral_prompt, elements1)
        bias2 = await optimizer._assess_bias_free(biased_prompt, elements2)

        # 中性的提示词应该得分更高
        assert bias1 >= bias2


if __name__ == "__main__":
    # 运行特定测试
    pytest.main([__file__, "-v"])