"""
PE Engineer Agent 配置模块

定义 Prompt Engineering 工程师 Agent 的配置参数，包括模型设置、
处理参数、默认值等配置信息。
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .types import PromptType, ComplexityLevel, FormFieldType


class DashScopeConfig(BaseModel):
    """DashScope API 配置"""
    model_name: str = "qwen-max"                    # 默认模型
    api_key: Optional[str] = None                   # API密钥 (从环境变量获取)
    max_tokens: int = 2000                          # 最大token数
    temperature: float = 0.7                        # 温度参数
    top_p: float = 0.9                             # Top-p采样
    timeout_seconds: int = 30                       # 请求超时
    retry_attempts: int = 3                         # 重试次数
    retry_delay: float = 1.0                        # 重试延迟


class ProcessingConfig(BaseModel):
    """处理配置"""
    max_concurrent_tasks: int = 5                   # 最大并发任务数
    task_timeout_seconds: int = 120                 # 任务超时
    cache_ttl_seconds: int = 3600                   # 缓存TTL
    enable_caching: bool = True                     # 启用缓存
    max_prompt_length: int = 8000                   # 最大prompt长度
    min_confidence_threshold: float = 0.6           # 最小置信度阈值


class RequirementsParsingConfig(BaseModel):
    """需求解析配置"""
    system_prompt: str = """你是一个专业的需求分析师，擅长从用户的自然语言描述中提取关键信息。
你需要分析用户的输入，识别以下信息：
1. 用户意图和目标
2. 领域或行业背景
3. 提示词类型（通用、创意、分析等）
4. 复杂度级别
5. 关键需求和约束条件
6. 期望的输出格式
7. 目标受众

请以JSON格式返回分析结果，确保提取的信息准确且有用。"""

    max_key_requirements: int = 10                  # 最大关键需求数
    max_constraints: int = 8                        # 最大约束数
    max_examples: int = 5                           # 最大示例数
    confidence_weights: Dict[str, float] = Field(default_factory=lambda: {
        "intent_clarity": 0.25,                     # 意图清晰度权重
        "domain_specificity": 0.15,                 # 领域特异性权重
        "requirement_completeness": 0.30,           # 需求完整性权重
        "constraint_clarity": 0.20,                 # 约束清晰度权重
        "example_relevance": 0.10                   # 示例相关性权重
    })


class FormGenerationConfig(BaseModel):
    """表单生成配置"""
    system_prompt: str = """你是一个专业的表单设计师，根据用户需求生成最适合的动态表单。
你需要考虑以下因素：
1. 用户的技术水平和背景
2. 任务的复杂度
3. 信息收集的完整性
4. 用户体验的友好性
5. 表单的逻辑结构

请设计合理的字段类型、验证规则和条件逻辑。"""

    max_fields_per_section: int = 8                 # 每个段落最大字段数
    max_sections: int = 6                           # 最大段落数
    default_field_types: Dict[str, FormFieldType] = Field(default_factory=lambda: {
        "text_input": FormFieldType.TEXT,
        "long_text": FormFieldType.TEXTAREA,
        "choice": FormFieldType.SELECT,
        "multiple_choice": FormFieldType.MULTISELECT,
        "yes_no": FormFieldType.RADIO,
        "number": FormFieldType.NUMBER
    })


class PromptCreationConfig(BaseModel):
    """提示词创建配置"""
    system_prompt: str = """你是一个专业的Prompt工程师，擅长创建高质量的AI提示词。
你需要根据用户填写的表单数据，创建清晰、有效、结构化的提示词。

遵循以下原则：
1. 清晰性：指令明确易懂
2. 具体性：提供具体的要求和约束
3. 结构性：逻辑清晰，层次分明
4. 完整性：包含所有必要信息
5. 可操作性：AI能够准确执行

生成的提示词应该包括角色设定、任务描述、输出要求等关键部分。"""

    include_role_definition: bool = True            # 包含角色定义
    include_context_section: bool = True            # 包含上下文部分
    include_constraints: bool = True                # 包含约束条件
    include_examples: bool = True                   # 包含示例
    include_output_format: bool = True              # 包含输出格式
    max_prompt_sections: int = 8                    # 最大提示词段落数


class OptimizationConfig(BaseModel):
    """优化配置"""
    system_prompt: str = """你是一个Prompt优化专家，擅长改进和优化AI提示词的质量。
你需要分析现有提示词，识别改进机会，并提供具体的优化建议。

关注以下优化方面：
1. 清晰度：消除歧义，提高理解性
2. 精确性：增强指令的准确性
3. 完整性：补充遗漏的重要信息
4. 效率性：减少冗余，提高执行效率
5. 鲁棒性：增强错误处理能力

提供具体的优化建议和改进后的版本。"""

    max_optimization_rounds: int = 3                # 最大优化轮数
    optimization_techniques: List[str] = Field(default_factory=lambda: [
        "clarity_improvement",
        "specificity_enhancement",
        "context_enrichment",
        "instruction_refinement",
        "example_addition",
        "constraint_clarification",
        "format_specification",
        "error_prevention"
    ])

    quality_weights: Dict[str, float] = Field(default_factory=lambda: {
        "clarity": 0.30,                           # 清晰度权重
        "completeness": 0.25,                      # 完整性权重
        "specificity": 0.20,                       # 具体性权重
        "structure": 0.15,                         # 结构性权重
        "effectiveness": 0.10                      # 有效性权重
    })


class TemplateConfig(BaseModel):
    """模板配置"""
    template_library_path: str = "templates/prompt_templates.json"  # 模板库路径
    max_templates_per_type: int = 20                # 每种类型最大模板数
    default_templates: Dict[PromptType, str] = Field(default_factory=lambda: {
        PromptType.GENERAL: """# 任务描述
请作为一个{role}，帮我{task}。

# 具体要求
{requirements}

# 输出格式
{output_format}

# 注意事项
{constraints}""",

        PromptType.CREATIVE: """# 创意任务
你是一个富有创意的{role}，请发挥你的想象力来{task}。

# 创意要求
{requirements}

# 风格指导
{style_guide}

# 输出要求
{output_format}""",

        PromptType.ANALYTICAL: """# 分析任务
作为专业的{role}，请对以下内容进行深入分析：

# 分析对象
{target}

# 分析维度
{dimensions}

# 分析要求
{requirements}

# 输出结构
{output_structure}""",

        PromptType.CONVERSATIONAL: """# 对话设定
你是一个{role}，正在与用户进行对话。

# 对话背景
{context}

# 对话目标
{objectives}

# 对话风格
{style}

# 注意事项
{guidelines}""",

        PromptType.CODE_GENERATION: """# 代码生成任务
作为专业的{role}，请根据要求生成代码。

# 技术要求
- 编程语言: {language}
- 技术栈: {tech_stack}
- 功能需求: {requirements}

# 代码规范
{coding_standards}

# 输出要求
{output_requirements}"""
    })


class PEEngineerConfig(BaseModel):
    """PE Engineer Agent 主配置"""
    agent_id: str = "pe_engineer_001"               # Agent ID
    agent_name: str = "PE Engineer"                 # Agent名称
    version: str = "1.0.0"                          # 版本号

    # 子配置
    dashscope: DashScopeConfig = Field(default_factory=DashScopeConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    requirements_parsing: RequirementsParsingConfig = Field(default_factory=RequirementsParsingConfig)
    form_generation: FormGenerationConfig = Field(default_factory=FormGenerationConfig)
    prompt_creation: PromptCreationConfig = Field(default_factory=PromptCreationConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    template: TemplateConfig = Field(default_factory=TemplateConfig)

    # 能力定义
    capabilities: List[str] = Field(default_factory=lambda: [
        "requirements_parsing",                     # 需求解析
        "dynamic_form_generation",                  # 动态表单生成
        "prompt_creation",                          # 提示词创建
        "prompt_optimization",                      # 提示词优化
        "template_management",                      # 模板管理
        "quality_assessment"                        # 质量评估
    ])

    # 性能监控
    enable_metrics: bool = True                     # 启用性能指标
    log_level: str = "INFO"                         # 日志级别

    # 缓存配置
    cache_config: Dict[str, Any] = Field(default_factory=lambda: {
        "requirements_cache_ttl": 1800,             # 需求解析缓存TTL (30分钟)
        "template_cache_ttl": 3600,                 # 模板缓存TTL (1小时)
        "form_cache_ttl": 7200,                     # 表单缓存TTL (2小时)
        "optimization_cache_ttl": 900               # 优化缓存TTL (15分钟)
    })


# 默认配置实例
DEFAULT_CONFIG = PEEngineerConfig()


def get_config() -> PEEngineerConfig:
    """获取配置实例"""
    return DEFAULT_CONFIG


def update_config(**kwargs) -> PEEngineerConfig:
    """更新配置参数"""
    config_dict = DEFAULT_CONFIG.dict()
    config_dict.update(kwargs)
    return PEEngineerConfig(**config_dict)