"""
PEEngineerAgent 全面测试套件

测试 PE Engineer Agent 的所有核心功能，包括需求解析、表单生成、
提示词创建和优化等功能的单元测试、集成测试和错误处理测试。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.agents.pe_engineer.PEEngineerAgent import PEEngineerAgent
from app.agents.pe_engineer.types import (
    RequirementsParsed, DynamicForm, OptimizedPrompt,
    PromptType, ComplexityLevel, PETaskType, PETaskData
)
from app.agents.base.message_types import TaskMessage

from .fixtures.pe_engineer_fixtures import (
    sample_user_inputs, sample_parsed_requirements, sample_dynamic_form,
    sample_optimized_prompt, sample_form_data, mock_pe_engineer_config,
    mock_dashscope_client, error_scenarios, performance_test_data
)


class TestPEEngineerAgent:
    """PEEngineerAgent 主要测试类"""

    @pytest.fixture(autouse=True)
    async def setup(self, mock_pe_engineer_config, mock_dashscope_client):
        """测试设置"""
        with patch('app.agents.pe_engineer.PEEngineerAgent.get_config', return_value=mock_pe_engineer_config):
            self.agent = PEEngineerAgent(config=mock_pe_engineer_config)
            self.mock_client = mock_dashscope_client
            # Mock DashScope API调用
            with patch.object(self.agent, '_call_dashscope_api', self.mock_client.call_api):
                yield

    def test_agent_initialization(self, mock_pe_engineer_config):
        """测试Agent初始化"""
        # 测试正常初始化
        agent = PEEngineerAgent(config=mock_pe_engineer_config)
        assert agent.agent_id == "pe_engineer_test"
        assert agent.agent_type == "PE_ENGINEER"
        assert agent.config == mock_pe_engineer_config

        # 测试默认配置初始化
        with patch('app.agents.pe_engineer.config.get_config') as mock_get_config:
            mock_get_config.return_value = mock_pe_engineer_config
            agent = PEEngineerAgent()
            assert agent.config is not None

    async def test_get_capabilities(self):
        """测试获取能力列表"""
        capabilities = await self.agent.get_capabilities()

        expected_capabilities = [
            "requirements_parsing",
            "form_generation",
            "prompt_creation",
            "prompt_optimization",
            "template_management"
        ]

        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        for cap in expected_capabilities:
            assert cap in capabilities

    async def test_parse_requirements_success(self, sample_user_inputs):
        """测试需求解析成功场景"""
        # Mock API响应
        mock_response = """
        {
            "intent": "创建创意写作助手",
            "context": "用户希望获得小说写作的帮助",
            "domain": "creative_writing",
            "complexity": "medium",
            "key_requirements": ["创意激发", "故事结构", "角色发展"],
            "constraints": ["适合中文写作", "保持原创性"],
            "target_audience": "作家和写作爱好者",
            "expected_output": "创意写作提示和建议",
            "prompt_type": "creative",
            "confidence_score": 0.85
        }
        """

        with patch.object(self.agent, '_call_dashscope_api', return_value=mock_response):
            result = await self.agent.parse_requirements(sample_user_inputs["simple_creative"])

        assert isinstance(result, RequirementsParsed)
        assert result.intent == "创建创意写作助手"
        assert result.prompt_type == PromptType.CREATIVE
        assert result.complexity == ComplexityLevel.MEDIUM
        assert result.confidence_score == 0.85
        assert len(result.key_requirements) == 3

    async def test_parse_requirements_empty_input(self):
        """测试空输入的需求解析"""
        with pytest.raises(ValueError, match="输入不能为空"):
            await self.agent.parse_requirements("")

    async def test_parse_requirements_too_long_input(self):
        """测试过长输入的需求解析"""
        long_input = "x" * 10000
        with pytest.raises(ValueError, match="输入长度超过限制"):
            await self.agent.parse_requirements(long_input)

    async def test_parse_requirements_api_failure(self, sample_user_inputs):
        """测试API调用失败的需求解析"""
        with patch.object(self.agent, '_call_dashscope_api', side_effect=Exception("API调用失败")):
            result = await self.agent.parse_requirements(sample_user_inputs["simple_creative"])

        # 应该返回回退结果
        assert isinstance(result, RequirementsParsed)
        assert result.confidence_score < 0.5  # 回退结果置信度较低

    async def test_generate_form_success(self, sample_parsed_requirements):
        """测试表单生成成功场景"""
        mock_response = """
        {
            "sections": [
                {
                    "title": "基础设置",
                    "description": "设置写作的基本参数",
                    "fields": [
                        {
                            "name": "writing_style",
                            "label": "写作风格",
                            "type": "select",
                            "required": true,
                            "options": ["现实主义", "魔幻现实", "科幻", "悬疑"]
                        }
                    ]
                }
            ]
        }
        """

        with patch.object(self.agent, '_call_dashscope_api', return_value=mock_response):
            result = await self.agent.generate_form(sample_parsed_requirements)

        assert isinstance(result, DynamicForm)
        assert len(result.sections) > 0
        assert result.sections[0].title == "基础设置"
        assert len(result.sections[0].fields) > 0

    async def test_generate_form_invalid_requirements(self):
        """测试无效需求的表单生成"""
        invalid_requirements = RequirementsParsed(
            intent="",
            context="",
            domain="unknown",
            complexity=ComplexityLevel.SIMPLE,
            key_requirements=[],
            constraints=[],
            target_audience="",
            expected_output="",
            prompt_type=PromptType.GENERAL,
            confidence_score=0.1
        )

        with pytest.raises(ValueError, match="需求信息不完整"):
            await self.agent.generate_form(invalid_requirements)

    async def test_create_prompt_success(self, sample_form_data):
        """测试提示词创建成功场景"""
        mock_response = """
        {
            "prompt": "你是一位经验丰富的创意写作导师...",
            "quality_score": 8.7,
            "techniques_used": ["结构化指令", "具体化要求"],
            "improvements": ["明确了角色定位", "添加了输出格式要求"]
        }
        """

        with patch.object(self.agent, '_call_dashscope_api', return_value=mock_response):
            result = await self.agent.create_prompt(sample_form_data)

        assert isinstance(result, OptimizedPrompt)
        assert len(result.optimized_prompt) > 0
        assert result.quality_score > 0
        assert len(result.optimization_techniques) > 0

    async def test_create_prompt_empty_form_data(self):
        """测试空表单数据的提示词创建"""
        with pytest.raises(ValueError, match="表单数据不能为空"):
            await self.agent.create_prompt({})

    async def test_optimize_prompt_success(self):
        """测试提示词优化成功场景"""
        original_prompt = "帮我写小说"
        mock_response = """
        {
            "optimized_prompt": "你是一位经验丰富的创意写作导师...",
            "optimization_techniques": ["结构化指令", "角色定位", "具体化要求"],
            "quality_score": 8.7,
            "improvements": ["明确了任务目标", "添加了专业背景"]
        }
        """

        with patch.object(self.agent, '_call_dashscope_api', return_value=mock_response):
            result = await self.agent.optimize_prompt(original_prompt)

        assert isinstance(result, OptimizedPrompt)
        assert result.original_prompt == original_prompt
        assert len(result.optimized_prompt) > len(original_prompt)
        assert result.quality_score > 0

    async def test_optimize_prompt_empty_input(self):
        """测试空输入的提示词优化"""
        with pytest.raises(ValueError, match="提示词不能为空"):
            await self.agent.optimize_prompt("")

    async def test_optimize_prompt_already_optimized(self):
        """测试已优化提示词的再次优化"""
        high_quality_prompt = """你是一位专业的AI助手，具有丰富的知识和经验。

请根据以下要求完成任务：
1. 仔细分析用户需求
2. 提供准确、详细的回答
3. 确保回答的逻辑性和实用性

输出格式：
- 结构清晰
- 重点突出
- 易于理解

请开始你的回答。"""

        with patch.object(self.agent, '_evaluate_prompt_quality', return_value={"quality_score": 9.2}):
            result = await self.agent.optimize_prompt(high_quality_prompt)

        # 高质量提示词可能不需要大幅优化
        assert isinstance(result, OptimizedPrompt)
        assert result.quality_score > 8.5

    async def test_process_task_parse_requirements(self, sample_user_inputs):
        """测试处理需求解析任务"""
        task = TaskMessage(
            task_id="test_task_1",
            agent_id=self.agent.agent_id,
            task_type="parse_requirements",
            data=PETaskData(
                task_type=PETaskType.PARSE_REQUIREMENTS,
                user_input=sample_user_inputs["simple_creative"]
            ),
            priority=1,
            created_at=asyncio.get_event_loop().time()
        )

        with patch.object(self.agent, 'parse_requirements') as mock_parse:
            mock_parse.return_value = RequirementsParsed(
                intent="test", context="test", domain="test",
                complexity=ComplexityLevel.SIMPLE, key_requirements=[],
                constraints=[], target_audience="", expected_output="",
                prompt_type=PromptType.GENERAL, confidence_score=0.8
            )

            result = await self.agent.process_task(task)

        assert result["status"] == "completed"
        assert "data" in result
        mock_parse.assert_called_once_with(sample_user_inputs["simple_creative"])

    async def test_process_task_invalid_task_type(self):
        """测试处理无效任务类型"""
        task = TaskMessage(
            task_id="test_task_invalid",
            agent_id=self.agent.agent_id,
            task_type="invalid_task_type",
            data={"invalid": "data"},
            priority=1,
            created_at=asyncio.get_event_loop().time()
        )

        result = await self.agent.process_task(task)
        assert result["status"] == "failed"
        assert "不支持的任务类型" in result["error"]

    async def test_concurrent_task_processing(self, sample_user_inputs):
        """测试并发任务处理"""
        tasks = []
        for i in range(3):
            task = TaskMessage(
                task_id=f"concurrent_task_{i}",
                agent_id=self.agent.agent_id,
                task_type="parse_requirements",
                data=PETaskData(
                    task_type=PETaskType.PARSE_REQUIREMENTS,
                    user_input=sample_user_inputs["simple_creative"]
                ),
                priority=1,
                created_at=asyncio.get_event_loop().time()
            )
            tasks.append(task)

        with patch.object(self.agent, 'parse_requirements') as mock_parse:
            mock_parse.return_value = RequirementsParsed(
                intent="test", context="test", domain="test",
                complexity=ComplexityLevel.SIMPLE, key_requirements=[],
                constraints=[], target_audience="", expected_output="",
                prompt_type=PromptType.GENERAL, confidence_score=0.8
            )

            # 并发执行任务
            results = await asyncio.gather(*[self.agent.process_task(task) for task in tasks])

        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"

    def test_confidence_score_calculation(self):
        """测试置信度分数计算"""
        parsed_data = {
            "intent": "创建写作助手",
            "key_requirements": ["创意", "结构", "角色"],
            "domain": "creative_writing"
        }
        user_input = "我想要一个帮助我写创意小说的提示词"

        score = self.agent._calculate_confidence_score(parsed_data, user_input)

        assert 0 <= score <= 1
        assert isinstance(score, float)

    def test_fallback_form_creation(self, sample_parsed_requirements):
        """测试回退表单创建"""
        fallback_form = self.agent._create_fallback_form(sample_parsed_requirements)

        assert isinstance(fallback_form, DynamicForm)
        assert len(fallback_form.sections) > 0
        assert fallback_form.title is not None

    def test_fallback_prompt_creation(self, sample_form_data):
        """测试回退提示词创建"""
        fallback_prompt = self.agent._create_fallback_prompt(sample_form_data)

        assert isinstance(fallback_prompt, OptimizedPrompt)
        assert len(fallback_prompt.optimized_prompt) > 0
        assert fallback_prompt.confidence_score < 0.7  # 回退结果置信度较低

    async def test_template_management(self):
        """测试模板管理功能"""
        # 测试获取所有模板
        templates = await self.agent._get_templates()
        assert isinstance(templates, list)

        # 测试按类型获取模板
        creative_templates = await self.agent._get_templates("creative")
        assert isinstance(creative_templates, list)

    def test_form_validation(self):
        """测试表单验证"""
        # 测试有效表单sections
        valid_sections = [
            {
                "title": "基础设置",
                "fields": [{"name": "field1", "type": "text", "required": True}]
            }
        ]
        validated = self.agent._validate_form_sections(valid_sections)
        assert len(validated) == 1

        # 测试无效表单sections
        invalid_sections = [
            {"title": "", "fields": []}  # 空标题和字段
        ]
        validated = self.agent._validate_form_sections(invalid_sections)
        assert len(validated) == 0

    async def test_error_handling_api_timeout(self, sample_user_inputs):
        """测试API超时错误处理"""
        with patch.object(self.agent, '_call_dashscope_api', side_effect=asyncio.TimeoutError()):
            result = await self.agent.parse_requirements(sample_user_inputs["simple_creative"])

        # 应该返回回退结果而不是抛出异常
        assert isinstance(result, RequirementsParsed)
        assert result.confidence_score < 0.5

    async def test_error_handling_json_parse_error(self, sample_user_inputs):
        """测试JSON解析错误处理"""
        with patch.object(self.agent, '_call_dashscope_api', return_value="invalid json response"):
            result = await self.agent.parse_requirements(sample_user_inputs["simple_creative"])

        # 应该返回回退结果
        assert isinstance(result, RequirementsParsed)
        assert result.confidence_score < 0.5

    def test_statistics_tracking(self):
        """测试统计信息跟踪"""
        stats = self.agent.get_stats()

        assert isinstance(stats, dict)
        expected_keys = ["total_tasks", "successful_tasks", "failed_tasks", "average_processing_time"]
        for key in expected_keys:
            assert key in stats

    async def test_memory_usage_large_inputs(self):
        """测试大输入的内存使用"""
        large_input = "详细需求描述 " * 1000  # 创建大输入

        # 监控内存使用情况
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        with patch.object(self.agent, '_call_dashscope_api', return_value='{"intent": "test"}'):
            result = await self.agent.parse_requirements(large_input)

        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before

        # 确保内存增长在合理范围内 (小于100MB)
        assert memory_increase < 100 * 1024 * 1024
        assert isinstance(result, RequirementsParsed)

    async def test_rate_limiting_handling(self, sample_user_inputs):
        """测试速率限制处理"""
        from app.dashscope.exceptions import RateLimitError

        with patch.object(self.agent, '_call_dashscope_api', side_effect=RateLimitError("请求频率过高")):
            result = await self.agent.parse_requirements(sample_user_inputs["simple_creative"])

        # 应该有适当的错误处理
        assert isinstance(result, RequirementsParsed)
        assert result.confidence_score < 0.5