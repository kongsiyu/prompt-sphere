"""
PE Engineer Agent 类型定义

定义 Prompt Engineering 工程师 Agent 相关的数据类型和结构，
包括需求解析、表单生成、prompt 优化等核心功能的类型定义。
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class PromptType(str, Enum):
    """提示词类型"""
    GENERAL = "general"                    # 通用型
    CREATIVE = "creative"                  # 创意型
    ANALYTICAL = "analytical"              # 分析型
    CONVERSATIONAL = "conversational"      # 对话型
    TASK_SPECIFIC = "task_specific"        # 任务特定型
    CODE_GENERATION = "code_generation"    # 代码生成型
    TRANSLATION = "translation"            # 翻译型
    SUMMARIZATION = "summarization"        # 摘要型


class FormFieldType(str, Enum):
    """表单字段类型"""
    TEXT = "text"                # 文本输入
    TEXTAREA = "textarea"        # 多行文本
    SELECT = "select"           # 下拉选择
    MULTISELECT = "multiselect" # 多选
    RADIO = "radio"             # 单选
    CHECKBOX = "checkbox"       # 复选框
    NUMBER = "number"           # 数字输入
    SLIDER = "slider"           # 滑块
    DATE = "date"               # 日期
    FILE = "file"               # 文件上传


class ComplexityLevel(str, Enum):
    """复杂度级别"""
    SIMPLE = "simple"           # 简单 (1-2个参数)
    MEDIUM = "medium"           # 中等 (3-5个参数)
    COMPLEX = "complex"         # 复杂 (6-10个参数)
    ADVANCED = "advanced"       # 高级 (10+个参数)


class RequirementsParsed(BaseModel):
    """解析后的需求"""
    intent: str                                    # 用户意图
    domain: Optional[str] = None                   # 领域/行业
    prompt_type: PromptType = PromptType.GENERAL   # 提示词类型
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE  # 复杂度
    key_requirements: List[str] = Field(default_factory=list)  # 关键需求
    context_info: Dict[str, Any] = Field(default_factory=dict) # 上下文信息
    target_audience: Optional[str] = None          # 目标受众
    expected_output: Optional[str] = None          # 期望输出格式
    constraints: List[str] = Field(default_factory=list)      # 限制条件
    examples: List[str] = Field(default_factory=list)         # 示例
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)  # 解析置信度


class FormField(BaseModel):
    """表单字段定义"""
    name: str                                      # 字段名
    label: str                                     # 显示标签
    field_type: FormFieldType                     # 字段类型
    description: Optional[str] = None              # 字段说明
    required: bool = True                          # 是否必填
    default_value: Optional[Union[str, int, float, bool, List[str]]] = None  # 默认值
    placeholder: Optional[str] = None              # 占位符文本
    options: Optional[List[Dict[str, str]]] = None # 选项列表 (for select/radio)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)  # 验证规则
    min_length: Optional[int] = None               # 最小长度
    max_length: Optional[int] = None               # 最大长度
    min_value: Optional[Union[int, float]] = None  # 最小值
    max_value: Optional[Union[int, float]] = None  # 最大值
    pattern: Optional[str] = None                  # 正则表达式模式

    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        field_type = info.data.get('field_type')
        if field_type in [FormFieldType.SELECT, FormFieldType.MULTISELECT, FormFieldType.RADIO]:
            if not v:
                raise ValueError(f"options are required for field_type {field_type}")
        return v


class FormSection(BaseModel):
    """表单段落"""
    title: str                                     # 段落标题
    description: Optional[str] = None              # 段落说明
    fields: List[FormField]                        # 字段列表
    conditional: Optional[Dict[str, Any]] = None   # 条件显示规则


class DynamicForm(BaseModel):
    """动态表单定义"""
    form_id: str                                   # 表单ID
    title: str                                     # 表单标题
    description: Optional[str] = None              # 表单说明
    sections: List[FormSection]                    # 表单段落
    estimated_time: Optional[int] = None           # 预估填写时间(分钟)
    complexity: ComplexityLevel                    # 表单复杂度
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据


class PromptTemplate(BaseModel):
    """提示词模板"""
    template_id: str                               # 模板ID
    name: str                                      # 模板名称
    description: str                               # 模板描述
    prompt_type: PromptType                        # 适用类型
    template_text: str                             # 模板文本
    variables: List[str] = Field(default_factory=list)  # 变量列表
    examples: List[Dict[str, str]] = Field(default_factory=list)  # 使用示例
    tags: List[str] = Field(default_factory=list)  # 标签
    usage_count: int = 0                           # 使用次数
    rating: float = Field(ge=0.0, le=5.0, default=0.0)  # 评分
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    type: str                                      # 建议类型
    title: str                                     # 建议标题
    description: str                               # 详细描述
    impact: str                                    # 影响程度 (low/medium/high)
    difficulty: str                                # 实施难度 (easy/medium/hard)
    before_example: Optional[str] = None           # 优化前示例
    after_example: Optional[str] = None            # 优化后示例


class OptimizedPrompt(BaseModel):
    """优化后的提示词"""
    original_prompt: str                           # 原始提示词
    optimized_prompt: str                          # 优化后提示词
    optimization_applied: List[str] = Field(default_factory=list)  # 应用的优化技术
    suggestions: List[OptimizationSuggestion] = Field(default_factory=list)  # 优化建议
    quality_score: float = Field(ge=0.0, le=1.0)  # 质量评分
    readability_score: float = Field(ge=0.0, le=1.0)  # 可读性评分
    effectiveness_score: float = Field(ge=0.0, le=1.0)  # 有效性预估
    improvement_summary: str                       # 改进摘要
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据


class PETaskType(str, Enum):
    """PE Engineer 任务类型"""
    PARSE_REQUIREMENTS = "parse_requirements"     # 需求解析
    GENERATE_FORM = "generate_form"               # 表单生成
    CREATE_PROMPT = "create_prompt"               # 创建提示词
    OPTIMIZE_PROMPT = "optimize_prompt"           # 优化提示词
    EVALUATE_PROMPT = "evaluate_prompt"           # 评估提示词
    GET_TEMPLATES = "get_templates"               # 获取模板


class PETaskData(BaseModel):
    """PE Engineer 任务数据"""
    task_type: PETaskType                         # 任务类型
    input_data: Dict[str, Any]                    # 输入数据
    parameters: Dict[str, Any] = Field(default_factory=dict)  # 任务参数
    context: Dict[str, Any] = Field(default_factory=dict)     # 上下文信息


class PEResponse(BaseModel):
    """PE Engineer 响应"""
    success: bool                                 # 是否成功
    data: Optional[Dict[str, Any]] = None         # 响应数据
    error_message: Optional[str] = None           # 错误信息
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据
    processing_info: Dict[str, Any] = Field(default_factory=dict)  # 处理信息


# 常用的表单字段模板
COMMON_FORM_FIELDS = {
    "target_audience": FormField(
        name="target_audience",
        label="目标受众",
        field_type=FormFieldType.TEXT,
        description="描述您的目标受众或用户群体",
        placeholder="例如：技术专家、普通用户、学生等"
    ),
    "output_format": FormField(
        name="output_format",
        label="输出格式",
        field_type=FormFieldType.SELECT,
        description="选择期望的输出格式",
        options=[
            {"label": "段落文本", "value": "paragraph"},
            {"label": "项目列表", "value": "list"},
            {"label": "表格形式", "value": "table"},
            {"label": "JSON格式", "value": "json"},
            {"label": "自定义格式", "value": "custom"}
        ]
    ),
    "tone": FormField(
        name="tone",
        label="语调风格",
        field_type=FormFieldType.SELECT,
        description="选择希望的语调风格",
        options=[
            {"label": "专业正式", "value": "professional"},
            {"label": "友好亲切", "value": "friendly"},
            {"label": "严谨学术", "value": "academic"},
            {"label": "轻松随意", "value": "casual"},
            {"label": "创意活泼", "value": "creative"}
        ]
    ),
    "length": FormField(
        name="length",
        label="内容长度",
        field_type=FormFieldType.SELECT,
        description="选择期望的内容长度",
        options=[
            {"label": "简短 (1-2句)", "value": "brief"},
            {"label": "中等 (1-2段)", "value": "medium"},
            {"label": "详细 (多段落)", "value": "detailed"},
            {"label": "全面 (完整分析)", "value": "comprehensive"}
        ]
    )
}


# 提示词优化技术列表
OPTIMIZATION_TECHNIQUES = [
    "clarity_improvement",      # 清晰度改进
    "specificity_enhancement",  # 具体性增强
    "context_enrichment",       # 上下文丰富化
    "instruction_refinement",   # 指令精炼
    "example_addition",         # 示例添加
    "constraint_clarification", # 约束条件澄清
    "format_specification",     # 格式规范化
    "error_prevention",         # 错误预防
    "performance_optimization", # 性能优化
    "accessibility_improvement" # 可访问性改进
]