"""
PEQA测试夹具
为PEQA质量评估Agent的测试提供模拟数据和配置
"""

import pytest
from typing import Dict, List, Any
from dataclasses import dataclass
from unittest.mock import Mock, AsyncMock


@dataclass
class TestPromptData:
    """测试提示词数据"""
    prompt: str
    expected_clarity: float
    expected_specificity: float
    expected_completeness: float
    expected_effectiveness: float
    expected_robustness: float
    expected_overall: float
    quality_level: str  # "high", "medium", "low"
    issues: List[str]
    strengths: List[str]


class PEQATestFixtures:
    """PEQA测试夹具类"""

    @staticmethod
    def get_high_quality_prompts() -> List[TestPromptData]:
        """高质量提示词测试数据"""
        return [
            TestPromptData(
                prompt="作为一个专业的Python开发工程师，请为我编写一个完整的数据分析脚本。要求：1)读取CSV文件data.csv，2)计算销售额的平均值、中位数和标准差，3)生成可视化图表保存为sales_analysis.png，4)输出详细的统计报告。请包含错误处理和代码注释。",
                expected_clarity=0.95,
                expected_specificity=0.90,
                expected_completeness=0.88,
                expected_effectiveness=0.92,
                expected_robustness=0.85,
                expected_overall=0.90,
                quality_level="high",
                issues=[],
                strengths=["明确的角色定义", "具体的任务要求", "详细的输出规范", "包含错误处理要求"]
            ),
            TestPromptData(
                prompt="请分析以下JSON数据结构：{'users': [{'id': 1, 'name': 'Alice', 'age': 25}, {'id': 2, 'name': 'Bob', 'age': 30}]}，并生成一个Python类来处理这些数据，包括：1)数据验证方法，2)年龄统计功能，3)用户查找方法，4)导出为CSV的功能。请使用类型提示和文档字符串。",
                expected_clarity=0.92,
                expected_specificity=0.88,
                expected_completeness=0.85,
                expected_effectiveness=0.90,
                expected_robustness=0.82,
                expected_overall=0.87,
                quality_level="high",
                issues=[],
                strengths=["提供了具体数据示例", "明确的功能要求", "技术规范清晰"]
            )
        ]

    @staticmethod
    def get_medium_quality_prompts() -> List[TestPromptData]:
        """中等质量提示词测试数据"""
        return [
            TestPromptData(
                prompt="帮我写一个网站，要有用户登录功能。",
                expected_clarity=0.60,
                expected_specificity=0.40,
                expected_completeness=0.35,
                expected_effectiveness=0.45,
                expected_robustness=0.30,
                expected_overall=0.42,
                quality_level="medium",
                issues=["缺乏技术栈说明", "功能描述过于简单", "没有具体要求"],
                strengths=["目标明确"]
            ),
            TestPromptData(
                prompt="我需要分析一些数据，请给我一些建议。数据大概有几千条记录，包含用户信息。",
                expected_clarity=0.65,
                expected_specificity=0.45,
                expected_completeness=0.40,
                expected_effectiveness=0.50,
                expected_robustness=0.35,
                expected_overall=0.47,
                quality_level="medium",
                issues=["分析目标不明确", "数据结构描述模糊", "期望输出未说明"],
                strengths=["提供了数据规模信息", "有一定的上下文"]
            )
        ]

    @staticmethod
    def get_low_quality_prompts() -> List[TestPromptData]:
        """低质量提示词测试数据"""
        return [
            TestPromptData(
                prompt="写代码",
                expected_clarity=0.20,
                expected_specificity=0.10,
                expected_completeness=0.15,
                expected_effectiveness=0.15,
                expected_robustness=0.10,
                expected_overall=0.14,
                quality_level="low",
                issues=["极度缺乏具体性", "没有上下文", "目标不明确", "无技术要求"],
                strengths=[]
            ),
            TestPromptData(
                prompt="帮我做个东西",
                expected_clarity=0.25,
                expected_specificity=0.15,
                expected_completeness=0.20,
                expected_effectiveness=0.20,
                expected_robustness=0.15,
                expected_overall=0.19,
                quality_level="low",
                issues=["完全缺乏具体信息", "无明确目标", "无技术细节"],
                strengths=[]
            )
        ]

    @staticmethod
    def get_edge_case_prompts() -> List[TestPromptData]:
        """边界情况测试数据"""
        return [
            TestPromptData(
                prompt="",  # 空提示词
                expected_clarity=0.0,
                expected_specificity=0.0,
                expected_completeness=0.0,
                expected_effectiveness=0.0,
                expected_robustness=0.0,
                expected_overall=0.0,
                quality_level="invalid",
                issues=["空提示词"],
                strengths=[]
            ),
            TestPromptData(
                prompt="a" * 10000,  # 超长提示词
                expected_clarity=0.1,
                expected_specificity=0.1,
                expected_completeness=0.1,
                expected_effectiveness=0.1,
                expected_robustness=0.1,
                expected_overall=0.1,
                quality_level="low",
                issues=["提示词过长", "缺乏结构"],
                strengths=[]
            )
        ]

    @staticmethod
    def get_all_test_prompts() -> List[TestPromptData]:
        """获取所有测试提示词"""
        return (
            PEQATestFixtures.get_high_quality_prompts() +
            PEQATestFixtures.get_medium_quality_prompts() +
            PEQATestFixtures.get_low_quality_prompts() +
            PEQATestFixtures.get_edge_case_prompts()
        )

    @staticmethod
    def get_mock_dashscope_client():
        """模拟DashScope客户端"""
        mock_client = Mock()
        mock_client.generate = AsyncMock()

        # 模拟不同的API响应
        def side_effect(prompt, **kwargs):
            if "clarity" in prompt.lower():
                return Mock(output=Mock(text="0.85"))
            elif "specificity" in prompt.lower():
                return Mock(output=Mock(text="0.78"))
            elif "completeness" in prompt.lower():
                return Mock(output=Mock(text="0.82"))
            elif "effectiveness" in prompt.lower():
                return Mock(output=Mock(text="0.80"))
            elif "robustness" in prompt.lower():
                return Mock(output=Mock(text="0.75"))
            else:
                return Mock(output=Mock(text="0.80"))

        mock_client.generate.side_effect = side_effect
        return mock_client

    @staticmethod
    def get_mock_peqa_config():
        """模拟PEQA配置"""
        return {
            "model_name": "qwen-max",
            "max_retries": 3,
            "timeout": 30,
            "quality_dimensions": {
                "clarity": {
                    "weight": 0.25,
                    "description": "清晰度和明确性"
                },
                "specificity": {
                    "weight": 0.20,
                    "description": "具体性和细节"
                },
                "completeness": {
                    "weight": 0.20,
                    "description": "完整性和全面性"
                },
                "effectiveness": {
                    "weight": 0.20,
                    "description": "有效性和实用性"
                },
                "robustness": {
                    "weight": 0.15,
                    "description": "鲁棒性和容错性"
                }
            },
            "scoring_thresholds": {
                "excellent": 0.9,
                "good": 0.7,
                "fair": 0.5,
                "poor": 0.3
            }
        }

    @staticmethod
    def get_expected_assessment_structure():
        """期望的评估结果结构"""
        return {
            "overall_score": float,
            "dimension_scores": dict,
            "strengths": list,
            "weaknesses": list,
            "improvement_suggestions": list,
            "confidence_level": float,
            "quality_level": str,
            "detailed_analysis": dict
        }

    @staticmethod
    def get_expected_improvement_suggestions():
        """期望的改进建议结构"""
        return [
            {
                "category": "clarity",
                "priority": "high",
                "suggestion": "使用更明确的指令词",
                "example": "将'帮我做'改为'请为我创建'"
            },
            {
                "category": "specificity",
                "priority": "medium",
                "suggestion": "添加具体的技术要求",
                "example": "指定编程语言、框架版本等"
            }
        ]


@pytest.fixture
def high_quality_prompts():
    """高质量提示词夹具"""
    return PEQATestFixtures.get_high_quality_prompts()


@pytest.fixture
def medium_quality_prompts():
    """中等质量提示词夹具"""
    return PEQATestFixtures.get_medium_quality_prompts()


@pytest.fixture
def low_quality_prompts():
    """低质量提示词夹具"""
    return PEQATestFixtures.get_low_quality_prompts()


@pytest.fixture
def edge_case_prompts():
    """边界情况提示词夹具"""
    return PEQATestFixtures.get_edge_case_prompts()


@pytest.fixture
def all_test_prompts():
    """所有测试提示词夹具"""
    return PEQATestFixtures.get_all_test_prompts()


@pytest.fixture
def mock_dashscope_client():
    """模拟DashScope客户端夹具"""
    return PEQATestFixtures.get_mock_dashscope_client()


@pytest.fixture
def mock_peqa_config():
    """模拟PEQA配置夹具"""
    return PEQATestFixtures.get_mock_peqa_config()


@pytest.fixture
def expected_assessment_structure():
    """期望评估结构夹具"""
    return PEQATestFixtures.get_expected_assessment_structure()


@pytest.fixture
def expected_improvement_suggestions():
    """期望改进建议夹具"""
    return PEQATestFixtures.get_expected_improvement_suggestions()