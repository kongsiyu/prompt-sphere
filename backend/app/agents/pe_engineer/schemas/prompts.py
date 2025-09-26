"""
提示词优化相关的数据模式定义

定义提示词创建、优化、评估和模板管理相关的数据结构，
使用 Pydantic 进行数据验证和序列化。
"""

from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import uuid4

from ..types import PromptType, ComplexityLevel


class OptimizationStrategy(str, Enum):
    """优化策略"""
    STRUCTURE_IMPROVEMENT = "structure_improvement"     # 结构改进
    CLARITY_ENHANCEMENT = "clarity_enhancement"         # 清晰度提升
    CONTEXT_ENRICHMENT = "context_enrichment"           # 上下文丰富
    SPECIFICITY_INCREASE = "specificity_increase"       # 具体性增强
    BIAS_REDUCTION = "bias_reduction"                   # 偏见减少
    INSTRUCTION_REFINEMENT = "instruction_refinement"   # 指令精炼
    EXAMPLE_ADDITION = "example_addition"               # 示例添加
    TEMPLATE_MATCHING = "template_matching"             # 模板匹配


class QualityDimension(str, Enum):
    """质量维度"""
    CLARITY = "clarity"                  # 清晰度
    SPECIFICITY = "specificity"          # 具体性
    COMPLETENESS = "completeness"        # 完整性
    RELEVANCE = "relevance"              # 相关性
    COHERENCE = "coherence"              # 连贯性
    EFFECTIVENESS = "effectiveness"      # 有效性
    CREATIVITY = "creativity"            # 创意性
    SAFETY = "safety"                    # 安全性
    BIAS_FREE = "bias_free"             # 无偏见
    ACTIONABILITY = "actionability"      # 可操作性


class TemplateCategory(str, Enum):
    """模板类别"""
    GENERAL_PURPOSE = "general_purpose"         # 通用
    CREATIVE_WRITING = "creative_writing"       # 创意写作
    TECHNICAL_ANALYSIS = "technical_analysis"   # 技术分析
    BUSINESS_STRATEGY = "business_strategy"     # 商业策略
    EDUCATIONAL = "educational"                 # 教育
    RESEARCH = "research"                       # 研究
    CODING = "coding"                          # 编程
    MARKETING = "marketing"                    # 市场营销
    DATA_ANALYSIS = "data_analysis"            # 数据分析
    ROLE_PLAYING = "role_playing"              # 角色扮演


class OptimizationLevel(str, Enum):
    """优化级别"""
    LIGHT = "light"                     # 轻度优化
    MODERATE = "moderate"               # 中度优化
    HEAVY = "heavy"                     # 重度优化
    COMPLETE_REWRITE = "complete_rewrite"  # 完全重写


class PromptElement(BaseModel):
    """提示词元素"""
    model_config = ConfigDict(use_enum_values=True)

    element_id: str = Field(default_factory=lambda: str(uuid4()))
    element_type: str                    # 元素类型 (instruction, context, example, constraint)
    content: str                         # 元素内容
    importance: float = Field(ge=0.0, le=1.0, default=0.5)  # 重要性
    position: int = 0                    # 位置顺序
    is_required: bool = True             # 是否必需
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QualityScore(BaseModel):
    """质量评分"""
    model_config = ConfigDict(use_enum_values=True)

    dimension: QualityDimension          # 质量维度
    score: float = Field(ge=0.0, le=10.0)  # 评分 (0-10)
    reasoning: Optional[str] = None      # 评分理由
    suggestions: List[str] = Field(default_factory=list)  # 改进建议
    evidence: List[str] = Field(default_factory=list)     # 证据


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    model_config = ConfigDict(use_enum_values=True)

    suggestion_id: str = Field(default_factory=lambda: str(uuid4()))
    strategy: OptimizationStrategy       # 优化策略
    priority: int = Field(ge=1, le=5, default=3)  # 优先级
    description: str                     # 建议描述
    before_text: Optional[str] = None    # 优化前文本
    after_text: Optional[str] = None     # 优化后文本
    impact_score: float = Field(ge=0.0, le=1.0)  # 影响评分
    implementation_effort: str           # 实现难度 (low, medium, high)
    rationale: Optional[str] = None      # 理由说明


class PromptTemplate(BaseModel):
    """提示词模板"""
    model_config = ConfigDict(use_enum_values=True)

    template_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str                            # 模板名称
    category: TemplateCategory           # 模板类别
    description: str                     # 模板描述
    template_content: str                # 模板内容
    variables: List[str] = Field(default_factory=list)  # 变量列表
    example_values: Dict[str, str] = Field(default_factory=dict)  # 示例值
    use_cases: List[str] = Field(default_factory=list)  # 使用场景
    tags: List[str] = Field(default_factory=list)       # 标签
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE
    prompt_type: PromptType = PromptType.GENERAL
    success_rate: float = Field(ge=0.0, le=1.0, default=0.0)  # 成功率
    usage_count: int = Field(ge=0, default=0)           # 使用次数
    rating: float = Field(ge=0.0, le=5.0, default=0.0)  # 用户评分
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    is_active: bool = True


class TemplateMatch(BaseModel):
    """模板匹配结果"""
    template: PromptTemplate             # 匹配的模板
    similarity_score: float = Field(ge=0.0, le=1.0)  # 相似度评分
    matching_features: List[str] = Field(default_factory=list)  # 匹配特征
    adaptation_needed: bool = False      # 是否需要适配
    adaptation_suggestions: List[str] = Field(default_factory=list)  # 适配建议


class PromptAnalysis(BaseModel):
    """提示词分析结果"""
    model_config = ConfigDict(use_enum_values=True)

    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_content: str                  # 提示词内容
    analyzed_at: datetime = Field(default_factory=datetime.now)

    # 基本属性分析
    length_analysis: Dict[str, Any] = Field(default_factory=dict)  # 长度分析
    structure_analysis: Dict[str, Any] = Field(default_factory=dict)  # 结构分析
    elements: List[PromptElement] = Field(default_factory=list)    # 提取的元素

    # 质量评估
    quality_scores: List[QualityScore] = Field(default_factory=list)  # 质量评分
    overall_score: float = Field(ge=0.0, le=10.0, default=0.0)      # 总体评分

    # 识别的问题
    issues: List[str] = Field(default_factory=list)    # 发现的问题
    warnings: List[str] = Field(default_factory=list)  # 警告

    # 元数据
    detected_type: Optional[PromptType] = None          # 检测到的类型
    detected_complexity: Optional[ComplexityLevel] = None  # 检测到的复杂度
    language: str = "zh"                                # 语言
    processing_time_ms: int = 0                         # 处理时间


class OptimizedPrompt(BaseModel):
    """优化后的提示词"""
    model_config = ConfigDict(use_enum_values=True)

    optimization_id: str = Field(default_factory=lambda: str(uuid4()))
    original_prompt: str                 # 原始提示词
    optimized_prompt: str               # 优化后提示词
    optimization_level: OptimizationLevel  # 优化级别

    # 优化信息
    applied_strategies: List[OptimizationStrategy] = Field(default_factory=list)
    suggestions_used: List[OptimizationSuggestion] = Field(default_factory=list)
    template_used: Optional[PromptTemplate] = None

    # 改进分析
    improvement_analysis: Dict[str, Any] = Field(default_factory=dict)
    before_analysis: Optional[PromptAnalysis] = None
    after_analysis: Optional[PromptAnalysis] = None

    # 质量对比
    quality_improvement: Dict[QualityDimension, float] = Field(default_factory=dict)
    overall_improvement_score: float = Field(ge=-1.0, le=1.0, default=0.0)

    # 元数据
    optimized_at: datetime = Field(default_factory=datetime.now)
    optimization_time_ms: int = 0
    optimization_version: str = "1.0"
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)


class PromptCreationRequest(BaseModel):
    """提示词创建请求"""
    model_config = ConfigDict(use_enum_values=True)

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_requirements: str               # 用户需求描述
    target_domain: Optional[str] = None  # 目标领域
    target_audience: Optional[str] = None  # 目标受众
    desired_tone: Optional[str] = None   # 期望语调
    specific_constraints: List[str] = Field(default_factory=list)  # 特定约束
    example_inputs: List[str] = Field(default_factory=list)       # 示例输入
    expected_outputs: List[str] = Field(default_factory=list)     # 期望输出
    complexity_preference: ComplexityLevel = ComplexityLevel.SIMPLE
    optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    use_templates: bool = True           # 是否使用模板
    created_at: datetime = Field(default_factory=datetime.now)


class PromptOptimizationRequest(BaseModel):
    """提示词优化请求"""
    model_config = ConfigDict(use_enum_values=True)

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_to_optimize: str              # 待优化的提示词
    optimization_goals: List[OptimizationStrategy] = Field(default_factory=list)
    optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    focus_dimensions: List[QualityDimension] = Field(default_factory=list)
    preserve_elements: List[str] = Field(default_factory=list)  # 保留元素
    avoid_strategies: List[OptimizationStrategy] = Field(default_factory=list)
    target_score_improvement: float = Field(ge=0.0, le=10.0, default=2.0)
    use_templates: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class TemplateSearchCriteria(BaseModel):
    """模板搜索条件"""
    model_config = ConfigDict(use_enum_values=True)

    query: Optional[str] = None          # 搜索查询
    categories: List[TemplateCategory] = Field(default_factory=list)
    prompt_types: List[PromptType] = Field(default_factory=list)
    complexity_levels: List[ComplexityLevel] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    min_rating: float = Field(ge=0.0, le=5.0, default=0.0)
    min_success_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    is_active: bool = True
    limit: int = Field(ge=1, le=100, default=10)
    offset: int = Field(ge=0, default=0)


class PromptOptimizationResult(BaseModel):
    """提示词优化结果"""
    model_config = ConfigDict(use_enum_values=True)

    request_id: str                      # 请求ID
    success: bool                        # 是否成功
    optimized_prompt: Optional[OptimizedPrompt] = None  # 优化结果
    alternative_versions: List[OptimizedPrompt] = Field(default_factory=list)
    analysis: Optional[PromptAnalysis] = None           # 分析结果
    template_matches: List[TemplateMatch] = Field(default_factory=list)
    processing_summary: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

    def get_best_version(self) -> Optional[OptimizedPrompt]:
        """获取最佳版本"""
        if self.optimized_prompt:
            return self.optimized_prompt
        if self.alternative_versions:
            return max(self.alternative_versions,
                      key=lambda x: x.overall_improvement_score)
        return None

    def get_average_improvement(self) -> float:
        """获取平均改进分数"""
        all_versions = []
        if self.optimized_prompt:
            all_versions.append(self.optimized_prompt)
        all_versions.extend(self.alternative_versions)

        if not all_versions:
            return 0.0

        return sum(v.overall_improvement_score for v in all_versions) / len(all_versions)


class OptimizationConfig(BaseModel):
    """优化配置"""
    model_config = ConfigDict(use_enum_values=True)

    # 分析设置
    enable_deep_analysis: bool = True             # 启用深度分析
    analyze_structure: bool = True                # 分析结构
    detect_bias: bool = True                      # 检测偏见
    extract_elements: bool = True                 # 提取元素

    # 优化设置
    max_optimization_iterations: int = 3          # 最大优化轮次
    optimization_strategies: List[OptimizationStrategy] = Field(
        default_factory=lambda: list(OptimizationStrategy)
    )
    quality_thresholds: Dict[QualityDimension, float] = Field(default_factory=dict)

    # 模板匹配设置
    enable_template_matching: bool = True         # 启用模板匹配
    template_similarity_threshold: float = 0.7   # 模板相似度阈值
    max_template_matches: int = 5                 # 最大模板匹配数

    # 性能设置
    max_processing_time_ms: int = 60000          # 最大处理时间
    enable_parallel_processing: bool = True       # 启用并行处理
    cache_results: bool = True                   # 缓存结果

    # 输出设置
    include_analysis: bool = True                # 包含分析结果
    include_alternatives: bool = True            # 包含备选版本
    max_alternative_versions: int = 3            # 最大备选版本数
    include_reasoning: bool = True               # 包含推理过程

    @field_validator('template_similarity_threshold')
    @classmethod
    def validate_similarity_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("相似度阈值必须在 0 到 1 之间")
        return v


# 异常类定义
class PromptOptimizationError(Exception):
    """提示词优化错误"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class TemplateNotFoundError(Exception):
    """模板未找到错误"""
    def __init__(self, criteria: str):
        self.criteria = criteria
        super().__init__(f"未找到匹配条件的模板: {criteria}")


class InvalidPromptError(Exception):
    """无效提示词错误"""
    def __init__(self, prompt: str, reason: str):
        self.prompt = prompt
        self.reason = reason
        super().__init__(f"无效的提示词: {reason}")