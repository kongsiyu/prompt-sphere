"""
PE Engineer Agent 测试数据和夹具

提供全面的测试数据，包括需求解析、表单生成、提示词优化等场景的
测试用例数据和mock配置。
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.agents.pe_engineer.types import (
    RequirementsParsed, DynamicForm, OptimizedPrompt, PromptTemplate,
    PETaskType, PETaskData, PEResponse,
    PromptType, ComplexityLevel, FormFieldType, FormField, FormSection
)
from app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, ExtractedContext, DomainInfo,
    TechnicalRequirement, QualityMetrics
)
from app.agents.pe_engineer.schemas.prompts import (
    PromptAnalysis, QualityScore, PromptElement, OptimizationSuggestion,
    OptimizationResult, VersionComparison
)


# 基础测试数据
@pytest.fixture
def sample_user_inputs():
    """用户输入示例数据"""
    return {
        "simple_creative": "我想要一个帮助我写创意小说的提示词",
        "complex_analytical": "我需要一个分析财务数据的提示词，要求能够处理多种数据格式，生成可视化图表，并提供投资建议",
        "code_generation": "创建一个Python代码生成器，能够根据需求描述生成完整的类和方法",
        "translation": "我要一个中英互译的提示词，保持原文的语气和风格",
        "conversational": "设计一个客服机器人对话提示词，要求专业、友好且能处理投诉",
        "empty": "",
        "too_long": "这是一个非常非常长的需求" + "描述" * 200,
        "ambiguous": "我想要一个好的提示词",
        "multilingual": "I need a prompt for 创建多语言content，supporting English and 中文"
    }


@pytest.fixture
def sample_parsed_requirements():
    """解析后的需求示例"""
    return RequirementsParsed(
        intent="创建创意写作助手",
        context="用户希望获得小说写作的帮助",
        domain="creative_writing",
        complexity=ComplexityLevel.MEDIUM,
        key_requirements=["创意激发", "故事结构", "角色发展"],
        constraints=["适合中文写作", "保持原创性"],
        target_audience="作家和写作爱好者",
        expected_output="创意写作提示和建议",
        prompt_type=PromptType.CREATIVE,
        confidence_score=0.85,
        suggestions=["添加具体的写作风格要求", "明确故事题材偏好"]
    )


@pytest.fixture
def sample_dynamic_form():
    """动态表单示例"""
    return DynamicForm(
        title="创意写作助手配置",
        description="配置您的个性化创意写作助手",
        sections=[
            FormSection(
                title="基础设置",
                description="设置写作的基本参数",
                fields=[
                    FormField(
                        name="writing_style",
                        label="写作风格",
                        field_type=FormFieldType.SELECT,
                        required=True,
                        options=["现实主义", "魔幻现实", "科幻", "悬疑"],
                        default_value="现实主义"
                    ),
                    FormField(
                        name="genre",
                        label="文学体裁",
                        field_type=FormFieldType.MULTISELECT,
                        required=True,
                        options=["小说", "散文", "诗歌", "剧本"],
                        default_value=["小说"]
                    )
                ]
            ),
            FormSection(
                title="高级设置",
                description="配置高级写作参数",
                fields=[
                    FormField(
                        name="creativity_level",
                        label="创意程度",
                        field_type=FormFieldType.SLIDER,
                        required=False,
                        min_value=1,
                        max_value=10,
                        default_value=7
                    )
                ]
            )
        ],
        estimated_time=3
    )


@pytest.fixture
def sample_optimized_prompt():
    """优化后的提示词示例"""
    return OptimizedPrompt(
        original_prompt="帮我写小说",
        optimized_prompt="""你是一位经验丰富的创意写作导师，专门帮助作家发挥创意潜能。

请根据以下要求创作一个引人入胜的小说片段：

**创作要求：**
- 风格：现实主义
- 体裁：小说
- 创意程度：7/10（在现实基础上融入适度想象）

**具体任务：**
1. 创建一个有深度的主角
2. 设计一个引人入胜的开场情节
3. 运用生动的细节描写
4. 保持故事的逻辑性和可读性

**输出格式：**
- 字数：800-1200字
- 结构：包含开头、发展、小高潮
- 风格：优美流畅，符合现实主义特点

开始创作吧，让想象力在现实的土壤中绽放！""",
        optimization_techniques=["结构化指令", "具体化要求", "角色定位", "输出规格化"],
        quality_score=8.7,
        confidence_score=0.92,
        improvements=[
            "将模糊的'帮我写小说'转换为具体的创作指导",
            "添加了角色设定和情景描述",
            "明确了输出格式和质量要求",
            "融入了创意度量化指标"
        ],
        metadata={
            "optimization_time": 2.3,
            "technique_count": 4,
            "improvement_areas": ["clarity", "specificity", "structure"]
        }
    )


@pytest.fixture
def sample_parsed_requirements_detailed():
    """详细的解析需求示例（使用schemas）"""
    return ParsedRequirements(
        intent=ParsedIntent(
            primary="creative_writing_assistance",
            secondary=["story_structure", "character_development"],
            confidence=0.88
        ),
        contexts=[
            ExtractedContext(
                type="domain",
                content="创意写作",
                relevance=0.95
            ),
            ExtractedContext(
                type="task",
                content="小说创作辅助",
                relevance=0.90
            )
        ],
        domain=DomainInfo(
            primary="creative_writing",
            secondary=["literature", "storytelling"],
            confidence=0.92
        ),
        technical_requirements=[
            TechnicalRequirement(
                type="functionality",
                description="创意激发功能",
                priority="high",
                complexity="medium"
            ),
            TechnicalRequirement(
                type="output_format",
                description="结构化写作建议",
                priority="medium",
                complexity="low"
            )
        ],
        quality_metrics=QualityMetrics(
            clarity=0.85,
            specificity=0.75,
            completeness=0.80,
            feasibility=0.90,
            overall_confidence=0.82
        ),
        suggestions={
            "improvements": ["明确写作风格偏好", "添加目标读者信息"],
            "clarifications": ["确定故事长度", "指定写作难度"],
            "enhancements": ["考虑添加范例", "提供模板选择"]
        },
        metadata={
            "parsing_time": 1.5,
            "complexity_score": 6.5,
            "language": "zh",
            "input_length": 15
        }
    )


@pytest.fixture
def sample_prompt_analysis():
    """提示词分析结果示例"""
    return PromptAnalysis(
        length_analysis={
            "character_count": 245,
            "word_count": 98,
            "sentence_count": 8,
            "category": "medium"
        },
        structure_analysis={
            "has_clear_role": True,
            "has_context": True,
            "has_task_description": True,
            "has_output_format": True,
            "has_examples": False,
            "logical_flow_score": 8.2
        },
        elements=[
            PromptElement(
                type="role_definition",
                content="你是一位经验丰富的创意写作导师",
                position=0,
                importance="high"
            ),
            PromptElement(
                type="task_description",
                content="创作一个引人入胜的小说片段",
                position=1,
                importance="high"
            )
        ],
        quality_scores=[
            QualityScore(
                dimension="clarity",
                score=8.5,
                max_score=10.0,
                explanation="指令清晰明确，容易理解"
            ),
            QualityScore(
                dimension="specificity",
                score=7.8,
                max_score=10.0,
                explanation="要求相对具体，但可进一步细化"
            )
        ],
        overall_score=8.2,
        detected_issues=[
            "缺少具体的示例",
            "输出长度要求可以更明确"
        ],
        optimization_suggestions=[
            OptimizationSuggestion(
                type="structure",
                priority="medium",
                description="添加具体示例以提高理解度",
                expected_impact="提升15%的输出质量"
            )
        ]
    )


@pytest.fixture
def sample_form_data():
    """表单数据示例"""
    return {
        "writing_style": "现实主义",
        "genre": ["小说", "散文"],
        "creativity_level": 7,
        "target_audience": "成年读者",
        "word_count": "1000-2000",
        "tone": "温暖感性",
        "special_requirements": "需要包含环境描写"
    }


@pytest.fixture
def sample_prompt_templates():
    """提示词模板示例"""
    return [
        PromptTemplate(
            id="creative_writing_basic",
            name="基础创意写作",
            description="适用于一般创意写作需求",
            category="creative",
            template="""你是一位{role}，专门帮助{target_audience}进行{task_type}。

请根据以下要求创作：
- 风格：{style}
- 长度：{length}
- 特殊要求：{special_requirements}

开始创作吧！""",
            variables=["role", "target_audience", "task_type", "style", "length", "special_requirements"],
            usage_count=156,
            rating=4.8,
            created_at=datetime.now()
        )
    ]


# Mock对象配置
@pytest.fixture
def mock_dashscope_client():
    """Mock DashScope API客户端"""
    mock = AsyncMock()
    mock.call_api.return_value = {
        "output": {
            "text": """{"intent": "creative_writing", "confidence": 0.88, "requirements": ["创意激发", "故事结构"]}"""
        }
    }
    return mock


@pytest.fixture
def mock_pe_engineer_config():
    """Mock PE Engineer配置"""
    mock = MagicMock()
    mock.agent_id = "pe_engineer_test"
    mock.model_config.temperature = 0.7
    mock.model_config.max_tokens = 2000
    mock.processing.max_concurrent_tasks = 5
    mock.processing.timeout_seconds = 30
    mock.parsing.cache_enabled = True
    mock.parsing.cache_size = 1000
    mock.optimization.enabled_techniques = ["clarity", "specificity", "structure"]
    return mock


@pytest.fixture
def mock_requirements_parser():
    """Mock RequirementsParser"""
    mock = AsyncMock()
    mock.parse_requirements.return_value = ParsedRequirements(
        intent=ParsedIntent(primary="test_intent", secondary=[], confidence=0.8),
        contexts=[],
        domain=DomainInfo(primary="test_domain", secondary=[], confidence=0.8),
        technical_requirements=[],
        quality_metrics=QualityMetrics(
            clarity=0.8, specificity=0.8, completeness=0.8,
            feasibility=0.8, overall_confidence=0.8
        ),
        suggestions={
            "improvements": [],
            "clarifications": [],
            "enhancements": []
        },
        metadata={}
    )
    return mock


@pytest.fixture
def mock_prompt_optimizer():
    """Mock PromptOptimizer"""
    mock = AsyncMock()
    mock.optimize_prompt.return_value = OptimizationResult(
        original_prompt="test",
        optimized_prompt="optimized test",
        optimization_applied=True,
        techniques_used=["clarity"],
        quality_improvement=0.2,
        version_comparison=VersionComparison(
            original_score=7.0,
            optimized_score=8.4,
            improvement_percentage=20.0
        ),
        metadata={}
    )
    return mock


# 测试场景数据
@pytest.fixture
def error_scenarios():
    """错误场景测试数据"""
    return {
        "empty_input": {
            "input": "",
            "expected_error": "输入不能为空"
        },
        "too_long_input": {
            "input": "x" * 10000,
            "expected_error": "输入长度超过限制"
        },
        "invalid_json": {
            "input": "这不是一个有效的JSON",
            "expected_error": "JSON解析失败"
        },
        "missing_required_field": {
            "form_data": {"style": "creative"},
            "expected_error": "缺少必需字段"
        },
        "api_timeout": {
            "scenario": "API调用超时",
            "expected_error": "请求超时"
        },
        "api_rate_limit": {
            "scenario": "API速率限制",
            "expected_error": "请求频率过高"
        }
    }


@pytest.fixture
def performance_test_data():
    """性能测试数据"""
    return {
        "concurrent_requests": [
            {"user_input": f"测试需求{i}", "expected_response_time": 2.0}
            for i in range(10)
        ],
        "large_inputs": [
            {"input": "详细需求描述 " * 100, "max_processing_time": 5.0},
            {"input": "复杂业务逻辑 " * 200, "max_processing_time": 8.0}
        ],
        "batch_operations": {
            "small_batch": [f"简单需求{i}" for i in range(5)],
            "medium_batch": [f"中等需求{i}" for i in range(20)],
            "large_batch": [f"复杂需求{i}" for i in range(50)]
        }
    }


@pytest.fixture
def integration_test_config():
    """集成测试配置"""
    return {
        "dashscope_api": {
            "mock_enabled": True,
            "response_delay": 0.1,
            "success_rate": 0.95
        },
        "database": {
            "mock_enabled": True,
            "connection_pool_size": 5
        },
        "cache": {
            "enabled": True,
            "ttl": 300
        }
    }