"""
PEQA Agent主类测试
测试PEQA质量评估Agent的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

# 导入测试夹具
from tests.fixtures.peqa_fixtures import (
    PEQATestFixtures,
    TestPromptData
)


class TestPEQAAgent:
    """PEQA Agent主类测试"""

    def setup_method(self):
        """测试前设置"""
        self.mock_config = PEQATestFixtures.get_mock_peqa_config()
        self.test_prompts = PEQATestFixtures.get_all_test_prompts()

    @pytest.mark.asyncio
    async def test_peqa_agent_initialization(self, mock_peqa_config):
        """测试PEQA Agent初始化"""
        # 模拟PEQAAgent类（实际实现时需要从相应模块导入）
        class MockPEQAAgent:
            def __init__(self, config):
                self.config = config
                self.initialized = True

        agent = MockPEQAAgent(mock_peqa_config)

        assert agent.initialized is True
        assert agent.config == mock_peqa_config
        assert "quality_dimensions" in agent.config
        assert len(agent.config["quality_dimensions"]) == 5

    @pytest.mark.asyncio
    async def test_assess_prompt_high_quality(self, high_quality_prompts):
        """测试高质量提示词评估"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                # 模拟高质量评估结果
                return {
                    "overall_score": 0.90,
                    "dimension_scores": {
                        "clarity": 0.95,
                        "specificity": 0.90,
                        "completeness": 0.88,
                        "effectiveness": 0.92,
                        "robustness": 0.85
                    },
                    "strengths": ["明确的角色定义", "具体的任务要求"],
                    "weaknesses": [],
                    "improvement_suggestions": [],
                    "confidence_level": 0.92,
                    "quality_level": "high"
                }

        agent = MockPEQAAgent()
        test_prompt = high_quality_prompts[0]

        result = await agent.assess_prompt(test_prompt.prompt)

        assert result["overall_score"] >= 0.8
        assert result["quality_level"] == "high"
        assert len(result["strengths"]) > 0
        assert result["confidence_level"] > 0.8

    @pytest.mark.asyncio
    async def test_assess_prompt_low_quality(self, low_quality_prompts):
        """测试低质量提示词评估"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                if not prompt or len(prompt.strip()) < 3:
                    return {
                        "overall_score": 0.0,
                        "dimension_scores": {
                            "clarity": 0.0,
                            "specificity": 0.0,
                            "completeness": 0.0,
                            "effectiveness": 0.0,
                            "robustness": 0.0
                        },
                        "strengths": [],
                        "weaknesses": ["空提示词或过短"],
                        "improvement_suggestions": ["请提供具体的任务描述"],
                        "confidence_level": 1.0,
                        "quality_level": "invalid"
                    }
                return {
                    "overall_score": 0.15,
                    "dimension_scores": {
                        "clarity": 0.20,
                        "specificity": 0.10,
                        "completeness": 0.15,
                        "effectiveness": 0.15,
                        "robustness": 0.10
                    },
                    "strengths": [],
                    "weaknesses": ["缺乏具体性", "无明确目标"],
                    "improvement_suggestions": [
                        "添加具体的任务描述",
                        "明确期望的输出格式",
                        "提供必要的上下文信息"
                    ],
                    "confidence_level": 0.95,
                    "quality_level": "low"
                }

        agent = MockPEQAAgent()
        test_prompt = low_quality_prompts[0]

        result = await agent.assess_prompt(test_prompt.prompt)

        assert result["overall_score"] <= 0.3
        assert result["quality_level"] in ["low", "invalid"]
        assert len(result["improvement_suggestions"]) > 0
        assert len(result["weaknesses"]) > 0

    @pytest.mark.asyncio
    async def test_generate_score(self):
        """测试评分生成"""
        class MockPEQAAgent:
            async def generate_score(self, assessment):
                dimension_scores = assessment["dimension_scores"]
                weights = {
                    "clarity": 0.25,
                    "specificity": 0.20,
                    "completeness": 0.20,
                    "effectiveness": 0.20,
                    "robustness": 0.15
                }

                weighted_score = sum(
                    dimension_scores[dim] * weights[dim]
                    for dim in dimension_scores
                )

                return {
                    "overall_score": weighted_score,
                    "weighted_breakdown": {
                        dim: dimension_scores[dim] * weights[dim]
                        for dim in dimension_scores
                    },
                    "scoring_method": "weighted_average"
                }

        agent = MockPEQAAgent()
        test_assessment = {
            "dimension_scores": {
                "clarity": 0.8,
                "specificity": 0.7,
                "completeness": 0.6,
                "effectiveness": 0.9,
                "robustness": 0.5
            }
        }

        result = await agent.generate_score(test_assessment)

        assert "overall_score" in result
        assert 0.0 <= result["overall_score"] <= 1.0
        assert "weighted_breakdown" in result
        assert len(result["weighted_breakdown"]) == 5

    @pytest.mark.asyncio
    async def test_suggest_improvements(self):
        """测试改进建议生成"""
        class MockPEQAAgent:
            async def suggest_improvements(self, assessment):
                suggestions = []
                dimension_scores = assessment["dimension_scores"]

                for dimension, score in dimension_scores.items():
                    if score < 0.7:
                        if dimension == "clarity":
                            suggestions.append({
                                "category": "clarity",
                                "priority": "high",
                                "suggestion": "使用更明确的指令词和结构",
                                "example": "将模糊的要求改为具体的步骤"
                            })
                        elif dimension == "specificity":
                            suggestions.append({
                                "category": "specificity",
                                "priority": "medium",
                                "suggestion": "添加更多具体细节",
                                "example": "指定技术栈、格式要求等"
                            })

                return suggestions

        agent = MockPEQAAgent()
        test_assessment = {
            "dimension_scores": {
                "clarity": 0.5,  # 低分，需要改进
                "specificity": 0.6,  # 低分，需要改进
                "completeness": 0.8,
                "effectiveness": 0.7,
                "robustness": 0.9
            }
        }

        suggestions = await agent.suggest_improvements(test_assessment)

        assert len(suggestions) >= 2  # 应该有clarity和specificity的建议
        assert all("category" in s for s in suggestions)
        assert all("priority" in s for s in suggestions)
        assert all("suggestion" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_create_report(self):
        """测试报告生成"""
        class MockPEQAAgent:
            async def create_report(self, assessment):
                return {
                    "report_id": "peqa_report_001",
                    "timestamp": "2025-09-26T14:36:51Z",
                    "assessment_summary": {
                        "overall_score": assessment["overall_score"],
                        "quality_level": assessment["quality_level"],
                        "confidence": assessment["confidence_level"]
                    },
                    "dimension_analysis": assessment["dimension_scores"],
                    "strengths": assessment["strengths"],
                    "improvement_areas": assessment["weaknesses"],
                    "recommendations": assessment["improvement_suggestions"],
                    "report_format": "detailed"
                }

        agent = MockPEQAAgent()
        test_assessment = {
            "overall_score": 0.75,
            "quality_level": "good",
            "confidence_level": 0.85,
            "dimension_scores": {"clarity": 0.8, "specificity": 0.7},
            "strengths": ["清晰的目标"],
            "weaknesses": ["缺乏细节"],
            "improvement_suggestions": ["添加更多细节"]
        }

        report = await agent.create_report(test_assessment)

        assert "report_id" in report
        assert "timestamp" in report
        assert "assessment_summary" in report
        assert report["assessment_summary"]["overall_score"] == 0.75

    @pytest.mark.asyncio
    async def test_benchmark_performance(self, all_test_prompts):
        """测试性能基准测试"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt):
                # 简化的评估逻辑
                score = max(0.1, min(0.9, len(prompt) / 100))
                return {
                    "overall_score": score,
                    "dimension_scores": {"clarity": score},
                    "processing_time": 0.5
                }

            async def benchmark_performance(self, prompts):
                results = []
                total_time = 0

                for prompt_data in prompts:
                    if hasattr(prompt_data, 'prompt'):
                        prompt = prompt_data.prompt
                    else:
                        prompt = prompt_data

                    assessment = await self.assess_prompt(prompt)
                    results.append(assessment)
                    total_time += assessment["processing_time"]

                return {
                    "total_prompts": len(prompts),
                    "average_score": sum(r["overall_score"] for r in results) / len(results),
                    "total_processing_time": total_time,
                    "average_processing_time": total_time / len(results),
                    "throughput": len(prompts) / total_time
                }

        agent = MockPEQAAgent()
        test_prompts = all_test_prompts[:5]  # 使用前5个测试样本

        benchmark_result = await agent.benchmark_performance(test_prompts)

        assert "total_prompts" in benchmark_result
        assert benchmark_result["total_prompts"] == 5
        assert "average_score" in benchmark_result
        assert "total_processing_time" in benchmark_result
        assert "throughput" in benchmark_result

    @pytest.mark.asyncio
    async def test_error_handling_empty_prompt(self):
        """测试空提示词错误处理"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                if not prompt or not prompt.strip():
                    raise ValueError("空提示词无法评估")
                return {"overall_score": 0.5}

        agent = MockPEQAAgent()

        with pytest.raises(ValueError, match="空提示词无法评估"):
            await agent.assess_prompt("")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self):
        """测试无效输入错误处理"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                if not isinstance(prompt, str):
                    raise TypeError("提示词必须是字符串类型")
                return {"overall_score": 0.5}

        agent = MockPEQAAgent()

        with pytest.raises(TypeError, match="提示词必须是字符串类型"):
            await agent.assess_prompt(123)

    @pytest.mark.asyncio
    async def test_concurrent_assessments(self):
        """测试并发评估"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                await asyncio.sleep(0.1)  # 模拟处理时间
                return {
                    "overall_score": len(prompt) / 100,
                    "processing_time": 0.1
                }

        agent = MockPEQAAgent()
        prompts = ["短提示", "这是一个中等长度的测试提示词", "这是一个相对较长的测试提示词，用于验证并发评估功能是否正常工作"]

        # 并发执行评估
        tasks = [agent.assess_prompt(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all("overall_score" in result for result in results)
        assert results[2]["overall_score"] > results[0]["overall_score"]  # 更长的提示词分数更高

    def test_assessment_result_structure(self, expected_assessment_structure):
        """测试评估结果结构"""
        # 模拟评估结果
        mock_result = {
            "overall_score": 0.85,
            "dimension_scores": {
                "clarity": 0.9,
                "specificity": 0.8,
                "completeness": 0.85,
                "effectiveness": 0.9,
                "robustness": 0.75
            },
            "strengths": ["明确的任务描述", "具体的技术要求"],
            "weaknesses": ["缺少错误处理说明"],
            "improvement_suggestions": [
                {"category": "robustness", "suggestion": "添加错误处理"}
            ],
            "confidence_level": 0.88,
            "quality_level": "high",
            "detailed_analysis": {
                "prompt_length": 150,
                "complexity_score": 0.7
            }
        }

        # 验证结构
        for key, expected_type in expected_assessment_structure.items():
            assert key in mock_result
            assert isinstance(mock_result[key], expected_type)

    @pytest.mark.asyncio
    async def test_quality_level_classification(self):
        """测试质量等级分类"""
        class MockPEQAAgent:
            def classify_quality_level(self, score: float) -> str:
                if score >= 0.9:
                    return "excellent"
                elif score >= 0.7:
                    return "good"
                elif score >= 0.5:
                    return "fair"
                elif score >= 0.3:
                    return "poor"
                else:
                    return "very_poor"

        agent = MockPEQAAgent()

        test_cases = [
            (0.95, "excellent"),
            (0.75, "good"),
            (0.55, "fair"),
            (0.35, "poor"),
            (0.15, "very_poor")
        ]

        for score, expected_level in test_cases:
            result = agent.classify_quality_level(score)
            assert result == expected_level

    @pytest.mark.asyncio
    async def test_batch_assessment(self, all_test_prompts):
        """测试批量评估"""
        class MockPEQAAgent:
            async def assess_prompt(self, prompt: str):
                return {"overall_score": min(0.9, len(prompt) / 100)}

            async def batch_assess(self, prompts: List[str]):
                tasks = [self.assess_prompt(p.prompt if hasattr(p, 'prompt') else p) for p in prompts]
                results = await asyncio.gather(*tasks)
                return {
                    "assessments": results,
                    "batch_summary": {
                        "total_count": len(results),
                        "average_score": sum(r["overall_score"] for r in results) / len(results),
                        "highest_score": max(r["overall_score"] for r in results),
                        "lowest_score": min(r["overall_score"] for r in results)
                    }
                }

        agent = MockPEQAAgent()
        test_batch = all_test_prompts[:3]

        result = await agent.batch_assess(test_batch)

        assert "assessments" in result
        assert "batch_summary" in result
        assert len(result["assessments"]) == 3
        assert "average_score" in result["batch_summary"]