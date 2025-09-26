"""
集成测试

测试各个组件之间的集成工作，验证完整的工作流程。
"""

import pytest
import tempfile
import json
import os
from pathlib import Path

from backend.app.agents.pe_engineer.PromptOptimizer import PromptOptimizer
from backend.app.agents.pe_engineer.optimizers.prompt_enhancer import PromptEnhancer
from backend.app.agents.pe_engineer.optimizers.template_matcher import TemplateMatcher
from backend.app.agents.pe_engineer.schemas.prompts import (
    PromptOptimizationRequest, OptimizationLevel, OptimizationConfig
)
from backend.app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, IntentCategory, DomainInfo
)


@pytest.fixture
def sample_template_data():
    """示例模板数据"""
    return {
        "templates": [
            {
                "template_id": "integration_001",
                "name": "集成测试模板",
                "category": "general_purpose",
                "description": "用于集成测试的通用模板",
                "template_content": "请{action}关于{topic}的{output_type}。要求：{requirements}",
                "variables": ["action", "topic", "output_type", "requirements"],
                "example_values": {
                    "action": "分析",
                    "topic": "人工智能",
                    "output_type": "报告",
                    "requirements": "详细准确"
                },
                "use_cases": ["分析任务", "报告写作"],
                "tags": ["通用", "分析"],
                "complexity": "intermediate",
                "prompt_type": "analytical",
                "success_rate": 0.85,
                "usage_count": 50,
                "rating": 4.2,
                "is_active": True
            }
        ]
    }


@pytest.fixture
def temp_template_file(sample_template_data):
    """创建临时模板文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_template_data, f, ensure_ascii=False)
        temp_path = f.name

    yield temp_path

    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def optimizer_with_templates(temp_template_file):
    """带模板的优化器"""
    config = OptimizationConfig(enable_template_matching=True)
    optimizer = PromptOptimizer(config)

    # 替换模板匹配器为使用测试模板文件的实例
    optimizer.template_matcher = TemplateMatcher(temp_template_file)

    return optimizer


@pytest.fixture
def sample_requirements():
    """示例需求"""
    intent = ParsedIntent(
        category=IntentCategory.CREATE_PROMPT,
        confidence=0.9
    )

    domain_info = DomainInfo(
        name="技术分析",
        confidence=0.8,
        keywords=["技术", "分析", "人工智能"]
    )

    return ParsedRequirements(
        original_input="分析人工智能技术的发展趋势",
        intent=intent,
        main_objective="分析AI技术发展",
        key_requirements=["技术准确", "趋势分析", "前景预测"],
        domain_info=domain_info
    )


class TestOptimizationWorkflow:
    """优化工作流程测试"""

    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self, optimizer_with_templates, sample_requirements):
        """测试完整的优化工作流程"""
        # 1. 创建优化请求
        request = PromptOptimizationRequest(
            prompt_to_optimize="分析AI发展",
            optimization_level=OptimizationLevel.MODERATE,
            target_score_improvement=2.0,
            use_templates=True
        )

        # 2. 执行优化
        result = await optimizer_with_templates.optimize_prompt(request, sample_requirements)

        # 3. 验证结果
        assert result.success or len(result.errors) > 0
        assert result.request_id == request.request_id
        assert result.processing_time_ms > 0

        # 如果成功，验证优化结果
        if result.success:
            assert result.analysis is not None
            assert result.processing_summary is not None
            assert "processing_steps" in result.processing_summary

    @pytest.mark.asyncio
    async def test_prompt_creation_from_requirements(self, optimizer_with_templates, sample_requirements):
        """测试从需求创建提示词"""
        result = await optimizer_with_templates.create_prompt_from_requirements(sample_requirements)

        assert result is not None
        assert result.request_id.startswith("create_")

        # 验证处理结果
        if result.success:
            assert result.optimized_prompt is not None
        else:
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_analysis_and_optimization_integration(self, optimizer_with_templates):
        """测试分析和优化的集成"""
        prompt = "请写一个关于机器学习的简单介绍"

        # 1. 先分析提示词
        analysis = await optimizer_with_templates.analyze_prompt(prompt)

        assert analysis is not None
        assert analysis.prompt_content == prompt
        assert len(analysis.quality_scores) > 0
        assert analysis.overall_score >= 0

        # 2. 基于分析结果进行优化
        request = PromptOptimizationRequest(
            prompt_to_optimize=prompt,
            optimization_level=OptimizationLevel.MODERATE
        )

        result = await optimizer_with_templates.optimize_prompt(request)

        # 验证分析被包含在结果中
        if result.success and result.analysis:
            assert result.analysis.prompt_content == prompt

    @pytest.mark.asyncio
    async def test_template_matching_integration(self, optimizer_with_templates):
        """测试模板匹配集成"""
        prompt = "请分析人工智能的技术发展情况"

        # 直接测试模板匹配
        matches = await optimizer_with_templates.template_matcher.find_matching_templates(prompt)

        assert isinstance(matches, list)
        # 可能没有匹配结果，但不应该出错

        # 测试集成在优化流程中
        request = PromptOptimizationRequest(
            prompt_to_optimize=prompt,
            optimization_level=OptimizationLevel.MODERATE,
            use_templates=True
        )

        result = await optimizer_with_templates.optimize_prompt(request)

        if result.success:
            # 如果有模板匹配，应该包含在结果中
            assert isinstance(result.template_matches, list)


class TestComponentIntegration:
    """组件集成测试"""

    @pytest.mark.asyncio
    async def test_enhancer_template_integration(self, temp_template_file):
        """测试增强器和模板的集成"""
        enhancer = PromptEnhancer()
        template_matcher = TemplateMatcher(temp_template_file)

        # 确保模板已加载
        await template_matcher._load_templates()

        prompt = "分析AI技术"

        # 1. 找到匹配的模板
        matches = await template_matcher.find_matching_templates(prompt)

        # 2. 使用增强器优化（模拟优化建议）
        from backend.app.agents.pe_engineer.schemas.prompts import OptimizationSuggestion, OptimizationStrategy

        suggestions = [
            OptimizationSuggestion(
                strategy=OptimizationStrategy.CONTEXT_ENRICHMENT,
                priority=1,
                description="丰富上下文",
                impact_score=0.8,
                implementation_effort="medium"
            )
        ]

        result = await enhancer.enhance_prompt(
            prompt, suggestions, OptimizationLevel.MODERATE
        )

        # 验证各组件都能正常工作
        assert isinstance(matches, list)
        # result可能为None如果没有有效改进

    @pytest.mark.asyncio
    async def test_schema_validation_integration(self, optimizer_with_templates):
        """测试schema验证集成"""
        # 测试有效请求
        valid_request = PromptOptimizationRequest(
            prompt_to_optimize="请分析技术趋势",
            optimization_level=OptimizationLevel.MODERATE,
            target_score_improvement=1.5
        )

        result = await optimizer_with_templates.optimize_prompt(valid_request)
        assert result.request_id == valid_request.request_id

        # 测试边界情况
        minimal_request = PromptOptimizationRequest(
            prompt_to_optimize="x" * 10,  # 最小长度
            optimization_level=OptimizationLevel.LIGHT
        )

        result = await optimizer_with_templates.optimize_prompt(minimal_request)
        # 应该成功处理或给出明确错误


class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_invalid_template_file_handling(self):
        """测试无效模板文件处理"""
        # 使用不存在的文件路径
        optimizer = PromptOptimizer()
        optimizer.template_matcher = TemplateMatcher("/non/existent/path.json")

        request = PromptOptimizationRequest(
            prompt_to_optimize="test prompt",
            optimization_level=OptimizationLevel.MODERATE,
            use_templates=True
        )

        # 应该能够处理而不崩溃
        result = await optimizer.optimize_prompt(request)

        # 验证能够返回结果（可能成功也可能失败，但不应该崩溃）
        assert result is not None
        assert hasattr(result, 'success')

    @pytest.mark.asyncio
    async def test_malformed_request_handling(self, optimizer_with_templates):
        """测试格式错误请求处理"""
        # 创建无效请求（空提示词）
        invalid_request = PromptOptimizationRequest(
            prompt_to_optimize="",
            optimization_level=OptimizationLevel.MODERATE
        )

        result = await optimizer_with_templates.optimize_prompt(invalid_request)

        # 应该失败但不崩溃
        assert not result.success
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, optimizer_with_templates):
        """测试并发请求处理"""
        import asyncio

        requests = [
            PromptOptimizationRequest(
                prompt_to_optimize=f"分析技术发展趋势 {i}",
                optimization_level=OptimizationLevel.LIGHT
            )
            for i in range(3)
        ]

        # 并发执行
        tasks = [optimizer_with_templates.optimize_prompt(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有请求都得到了处理
        assert len(results) == 3

        for result in results:
            # 结果可能是成功的优化结果或异常，但不应该是None
            assert result is not None
            if not isinstance(result, Exception):
                assert hasattr(result, 'success')


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.mark.asyncio
    async def test_optimization_performance(self, optimizer_with_templates):
        """测试优化性能"""
        import time

        prompt = "请详细分析人工智能技术在各个领域的应用现状，包括机器学习、深度学习、自然语言处理等技术的发展趋势和应用前景。"

        request = PromptOptimizationRequest(
            prompt_to_optimize=prompt,
            optimization_level=OptimizationLevel.MODERATE
        )

        start_time = time.time()
        result = await optimizer_with_templates.optimize_prompt(request)
        end_time = time.time()

        processing_time_seconds = end_time - start_time

        # 验证性能指标
        assert processing_time_seconds < 30  # 应该在30秒内完成
        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 30000  # 内部记录也应该在30秒内

    @pytest.mark.asyncio
    async def test_large_prompt_handling(self, optimizer_with_templates):
        """测试大型提示词处理"""
        # 创建较大的提示词（但不超过限制）
        large_prompt = """
        请作为一名资深的人工智能专家，深入分析当前人工智能技术的发展现状和未来趋势。

        分析要求：
        1. 技术现状分析
           - 机器学习算法的最新进展
           - 深度学习在各领域的应用
           - 自然语言处理技术突破
           - 计算机视觉技术发展

        2. 应用领域评估
           - 医疗健康领域的AI应用
           - 金融科技中的智能化解决方案
           - 自动驾驶技术进展
           - 智能制造和工业4.0

        3. 技术挑战分析
           - 数据隐私和安全问题
           - 算法公平性和偏见
           - 技术可解释性挑战
           - 计算资源和能耗问题

        4. 未来发展预测
           - 下一代AI技术方向
           - 产业应用前景展望
           - 社会影响和伦理考量
           - 政策法规发展趋势

        请确保分析内容准确、全面、深入，并提供具体的数据支撑和案例分析。
        """

        request = PromptOptimizationRequest(
            prompt_to_optimize=large_prompt,
            optimization_level=OptimizationLevel.MODERATE
        )

        result = await optimizer_with_templates.optimize_prompt(request)

        # 应该能够处理大型提示词
        assert result is not None
        if result.success:
            assert result.analysis is not None
            assert len(result.analysis.quality_scores) > 0


class TestDataFlowIntegration:
    """数据流集成测试"""

    @pytest.mark.asyncio
    async def test_requirements_to_optimization_flow(self, optimizer_with_templates):
        """测试需求到优化的完整数据流"""
        # 1. 模拟需求解析结果
        requirements = ParsedRequirements(
            original_input="帮我写一个技术分析报告",
            intent=ParsedIntent(
                category=IntentCategory.CREATE_PROMPT,
                confidence=0.9
            ),
            main_objective="创建技术分析报告",
            key_requirements=["技术准确", "结构清晰", "数据支撑"],
            domain_info=DomainInfo(
                name="技术分析",
                confidence=0.8,
                keywords=["技术", "分析", "报告"]
            )
        )

        # 2. 从需求创建提示词
        creation_result = await optimizer_with_templates.create_prompt_from_requirements(requirements)

        assert creation_result is not None

        # 3. 如果创建成功，进一步优化
        if creation_result.success and creation_result.optimized_prompt:
            optimization_request = PromptOptimizationRequest(
                prompt_to_optimize=creation_result.optimized_prompt.optimized_prompt,
                optimization_level=OptimizationLevel.LIGHT
            )

            optimization_result = await optimizer_with_templates.optimize_prompt(
                optimization_request, requirements
            )

            # 验证数据流的完整性
            assert optimization_result is not None
            if optimization_result.success:
                assert optimization_result.analysis is not None

    @pytest.mark.asyncio
    async def test_configuration_propagation(self, temp_template_file):
        """测试配置传播"""
        # 创建带有特定配置的优化器
        config = OptimizationConfig(
            max_optimization_iterations=2,
            enable_template_matching=True,
            include_analysis=True,
            include_alternatives=False
        )

        optimizer = PromptOptimizer(config)
        optimizer.template_matcher = TemplateMatcher(temp_template_file)

        request = PromptOptimizationRequest(
            prompt_to_optimize="测试提示词配置传播",
            optimization_level=OptimizationLevel.MODERATE
        )

        result = await optimizer.optimize_prompt(request)

        # 验证配置被正确应用
        if result.success:
            # include_analysis=True应该包含分析
            assert result.analysis is not None
            # include_alternatives=False应该不包含备选版本
            assert len(result.alternative_versions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])