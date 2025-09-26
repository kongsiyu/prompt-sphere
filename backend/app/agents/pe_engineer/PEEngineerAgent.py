"""
PE Engineer Agent 实现

Prompt Engineering 工程师 Agent，负责需求解析、动态表单生成、
提示词创建和优化等核心功能。继承自 BaseAgent 提供完整的 Agent 能力。
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from ..base.base_agent import BaseAgent
from ..base.message_types import TaskMessage, AgentMessage

from .types import (
    RequirementsParsed, DynamicForm, OptimizedPrompt, PromptTemplate,
    PETaskType, PETaskData, PEResponse,
    PromptType, ComplexityLevel, FormFieldType, FormField, FormSection,
    COMMON_FORM_FIELDS, OPTIMIZATION_TECHNIQUES
)
from .config import PEEngineerConfig, get_config

logger = logging.getLogger(__name__)


class PEEngineerAgent(BaseAgent):
    """
    Prompt Engineering 工程师 Agent

    提供以下核心能力：
    1. 自然语言需求解析
    2. 动态表单生成
    3. 提示词创建
    4. 提示词优化
    5. 模板管理
    """

    def __init__(self, config: Optional[PEEngineerConfig] = None):
        self.config = config or get_config()

        super().__init__(
            agent_id=self.config.agent_id,
            agent_type="PE_ENGINEER",
            max_concurrent_tasks=self.config.processing.max_concurrent_tasks,
            heartbeat_interval=30,
            max_queue_size=100
        )

        # 模板缓存
        self._template_cache: Dict[str, PromptTemplate] = {}
        self._template_cache_expire: Optional[datetime] = None

        # 统计信息
        self._parse_count = 0
        self._form_generation_count = 0
        self._prompt_creation_count = 0
        self._optimization_count = 0

        logger.info(f"PE Engineer Agent initialized with ID: {self.agent_id}")

    async def get_capabilities(self) -> List[str]:
        """获取 Agent 能力列表"""
        return self.config.capabilities.copy()

    async def process_task(self, task: TaskMessage) -> Dict[str, Any]:
        """处理具体任务"""
        try:
            # 验证任务数据
            if not isinstance(task.task_data, dict):
                raise ValueError("task_data must be a dictionary")

            pe_task_data = PETaskData(**task.task_data)

            # 根据任务类型分发处理
            if pe_task_data.task_type == PETaskType.PARSE_REQUIREMENTS:
                result = await self._handle_parse_requirements(pe_task_data)
            elif pe_task_data.task_type == PETaskType.GENERATE_FORM:
                result = await self._handle_generate_form(pe_task_data)
            elif pe_task_data.task_type == PETaskType.CREATE_PROMPT:
                result = await self._handle_create_prompt(pe_task_data)
            elif pe_task_data.task_type == PETaskType.OPTIMIZE_PROMPT:
                result = await self._handle_optimize_prompt(pe_task_data)
            elif pe_task_data.task_type == PETaskType.GET_TEMPLATES:
                result = await self._handle_get_templates(pe_task_data)
            else:
                raise ValueError(f"Unsupported task type: {pe_task_data.task_type}")

            return result.dict()

        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            return PEResponse(
                success=False,
                error_message=str(e)
            ).dict()

    async def parse_requirements(self, user_input: str) -> RequirementsParsed:
        """解析用户需求"""
        logger.info(f"Parsing requirements for input length: {len(user_input)}")

        try:
            # 构建解析提示词
            parse_prompt = self._build_requirements_parse_prompt(user_input)

            # 调用 DashScope API 进行解析
            response = await self._call_dashscope_api(
                prompt=parse_prompt,
                system_prompt=self.config.requirements_parsing.system_prompt
            )

            # 解析响应
            parsed_data = self._parse_requirements_response(response)

            # 计算置信度
            confidence_score = self._calculate_confidence_score(parsed_data, user_input)
            parsed_data['confidence_score'] = confidence_score

            requirements = RequirementsParsed(**parsed_data)

            self._parse_count += 1
            logger.info(f"Requirements parsed successfully with confidence: {confidence_score:.2f}")

            return requirements

        except Exception as e:
            logger.error(f"Error parsing requirements: {e}")
            # 返回基础解析结果
            return RequirementsParsed(
                intent="用户需求解析失败",
                key_requirements=[user_input],
                confidence_score=0.1
            )

    async def generate_form(self, requirements: RequirementsParsed) -> DynamicForm:
        """根据需求生成动态表单"""
        logger.info(f"Generating form for requirements: {requirements.intent}")

        try:
            # 构建表单生成提示词
            form_prompt = self._build_form_generation_prompt(requirements)

            # 调用 DashScope API 生成表单结构
            response = await self._call_dashscope_api(
                prompt=form_prompt,
                system_prompt=self.config.form_generation.system_prompt
            )

            # 解析表单结构
            form_data = self._parse_form_response(response, requirements)

            # 创建动态表单
            form = DynamicForm(**form_data)

            self._form_generation_count += 1
            logger.info(f"Dynamic form generated with {len(form.sections)} sections")

            return form

        except Exception as e:
            logger.error(f"Error generating form: {e}")
            # 返回基础表单
            return self._create_fallback_form(requirements)

    async def create_prompt(self, form_data: dict) -> OptimizedPrompt:
        """根据表单数据创建提示词"""
        logger.info("Creating prompt from form data")

        try:
            # 构建提示词创建提示词
            creation_prompt = self._build_prompt_creation_prompt(form_data)

            # 调用 DashScope API 创建提示词
            response = await self._call_dashscope_api(
                prompt=creation_prompt,
                system_prompt=self.config.prompt_creation.system_prompt
            )

            # 解析创建结果
            prompt_data = self._parse_prompt_creation_response(response, form_data)

            # 评估提示词质量
            quality_scores = await self._evaluate_prompt_quality(prompt_data['optimized_prompt'])
            prompt_data.update(quality_scores)

            optimized_prompt = OptimizedPrompt(**prompt_data)

            self._prompt_creation_count += 1
            logger.info(f"Prompt created with quality score: {optimized_prompt.quality_score:.2f}")

            return optimized_prompt

        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            # 返回基础提示词
            return self._create_fallback_prompt(form_data)

    async def optimize_prompt(self, prompt: str) -> OptimizedPrompt:
        """优化现有提示词"""
        logger.info(f"Optimizing prompt length: {len(prompt)}")

        try:
            # 构建优化提示词
            optimization_prompt = self._build_optimization_prompt(prompt)

            # 调用 DashScope API 进行优化
            response = await self._call_dashscope_api(
                prompt=optimization_prompt,
                system_prompt=self.config.optimization.system_prompt
            )

            # 解析优化结果
            optimization_data = self._parse_optimization_response(response, prompt)

            # 评估优化效果
            quality_scores = await self._evaluate_prompt_quality(optimization_data['optimized_prompt'])
            optimization_data.update(quality_scores)

            optimized_prompt = OptimizedPrompt(**optimization_data)

            self._optimization_count += 1
            logger.info(f"Prompt optimized, improvement: {optimized_prompt.quality_score:.2f}")

            return optimized_prompt

        except Exception as e:
            logger.error(f"Error optimizing prompt: {e}")
            # 返回原始提示词作为结果
            return OptimizedPrompt(
                original_prompt=prompt,
                optimized_prompt=prompt,
                optimization_applied=[],
                quality_score=0.5,
                readability_score=0.5,
                effectiveness_score=0.5,
                improvement_summary="优化过程中出现错误，返回原始提示词"
            )

    # 私有方法 - 任务处理器

    async def _handle_parse_requirements(self, task_data: PETaskData) -> PEResponse:
        """处理需求解析任务"""
        user_input = task_data.input_data.get('user_input')
        if not user_input:
            return PEResponse(
                success=False,
                error_message="Missing required field: user_input"
            )

        requirements = await self.parse_requirements(user_input)

        return PEResponse(
            success=True,
            data=requirements.dict(),
            metadata={
                "task_type": "parse_requirements",
                "confidence_score": requirements.confidence_score
            }
        )

    async def _handle_generate_form(self, task_data: PETaskData) -> PEResponse:
        """处理表单生成任务"""
        requirements_data = task_data.input_data.get('requirements')
        if not requirements_data:
            return PEResponse(
                success=False,
                error_message="Missing required field: requirements"
            )

        requirements = RequirementsParsed(**requirements_data)
        form = await self.generate_form(requirements)

        return PEResponse(
            success=True,
            data=form.dict(),
            metadata={
                "task_type": "generate_form",
                "sections_count": len(form.sections),
                "complexity": form.complexity
            }
        )

    async def _handle_create_prompt(self, task_data: PETaskData) -> PEResponse:
        """处理提示词创建任务"""
        form_data = task_data.input_data.get('form_data')
        if not form_data:
            return PEResponse(
                success=False,
                error_message="Missing required field: form_data"
            )

        prompt = await self.create_prompt(form_data)

        return PEResponse(
            success=True,
            data=prompt.dict(),
            metadata={
                "task_type": "create_prompt",
                "quality_score": prompt.quality_score,
                "optimizations_applied": len(prompt.optimization_applied)
            }
        )

    async def _handle_optimize_prompt(self, task_data: PETaskData) -> PEResponse:
        """处理提示词优化任务"""
        prompt = task_data.input_data.get('prompt')
        if not prompt:
            return PEResponse(
                success=False,
                error_message="Missing required field: prompt"
            )

        optimized = await self.optimize_prompt(prompt)

        return PEResponse(
            success=True,
            data=optimized.dict(),
            metadata={
                "task_type": "optimize_prompt",
                "quality_improvement": optimized.quality_score,
                "suggestions_count": len(optimized.suggestions)
            }
        )

    async def _handle_get_templates(self, task_data: PETaskData) -> PEResponse:
        """处理获取模板任务"""
        prompt_type = task_data.input_data.get('prompt_type')

        templates = await self._get_templates(prompt_type)

        return PEResponse(
            success=True,
            data={"templates": [t.dict() for t in templates]},
            metadata={
                "task_type": "get_templates",
                "templates_count": len(templates)
            }
        )

    # 私有方法 - 核心逻辑实现

    def _build_requirements_parse_prompt(self, user_input: str) -> str:
        """构建需求解析提示词"""
        return f"""请分析以下用户输入，提取关键信息：

用户输入：
{user_input}

请以JSON格式返回分析结果，包含以下字段：
- intent: 用户意图
- domain: 领域或行业（可选）
- prompt_type: 提示词类型（general/creative/analytical/conversational/task_specific/code_generation/translation/summarization）
- complexity: 复杂度级别（simple/medium/complex/advanced）
- key_requirements: 关键需求列表
- context_info: 上下文信息对象
- target_audience: 目标受众（可选）
- expected_output: 期望输出格式（可选）
- constraints: 限制条件列表
- examples: 示例列表（如果有的话）

请确保JSON格式正确，字段完整。"""

    def _build_form_generation_prompt(self, requirements: RequirementsParsed) -> str:
        """构建表单生成提示词"""
        return f"""根据以下需求分析结果，设计一个动态表单：

需求分析：
- 用户意图：{requirements.intent}
- 领域：{requirements.domain or '未指定'}
- 提示词类型：{requirements.prompt_type}
- 复杂度：{requirements.complexity}
- 关键需求：{', '.join(requirements.key_requirements)}
- 目标受众：{requirements.target_audience or '未指定'}
- 期望输出：{requirements.expected_output or '未指定'}
- 约束条件：{', '.join(requirements.constraints)}

请设计合适的表单字段，以JSON格式返回表单结构，包含：
- form_id: 表单ID
- title: 表单标题
- description: 表单说明
- sections: 表单段落列表
- complexity: 表单复杂度

每个段落包含：
- title: 段落标题
- fields: 字段列表

每个字段包含：
- name: 字段名
- label: 显示标签
- field_type: 字段类型（text/textarea/select/multiselect/radio/checkbox/number/slider/date/file）
- description: 字段说明
- required: 是否必填
- default_value: 默认值（可选）
- options: 选项列表（选择类字段）

请确保表单逻辑合理，字段类型适当。"""

    def _build_prompt_creation_prompt(self, form_data: dict) -> str:
        """构建提示词创建提示词"""
        form_summary = self._summarize_form_data(form_data)

        return f"""根据用户填写的表单数据创建高质量的AI提示词：

表单数据摘要：
{form_summary}

请创建一个结构化的提示词，包含：
1. 角色设定（如果适用）
2. 任务描述
3. 具体要求
4. 输出格式
5. 约束条件（如果有）
6. 示例（如果需要）

返回JSON格式，包含：
- optimized_prompt: 生成的提示词
- optimization_applied: 应用的优化技术列表
- improvement_summary: 改进摘要

请确保提示词清晰、完整、可执行。"""

    def _build_optimization_prompt(self, prompt: str) -> str:
        """构建优化提示词"""
        return f"""请优化以下AI提示词，提高其清晰度、有效性和完整性：

原始提示词：
{prompt}

请从以下方面进行优化：
1. 清晰度：消除歧义，提高理解性
2. 完整性：补充遗漏的重要信息
3. 具体性：增强指令的准确性
4. 结构性：改进逻辑结构
5. 有效性：提高执行效果

返回JSON格式，包含：
- optimized_prompt: 优化后的提示词
- optimization_applied: 应用的优化技术列表
- suggestions: 优化建议列表
- improvement_summary: 改进摘要

每个建议包含：
- type: 建议类型
- title: 建议标题
- description: 详细描述
- impact: 影响程度（low/medium/high）
- difficulty: 实施难度（easy/medium/hard）

请提供具体的优化建议和改进理由。"""

    def _parse_requirements_response(self, response: str) -> dict:
        """解析需求分析响应"""
        try:
            # 尝试解析JSON响应
            parsed = json.loads(response)

            # 验证必需字段
            required_fields = ['intent', 'prompt_type', 'complexity']
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = self._get_default_value(field)

            # 确保列表字段是列表
            list_fields = ['key_requirements', 'constraints', 'examples']
            for field in list_fields:
                if field not in parsed:
                    parsed[field] = []
                elif not isinstance(parsed[field], list):
                    parsed[field] = [str(parsed[field])]

            # 确保对象字段是字典
            if 'context_info' not in parsed:
                parsed['context_info'] = {}
            elif not isinstance(parsed['context_info'], dict):
                parsed['context_info'] = {}

            return parsed

        except json.JSONDecodeError:
            # JSON解析失败，返回基础结构
            logger.warning("Failed to parse JSON response, using fallback")
            return {
                'intent': response[:100] if response else "解析失败",
                'prompt_type': PromptType.GENERAL,
                'complexity': ComplexityLevel.SIMPLE,
                'key_requirements': [response] if response else [],
                'context_info': {},
                'constraints': [],
                'examples': []
            }

    def _parse_form_response(self, response: str, requirements: RequirementsParsed) -> dict:
        """解析表单生成响应"""
        try:
            parsed = json.loads(response)

            # 确保必需字段存在
            if 'form_id' not in parsed:
                parsed['form_id'] = str(uuid4())
            if 'title' not in parsed:
                parsed['title'] = f"{requirements.intent} - 信息收集表单"
            if 'sections' not in parsed:
                parsed['sections'] = []
            if 'complexity' not in parsed:
                parsed['complexity'] = requirements.complexity

            # 验证和修正sections结构
            parsed['sections'] = self._validate_form_sections(parsed['sections'])

            return parsed

        except json.JSONDecodeError:
            # JSON解析失败，返回基础表单
            return self._create_fallback_form(requirements).dict()

    def _parse_prompt_creation_response(self, response: str, form_data: dict) -> dict:
        """解析提示词创建响应"""
        try:
            parsed = json.loads(response)

            if 'optimized_prompt' not in parsed:
                parsed['optimized_prompt'] = response
            if 'optimization_applied' not in parsed:
                parsed['optimization_applied'] = []
            if 'improvement_summary' not in parsed:
                parsed['improvement_summary'] = "基于表单数据创建的提示词"

            # 设置原始提示词为空（这是创建任务，不是优化任务）
            parsed['original_prompt'] = ""

            return parsed

        except json.JSONDecodeError:
            return {
                'original_prompt': "",
                'optimized_prompt': response or "提示词创建失败",
                'optimization_applied': [],
                'improvement_summary': "提示词创建过程中出现解析错误"
            }

    def _parse_optimization_response(self, response: str, original_prompt: str) -> dict:
        """解析优化响应"""
        try:
            parsed = json.loads(response)

            if 'optimized_prompt' not in parsed:
                parsed['optimized_prompt'] = response
            if 'optimization_applied' not in parsed:
                parsed['optimization_applied'] = []
            if 'suggestions' not in parsed:
                parsed['suggestions'] = []
            if 'improvement_summary' not in parsed:
                parsed['improvement_summary'] = "提示词优化完成"

            parsed['original_prompt'] = original_prompt

            return parsed

        except json.JSONDecodeError:
            return {
                'original_prompt': original_prompt,
                'optimized_prompt': response or original_prompt,
                'optimization_applied': [],
                'suggestions': [],
                'improvement_summary': "优化过程中出现解析错误"
            }

    def _calculate_confidence_score(self, parsed_data: dict, user_input: str) -> float:
        """计算置信度评分"""
        weights = self.config.requirements_parsing.confidence_weights
        scores = {}

        # 意图清晰度 - 基于意图描述的完整性
        intent = parsed_data.get('intent', '')
        scores['intent_clarity'] = min(len(intent) / 50, 1.0) if intent else 0.0

        # 领域特异性 - 是否识别出特定领域
        domain = parsed_data.get('domain')
        scores['domain_specificity'] = 1.0 if domain and domain != '未指定' else 0.3

        # 需求完整性 - 基于提取的需求数量
        requirements = parsed_data.get('key_requirements', [])
        scores['requirement_completeness'] = min(len(requirements) / 5, 1.0)

        # 约束清晰度 - 基于约束条件
        constraints = parsed_data.get('constraints', [])
        scores['constraint_clarity'] = min(len(constraints) / 3, 1.0) if constraints else 0.5

        # 示例相关性 - 基于示例数量
        examples = parsed_data.get('examples', [])
        scores['example_relevance'] = min(len(examples) / 2, 1.0) if examples else 0.5

        # 加权平均
        weighted_score = sum(scores[key] * weights[key] for key in weights.keys())

        return round(weighted_score, 2)

    async def _evaluate_prompt_quality(self, prompt: str) -> dict:
        """评估提示词质量"""
        # 这里可以实现更复杂的质量评估逻辑
        # 目前提供基础评估

        # 长度评分
        length = len(prompt)
        length_score = min(length / 500, 1.0) if length > 0 else 0.0

        # 结构评分 - 基于段落和格式
        structure_indicators = ['#', '-', '1.', '2.', '：', '要求', '格式', '注意']
        structure_count = sum(1 for indicator in structure_indicators if indicator in prompt)
        structure_score = min(structure_count / len(structure_indicators), 1.0)

        # 清晰度评分 - 基于关键词
        clarity_keywords = ['请', '需要', '要求', '输出', '格式', '例如', '注意', '限制']
        clarity_count = sum(1 for keyword in clarity_keywords if keyword in prompt)
        clarity_score = min(clarity_count / len(clarity_keywords), 1.0)

        # 综合评分
        quality_score = (length_score * 0.3 + structure_score * 0.4 + clarity_score * 0.3)

        return {
            'quality_score': round(quality_score, 2),
            'readability_score': round(clarity_score, 2),
            'effectiveness_score': round((structure_score + quality_score) / 2, 2)
        }

    def _create_fallback_form(self, requirements: RequirementsParsed) -> DynamicForm:
        """创建备用表单"""
        sections = [
            FormSection(
                title="基本信息",
                description="请提供基本的任务信息",
                fields=[
                    COMMON_FORM_FIELDS["target_audience"],
                    COMMON_FORM_FIELDS["output_format"],
                    COMMON_FORM_FIELDS["tone"],
                    COMMON_FORM_FIELDS["length"]
                ]
            )
        ]

        return DynamicForm(
            form_id=str(uuid4()),
            title=f"{requirements.intent} - 信息收集",
            description="请填写以下信息以帮助生成更精确的提示词",
            sections=sections,
            complexity=requirements.complexity,
            estimated_time=5
        )

    def _create_fallback_prompt(self, form_data: dict) -> OptimizedPrompt:
        """创建备用提示词"""
        summary = self._summarize_form_data(form_data)

        basic_prompt = f"""请根据以下要求完成任务：

{summary}

请提供清晰、准确的回答。"""

        return OptimizedPrompt(
            original_prompt="",
            optimized_prompt=basic_prompt,
            optimization_applied=["basic_structure"],
            quality_score=0.6,
            readability_score=0.7,
            effectiveness_score=0.5,
            improvement_summary="生成了基础结构的提示词"
        )

    def _summarize_form_data(self, form_data: dict) -> str:
        """总结表单数据"""
        summary_parts = []

        for key, value in form_data.items():
            if value and str(value).strip():
                summary_parts.append(f"- {key}: {value}")

        return "\n".join(summary_parts) if summary_parts else "没有提供具体信息"

    def _validate_form_sections(self, sections: list) -> list:
        """验证和修正表单sections"""
        validated_sections = []

        for section_data in sections:
            if isinstance(section_data, dict):
                # 确保必需字段存在
                if 'title' not in section_data:
                    section_data['title'] = "信息收集"
                if 'fields' not in section_data:
                    section_data['fields'] = []

                # 验证字段
                validated_fields = []
                for field_data in section_data['fields']:
                    if isinstance(field_data, dict) and all(
                        key in field_data for key in ['name', 'label', 'field_type']
                    ):
                        validated_fields.append(field_data)

                section_data['fields'] = validated_fields
                if validated_fields:  # 只添加有字段的sections
                    validated_sections.append(section_data)

        return validated_sections

    def _get_default_value(self, field: str) -> str:
        """获取字段默认值"""
        defaults = {
            'intent': '通用任务',
            'prompt_type': PromptType.GENERAL,
            'complexity': ComplexityLevel.SIMPLE
        }
        return defaults.get(field, '')

    async def _get_templates(self, prompt_type: Optional[str] = None) -> List[PromptTemplate]:
        """获取提示词模板"""
        # 检查缓存
        if self._template_cache and (
            not self._template_cache_expire or
            datetime.now(timezone.utc) < self._template_cache_expire
        ):
            templates = list(self._template_cache.values())
        else:
            # 重新加载模板 (这里应该从文件或数据库加载)
            templates = self._load_default_templates()

            # 更新缓存
            self._template_cache = {t.template_id: t for t in templates}
            self._template_cache_expire = datetime.now(timezone.utc) + timedelta(
                seconds=self.config.cache_config['template_cache_ttl']
            )

        # 按类型过滤
        if prompt_type:
            templates = [t for t in templates if t.prompt_type == prompt_type]

        # 按评分排序
        templates.sort(key=lambda x: x.rating, reverse=True)

        return templates

    def _load_default_templates(self) -> List[PromptTemplate]:
        """加载默认模板"""
        templates = []

        for prompt_type, template_text in self.config.template.default_templates.items():
            template = PromptTemplate(
                template_id=f"default_{prompt_type.value}",
                name=f"默认{prompt_type.value}模板",
                description=f"适用于{prompt_type.value}类型任务的默认模板",
                prompt_type=prompt_type,
                template_text=template_text,
                variables=['role', 'task', 'requirements', 'output_format'],
                rating=4.0,
                usage_count=0
            )
            templates.append(template)

        return templates

    async def _call_dashscope_api(self, prompt: str, system_prompt: str) -> str:
        """调用DashScope API"""
        # 这里应该调用实际的DashScope API
        # 目前返回模拟响应用于测试

        logger.info("Calling DashScope API (simulated)")

        # 模拟API延迟
        import asyncio
        await asyncio.sleep(0.1)

        # 返回基础响应 - 在实际实现中应该调用真实API
        return f"""{{
    "intent": "根据用户输入创建AI提示词",
    "prompt_type": "general",
    "complexity": "medium",
    "key_requirements": ["清晰的指令", "结构化输出", "准确的回答"],
    "context_info": {{}},
    "constraints": ["保持专业性", "确保准确性"],
    "examples": []
}}"""

    # 统计方法

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "parse_count": self._parse_count,
            "form_generation_count": self._form_generation_count,
            "prompt_creation_count": self._prompt_creation_count,
            "optimization_count": self._optimization_count,
            "template_cache_size": len(self._template_cache),
            "uptime_seconds": self.uptime_seconds,
            "status": self.status.value
        }