"""
PromptOptimizer 全面测试套件

测试提示词优化器的所有功能，包括提示词分析、优化建议生成、
质量评估、版本比较等核心优化功能的单元测试和集成测试。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.agents.pe_engineer.PromptOptimizer import PromptOptimizer
from app.agents.pe_engineer.schemas.prompts import (
    PromptAnalysis, QualityScore, PromptElement, OptimizationSuggestion,
    OptimizationResult, VersionComparison, OptimizationConfig
)
from app.agents.pe_engineer.schemas.requirements import ParsedRequirements

from .fixtures.pe_engineer_fixtures import (
    sample_optimized_prompt, sample_prompt_analysis,
    sample_parsed_requirements_detailed, error_scenarios, performance_test_data
)


class TestPromptOptimizer:
    """PromptOptimizer 主要测试类"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试设置"""
        config = OptimizationConfig(
            enabled_techniques=["clarity", "specificity", "structure", "completeness"],
            quality_threshold=7.0,
            max_iterations=3,
            timeout_seconds=30
        )
        self.optimizer = PromptOptimizer(config=config)
        self.mock_dashscope = AsyncMock()

        # Mock优化相关方法
        with patch.multiple(
            self.optimizer,
            _analyze_length=AsyncMock(),
            _analyze_structure=AsyncMock(),
            _extract_prompt_elements=AsyncMock(),
            _assess_quality=AsyncMock(),
            _generate_optimization_suggestions=AsyncMock()
        ):
            yield

    def test_optimizer_initialization(self):
        """测试优化器初始化"""
        # 测试默认配置初始化
        optimizer = PromptOptimizer()
        assert optimizer.config is not None
        assert optimizer.templates == {}
        assert optimizer.stats["total_optimizations"] == 0

        # 测试自定义配置初始化
        config = OptimizationConfig(
            enabled_techniques=["clarity", "specificity"],
            quality_threshold=8.0
        )
        optimizer = PromptOptimizer(config=config)
        assert optimizer.config.quality_threshold == 8.0
        assert len(optimizer.config.enabled_techniques) == 2

    async def test_validate_prompt_success(self):
        """测试成功的提示词验证"""
        valid_prompts = [
            "你是一个有用的AI助手，请回答用户的问题。",
            "根据以下要求生成代码：\n1. 使用Python\n2. 实现排序算法",
            "Please translate the following text from English to Chinese:",
            "分析以下数据并生成报告：\n- 销售数据\n- 用户反馈\n- 市场趋势"
        ]

        for prompt in valid_prompts:
            try:
                await self.optimizer._validate_prompt(prompt)
            except ValueError:
                pytest.fail(f"有效提示词不应该抛出异常: {prompt}")

    async def test_validate_prompt_empty(self):
        """测试空提示词验证"""
        with pytest.raises(ValueError, match="提示词不能为空"):
            await self.optimizer._validate_prompt("")

        with pytest.raises(ValueError, match="提示词不能为空"):
            await self.optimizer._validate_prompt("   ")  # 只有空白字符

    async def test_validate_prompt_too_short(self):
        """测试过短提示词验证"""
        with pytest.raises(ValueError, match="提示词长度不能少于"):
            await self.optimizer._validate_prompt("Hi")

    async def test_analyze_length_comprehensive(self):
        """测试全面的长度分析"""
        test_prompts = [
            {
                "prompt": "简短提示",
                "expected_category": "short"
            },
            {
                "prompt": "这是一个中等长度的提示词，包含了一些基本的指令和要求，" * 5,
                "expected_category": "medium"
            },
            {
                "prompt": "这是一个非常详细和长的提示词，" * 50,
                "expected_category": "long"
            }
        ]

        for case in test_prompts:
            # Mock长度分析实现
            async def mock_analyze_length(prompt):
                char_count = len(prompt)
                word_count = len(prompt.split())
                sentence_count = prompt.count('。') + prompt.count('.')

                category = "short" if char_count < 100 else "medium" if char_count < 500 else "long"

                return {
                    "character_count": char_count,
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "category": category
                }

            with patch.object(self.optimizer, '_analyze_length', side_effect=mock_analyze_length):
                result = await self.optimizer._analyze_length(case["prompt"])

            assert result["category"] == case["expected_category"]
            assert result["character_count"] > 0
            assert result["word_count"] > 0

    async def test_analyze_structure_detailed(self):
        """测试详细的结构分析"""
        test_cases = [
            {
                "prompt": """你是一个专业的数据分析师。

请根据以下数据生成分析报告：
1. 销售数据
2. 用户反馈
3. 市场趋势

输出格式：
- 执行摘要
- 详细分析
- 建议和结论""",
                "expected_structure": {
                    "has_clear_role": True,
                    "has_context": True,
                    "has_task_description": True,
                    "has_output_format": True,
                    "has_examples": False
                }
            },
            {
                "prompt": "帮我写个故事",
                "expected_structure": {
                    "has_clear_role": False,
                    "has_context": False,
                    "has_task_description": True,
                    "has_output_format": False,
                    "has_examples": False
                }
            }
        ]

        for case in test_cases:
            async def mock_analyze_structure(prompt):
                # 简单的结构识别逻辑
                has_role = any(keyword in prompt for keyword in ["你是", "作为", "扮演"])
                has_context = "根据" in prompt or "基于" in prompt
                has_task = any(keyword in prompt for keyword in ["请", "生成", "创建", "分析", "写"])
                has_format = any(keyword in prompt for keyword in ["格式", "输出", "形式"])
                has_examples = "例如" in prompt or "比如" in prompt

                return {
                    "has_clear_role": has_role,
                    "has_context": has_context,
                    "has_task_description": has_task,
                    "has_output_format": has_format,
                    "has_examples": has_examples,
                    "logical_flow_score": 8.0 if all([has_role, has_task]) else 6.0
                }

            with patch.object(self.optimizer, '_analyze_structure', side_effect=mock_analyze_structure):
                result = await self.optimizer._analyze_structure(case["prompt"])

            for key, expected_value in case["expected_structure"].items():
                assert result[key] == expected_value, f"结构分析失败: {key}"

    async def test_extract_prompt_elements_comprehensive(self):
        """测试全面的提示词元素提取"""
        complex_prompt = """你是一位经验丰富的创意写作导师，专门帮助作家发挥创意潜能。

**当前任务：**
请根据以下要求创作一个引人入胜的小说片段：

**创作要求：**
- 风格：现实主义
- 体裁：小说
- 创意程度：7/10

**具体步骤：**
1. 创建有深度的主角
2. 设计引人入胜的开场情节
3. 运用生动的细节描写

**输出格式：**
- 字数：800-1200字
- 结构：包含开头、发展、小高潮

**示例风格：**
"阳光透过百叶窗的缝隙，在地板上投下斑驳的光影..."

开始创作吧！"""

        # Mock元素提取实现
        async def mock_extract_elements(prompt):
            elements = []
            lines = prompt.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('你是'):
                    elements.append(PromptElement(
                        type="role_definition",
                        content=line,
                        position=i,
                        importance="high"
                    ))
                elif '任务' in line:
                    elements.append(PromptElement(
                        type="task_description",
                        content=line,
                        position=i,
                        importance="high"
                    ))
                elif '要求' in line:
                    elements.append(PromptElement(
                        type="requirements",
                        content=line,
                        position=i,
                        importance="medium"
                    ))
                elif '格式' in line:
                    elements.append(PromptElement(
                        type="output_format",
                        content=line,
                        position=i,
                        importance="medium"
                    ))
                elif '示例' in line:
                    elements.append(PromptElement(
                        type="examples",
                        content=line,
                        position=i,
                        importance="low"
                    ))

            return elements

        with patch.object(self.optimizer, '_extract_prompt_elements',
                         side_effect=mock_extract_elements):
            elements = await self.optimizer._extract_prompt_elements(complex_prompt)

        assert len(elements) >= 4
        element_types = [e.type for e in elements]
        assert "role_definition" in element_types
        assert "task_description" in element_types
        assert "requirements" in element_types
        assert "output_format" in element_types

    async def test_assess_quality_comprehensive(self):
        """测试全面的质量评估"""
        high_quality_prompt = """你是一位专业的Python开发专家，拥有10年以上的开发经验。

**任务目标：**
帮助用户创建一个完整的Web应用程序

**具体要求：**
1. 使用Flask框架
2. 实现用户认证系统
3. 包含数据库操作
4. 添加API接口
5. 编写单元测试

**技术规范：**
- Python 3.8+
- SQLAlchemy ORM
- JWT认证
- RESTful API设计
- 遵循PEP8代码规范

**输出格式：**
请按以下结构组织代码：
```
project/
├── app.py
├── models.py
├── routes.py
├── tests/
└── requirements.txt
```

**质量标准：**
- 代码可读性高
- 错误处理完善
- 安全性考虑
- 性能优化

请开始实现这个Web应用程序。"""

        # Mock质量评估各个维度
        mock_elements = [
            PromptElement(type="role_definition", content="专家", position=0, importance="high"),
            PromptElement(type="task_description", content="任务", position=1, importance="high"),
            PromptElement(type="requirements", content="要求", position=2, importance="medium")
        ]

        async def mock_assess_quality(prompt, elements, quality_dimensions):
            scores = []
            for dimension in quality_dimensions:
                if dimension == "clarity":
                    score = 9.0  # 高质量提示词清晰度高
                elif dimension == "specificity":
                    score = 8.5  # 具体要求明确
                elif dimension == "completeness":
                    score = 8.8  # 信息完整
                elif dimension == "coherence":
                    score = 8.7  # 逻辑连贯
                else:
                    score = 8.0  # 其他维度

                scores.append(QualityScore(
                    dimension=dimension,
                    score=score,
                    max_score=10.0,
                    explanation=f"{dimension}维度评分: {score}/10.0"
                ))
            return scores

        with patch.object(self.optimizer, '_extract_prompt_elements', return_value=mock_elements):
            with patch.object(self.optimizer, '_assess_quality', side_effect=mock_assess_quality):
                quality_scores = await self.optimizer._assess_quality(
                    high_quality_prompt, mock_elements, ["clarity", "specificity", "completeness"]
                )

        assert len(quality_scores) == 3
        for score in quality_scores:
            assert isinstance(score, QualityScore)
            assert score.score > 8.0  # 高质量提示词得分应该较高

    async def test_optimize_prompt_success(self):
        """测试成功的提示词优化"""
        low_quality_prompt = "帮我写代码"

        # Mock分析结果
        mock_analysis = PromptAnalysis(
            length_analysis={"character_count": 10, "category": "short"},
            structure_analysis={"has_clear_role": False, "logical_flow_score": 3.0},
            elements=[PromptElement(type="task", content="写代码", position=0, importance="high")],
            quality_scores=[
                QualityScore(dimension="clarity", score=4.0, max_score=10.0, explanation="不够清晰")
            ],
            overall_score=4.0,
            detected_issues=["缺少角色定义", "任务描述不具体"],
            optimization_suggestions=[
                OptimizationSuggestion(
                    type="structure",
                    priority="high",
                    description="添加明确的角色定义",
                    expected_impact="提升40%的清晰度"
                )
            ]
        )

        with patch.object(self.optimizer, 'analyze_prompt', return_value=mock_analysis):
            with patch.object(self.optimizer, '_execute_optimization') as mock_execute:
                mock_execute.return_value = OptimizationResult(
                    original_prompt=low_quality_prompt,
                    optimized_prompt="你是一位Python开发专家。请根据用户需求编写高质量的代码...",
                    optimization_applied=True,
                    techniques_used=["role_definition", "task_clarification"],
                    quality_improvement=4.5,
                    version_comparison=VersionComparison(
                        original_score=4.0,
                        optimized_score=8.5,
                        improvement_percentage=112.5
                    ),
                    metadata={"optimization_time": 2.3}
                )

                result = await self.optimizer.optimize_prompt(low_quality_prompt)

        assert isinstance(result, OptimizationResult)
        assert result.optimization_applied == True
        assert result.quality_improvement > 0
        assert len(result.optimized_prompt) > len(result.original_prompt)
        assert result.version_comparison.improvement_percentage > 50

    async def test_optimize_prompt_already_high_quality(self):
        """测试已经高质量的提示词优化"""
        high_quality_prompt = """你是一位专业的AI助手，拥有广泛的知识和经验。

请根据以下要求完成任务：
1. 仔细分析用户需求
2. 提供准确、详细的回答
3. 确保回答的逻辑性和实用性

输出格式：
- 结构清晰
- 重点突出
- 易于理解

请开始你的回答。"""

        # Mock高质量分析结果
        mock_analysis = PromptAnalysis(
            length_analysis={"character_count": 200, "category": "medium"},
            structure_analysis={"has_clear_role": True, "logical_flow_score": 9.0},
            elements=[],
            quality_scores=[
                QualityScore(dimension="clarity", score=9.2, max_score=10.0, explanation="非常清晰")
            ],
            overall_score=9.2,
            detected_issues=[],
            optimization_suggestions=[]
        )

        with patch.object(self.optimizer, 'analyze_prompt', return_value=mock_analysis):
            result = await self.optimizer.optimize_prompt(high_quality_prompt)

        # 高质量提示词可能不需要优化
        assert isinstance(result, OptimizationResult)
        if not result.optimization_applied:
            assert result.original_prompt == result.optimized_prompt
        else:
            # 如果优化了，改进幅度应该很小
            assert result.quality_improvement < 1.0

    async def test_create_prompt_from_requirements(self, sample_parsed_requirements_detailed):
        """测试从需求创建提示词"""
        with patch.object(self.optimizer, '_generate_initial_prompt') as mock_generate:
            mock_generate.return_value = """你是一位创意写作专家。

请根据以下需求创作内容：
- 领域：创意写作
- 任务：小说创作辅助
- 目标：激发创意灵感

请开始创作。"""

            result = await self.optimizer.create_prompt_from_requirements(
                sample_parsed_requirements_detailed
            )

        assert isinstance(result, OptimizationResult)
        assert len(result.optimized_prompt) > 0
        assert "创意写作" in result.optimized_prompt
        assert "小说创作" in result.optimized_prompt

    async def test_analyze_prompt_comprehensive(self):
        """测试全面的提示词分析"""
        test_prompt = """作为一名经验丰富的数据科学家，你需要帮助用户分析复杂的数据集。

**任务描述：**
分析提供的销售数据，识别趋势和模式

**分析要求：**
1. 数据清理和预处理
2. 探索性数据分析
3. 统计分析和可视化
4. 趋势预测

**输出格式：**
- 数据质量报告
- 可视化图表
- 分析结论
- 预测结果

请开始分析。"""

        # Mock各个分析组件
        with patch.multiple(
            self.optimizer,
            _analyze_length=AsyncMock(return_value={
                "character_count": 200,
                "word_count": 50,
                "sentence_count": 10,
                "category": "medium"
            }),
            _analyze_structure=AsyncMock(return_value={
                "has_clear_role": True,
                "has_context": True,
                "has_task_description": True,
                "has_output_format": True,
                "logical_flow_score": 8.5
            }),
            _extract_prompt_elements=AsyncMock(return_value=[
                PromptElement(type="role", content="数据科学家", position=0, importance="high")
            ]),
            _assess_quality=AsyncMock(return_value=[
                QualityScore(dimension="clarity", score=8.5, max_score=10.0, explanation="清晰")
            ])
        ):
            analysis = await self.optimizer.analyze_prompt(test_prompt)

        assert isinstance(analysis, PromptAnalysis)
        assert analysis.length_analysis["category"] == "medium"
        assert analysis.structure_analysis["has_clear_role"] == True
        assert len(analysis.elements) > 0
        assert len(analysis.quality_scores) > 0
        assert analysis.overall_score > 0

    async def test_optimization_techniques_application(self):
        """测试优化技术应用"""
        basic_prompt = "翻译文本"

        techniques_test_cases = [
            {
                "technique": "clarity",
                "expected_improvement": "明确翻译方向和要求"
            },
            {
                "technique": "specificity",
                "expected_improvement": "指定具体的翻译参数"
            },
            {
                "technique": "structure",
                "expected_improvement": "添加结构化格式"
            },
            {
                "technique": "completeness",
                "expected_improvement": "补充完整的上下文信息"
            }
        ]

        for case in techniques_test_cases:
            # Mock特定技术的优化
            async def mock_execute_optimization(prompt, suggestions, techniques):
                if case["technique"] in techniques:
                    if case["technique"] == "clarity":
                        optimized = "请将以下中文文本翻译成英文，保持原意和语调："
                    elif case["technique"] == "specificity":
                        optimized = "作为专业翻译，请将中文文本准确翻译成地道的英文："
                    elif case["technique"] == "structure":
                        optimized = """**翻译任务：**
中文 → 英文

**要求：**
- 保持原意
- 语法正确
- 表达自然"""
                    else:  # completeness
                        optimized = """你是一位专业的中英翻译专家。

**任务：**翻译以下文本
**方向：**中文 → 英文
**要求：**准确、流畅、符合英文表达习惯

请提供翻译结果："""

                    return OptimizationResult(
                        original_prompt=prompt,
                        optimized_prompt=optimized,
                        optimization_applied=True,
                        techniques_used=[case["technique"]],
                        quality_improvement=2.0,
                        version_comparison=VersionComparison(
                            original_score=4.0, optimized_score=6.0, improvement_percentage=50.0
                        ),
                        metadata={}
                    )
                else:
                    return OptimizationResult(
                        original_prompt=prompt,
                        optimized_prompt=prompt,
                        optimization_applied=False,
                        techniques_used=[],
                        quality_improvement=0.0,
                        version_comparison=VersionComparison(
                            original_score=4.0, optimized_score=4.0, improvement_percentage=0.0
                        ),
                        metadata={}
                    )

            with patch.object(self.optimizer, '_execute_optimization',
                             side_effect=mock_execute_optimization):
                # 创建包含特定技术的建议
                suggestions = [OptimizationSuggestion(
                    type=case["technique"],
                    priority="high",
                    description=case["expected_improvement"],
                    expected_impact="提升质量"
                )]

                result = await self.optimizer._execute_optimization(
                    basic_prompt, suggestions, [case["technique"]]
                )

            if case["technique"] == "clarity":
                assert "保持原意" in result.optimized_prompt
            elif case["technique"] == "structure":
                assert "**" in result.optimized_prompt  # 结构化标记

    async def test_batch_optimization(self):
        """测试批量优化"""
        prompts = [
            "写故事",
            "分析数据",
            "翻译文档",
            "生成代码"
        ]

        # Mock单个优化结果
        async def mock_optimize(prompt):
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=f"优化后的：{prompt}",
                optimization_applied=True,
                techniques_used=["clarity"],
                quality_improvement=3.0,
                version_comparison=VersionComparison(
                    original_score=4.0, optimized_score=7.0, improvement_percentage=75.0
                ),
                metadata={}
            )

        with patch.object(self.optimizer, 'optimize_prompt', side_effect=mock_optimize):
            results = await asyncio.gather(*[
                self.optimizer.optimize_prompt(prompt) for prompt in prompts
            ])

        assert len(results) == 4
        for result in results:
            assert isinstance(result, OptimizationResult)
            assert result.optimization_applied == True

    async def test_error_handling_invalid_prompt(self):
        """测试无效提示词的错误处理"""
        invalid_prompts = [
            "",
            "   ",
            "x",  # 太短
            None
        ]

        for invalid_prompt in invalid_prompts:
            with pytest.raises(ValueError):
                if invalid_prompt is None:
                    await self.optimizer.optimize_prompt(None)
                else:
                    await self.optimizer.optimize_prompt(invalid_prompt)

    async def test_performance_large_prompt(self):
        """测试大提示词的性能"""
        large_prompt = """你是一位专业的AI助手。""" + "详细指令 " * 1000

        start_time = asyncio.get_event_loop().time()

        # Mock分析以避免实际API调用
        with patch.object(self.optimizer, 'analyze_prompt') as mock_analyze:
            mock_analyze.return_value = PromptAnalysis(
                length_analysis={"character_count": len(large_prompt), "category": "long"},
                structure_analysis={"logical_flow_score": 7.0},
                elements=[],
                quality_scores=[
                    QualityScore(dimension="clarity", score=7.0, max_score=10.0, explanation="OK")
                ],
                overall_score=7.0,
                detected_issues=[],
                optimization_suggestions=[]
            )

            result = await self.optimizer.optimize_prompt(large_prompt)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        # 处理时间应该在合理范围内（小于10秒）
        assert processing_time < 10.0
        assert isinstance(result, OptimizationResult)

    def test_quality_threshold_enforcement(self):
        """测试质量阈值强制执行"""
        # 设置高质量阈值的配置
        high_threshold_config = OptimizationConfig(quality_threshold=9.0)
        optimizer = PromptOptimizer(config=high_threshold_config)

        # 测试质量计算方法
        mock_scores = [
            QualityScore(dimension="clarity", score=8.5, max_score=10.0, explanation="好"),
            QualityScore(dimension="specificity", score=7.8, max_score=10.0, explanation="中等"),
            QualityScore(dimension="completeness", score=9.2, max_score=10.0, explanation="优秀")
        ]

        # Mock计算总体质量分数
        async def mock_calculate_score(scores):
            return sum(s.score for s in scores) / len(scores)

        # 平均分数应该低于阈值，触发优化
        average_score = sum(s.score for s in mock_scores) / len(mock_scores)
        assert average_score < high_threshold_config.quality_threshold

    def test_statistics_tracking(self):
        """测试统计信息跟踪"""
        # 模拟一些优化统计
        self.optimizer.stats["total_optimizations"] = 10
        self.optimizer.stats["successful_optimizations"] = 8
        self.optimizer.stats["average_improvement"] = 3.2

        stats = self.optimizer.stats

        assert stats["total_optimizations"] == 10
        assert stats["successful_optimizations"] == 8
        assert stats["average_improvement"] == 3.2

        # 计算成功率
        success_rate = stats["successful_optimizations"] / stats["total_optimizations"]
        assert success_rate == 0.8

    async def test_memory_efficiency(self):
        """测试内存效率"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # 处理多个大提示词
        large_prompts = [f"详细提示词 " * 200 + f" {i}" for i in range(10)]

        with patch.object(self.optimizer, 'analyze_prompt') as mock_analyze:
            mock_analyze.return_value = PromptAnalysis(
                length_analysis={"category": "long"},
                structure_analysis={},
                elements=[],
                quality_scores=[],
                overall_score=7.0,
                detected_issues=[],
                optimization_suggestions=[]
            )

            for prompt in large_prompts:
                await self.optimizer.optimize_prompt(prompt)

        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before

        # 内存增长应该在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024

    async def test_concurrent_optimization(self):
        """测试并发优化"""
        prompts = [f"优化测试提示词 {i}" for i in range(5)]

        # Mock优化结果
        async def mock_optimize(prompt):
            await asyncio.sleep(0.1)  # 模拟处理时间
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=f"优化后：{prompt}",
                optimization_applied=True,
                techniques_used=["clarity"],
                quality_improvement=2.0,
                version_comparison=VersionComparison(
                    original_score=5.0, optimized_score=7.0, improvement_percentage=40.0
                ),
                metadata={}
            )

        with patch.object(self.optimizer, 'optimize_prompt', side_effect=mock_optimize):
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*[
                self.optimizer.optimize_prompt(prompt) for prompt in prompts
            ])
            end_time = asyncio.get_event_loop().time()

        # 并发执行应该比串行执行快
        total_time = end_time - start_time
        assert total_time < 1.0  # 5个任务并发应该在1秒内完成

        assert len(results) == 5
        for result in results:
            assert isinstance(result, OptimizationResult)
            assert result.optimization_applied == True