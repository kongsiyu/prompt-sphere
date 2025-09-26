"""
需求解析相关的数据模式定义

定义自然语言处理、意图识别和需求解析相关的数据结构，
使用 Pydantic 进行数据验证和序列化。
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..types import PromptType, ComplexityLevel


class IntentCategory(str, Enum):
    """意图类别"""
    CREATE_PROMPT = "create_prompt"           # 创建新提示词
    OPTIMIZE_PROMPT = "optimize_prompt"       # 优化现有提示词
    ANALYZE_PROMPT = "analyze_prompt"         # 分析提示词质量
    GET_TEMPLATE = "get_template"             # 获取模板
    CUSTOM_REQUEST = "custom_request"         # 自定义请求
    GENERAL_INQUIRY = "general_inquiry"       # 一般询问
    UNKNOWN = "unknown"                       # 未知意图


class ContextType(str, Enum):
    """上下文类型"""
    DOMAIN = "domain"                         # 领域信息
    TECHNICAL = "technical"                   # 技术背景
    BUSINESS = "business"                     # 业务场景
    PERSONAL = "personal"                     # 个人偏好
    CONSTRAINT = "constraint"                 # 约束条件
    EXAMPLE = "example"                       # 示例内容
    REFERENCE = "reference"                   # 参考资料


class SentimentType(str, Enum):
    """情感倾向"""
    POSITIVE = "positive"                     # 积极
    NEUTRAL = "neutral"                       # 中性
    NEGATIVE = "negative"                     # 消极
    URGENT = "urgent"                         # 紧急
    CONFUSED = "confused"                     # 困惑


class ConfidenceLevel(str, Enum):
    """置信度级别"""
    VERY_HIGH = "very_high"                   # 90-100%
    HIGH = "high"                             # 75-89%
    MEDIUM = "medium"                         # 50-74%
    LOW = "low"                               # 25-49%
    VERY_LOW = "very_low"                     # 0-24%


class ParsedIntent(BaseModel):
    """解析后的意图"""
    model_config = ConfigDict(use_enum_values=True)

    category: IntentCategory                  # 意图类别
    confidence: float = Field(ge=0.0, le=1.0) # 识别置信度
    confidence_level: ConfidenceLevel         # 置信度级别
    keywords: List[str] = Field(default_factory=list)  # 关键词
    sentiment: SentimentType = SentimentType.NEUTRAL   # 情感倾向
    urgency_level: int = Field(ge=1, le=5, default=3)  # 紧急程度 1-5
    alternative_intents: List[Dict[str, Any]] = Field(default_factory=list)  # 备选意图

    @field_validator('confidence_level', mode='before')
    @classmethod
    def validate_confidence_level(cls, v, info):
        """根据 confidence 值自动设置 confidence_level"""
        if 'confidence' in info.data:
            confidence = info.data['confidence']
            if confidence >= 0.9:
                return ConfidenceLevel.VERY_HIGH
            elif confidence >= 0.75:
                return ConfidenceLevel.HIGH
            elif confidence >= 0.5:
                return ConfidenceLevel.MEDIUM
            elif confidence >= 0.25:
                return ConfidenceLevel.LOW
            else:
                return ConfidenceLevel.VERY_LOW
        return v


class ExtractedContext(BaseModel):
    """提取的上下文信息"""
    model_config = ConfigDict(use_enum_values=True)

    context_type: ContextType                 # 上下文类型
    content: str                              # 内容
    importance: float = Field(ge=0.0, le=1.0, default=0.5)  # 重要性
    source_position: int                      # 在原文中的位置
    related_keywords: List[str] = Field(default_factory=list)  # 相关关键词


class DomainInfo(BaseModel):
    """领域信息"""
    name: str                                 # 领域名称
    confidence: float = Field(ge=0.0, le=1.0) # 识别置信度
    keywords: List[str] = Field(default_factory=list)  # 领域关键词
    subcategory: Optional[str] = None         # 子类别


class TechnicalRequirement(BaseModel):
    """技术要求"""
    requirement_type: str                     # 要求类型
    description: str                          # 描述
    priority: int = Field(ge=1, le=5, default=3)  # 优先级
    examples: List[str] = Field(default_factory=list)  # 示例


class QualityMetric(BaseModel):
    """质量指标"""
    metric_name: str                          # 指标名称
    score: float = Field(ge=0.0, le=1.0)     # 评分
    description: Optional[str] = None         # 说明


class ParsedRequirements(BaseModel):
    """完整的解析结果"""
    model_config = ConfigDict(use_enum_values=True)

    # 基本信息
    request_id: str = Field(default_factory=lambda: f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    original_input: str                       # 原始输入
    parsed_at: datetime = Field(default_factory=datetime.now)

    # 意图分析
    intent: ParsedIntent                      # 主要意图

    # 上下文信息
    extracted_contexts: List[ExtractedContext] = Field(default_factory=list)
    domain_info: Optional[DomainInfo] = None  # 领域信息

    # 需求详情
    main_objective: str                       # 主要目标
    key_requirements: List[str] = Field(default_factory=list)  # 关键需求
    technical_requirements: List[TechnicalRequirement] = Field(default_factory=list)  # 技术要求
    constraints: List[str] = Field(default_factory=list)  # 约束条件

    # 提示词属性
    suggested_prompt_type: PromptType = PromptType.GENERAL  # 建议的提示词类型
    complexity_estimate: ComplexityLevel = ComplexityLevel.SIMPLE  # 复杂度估计

    # 目标和输出
    target_audience: Optional[str] = None     # 目标受众
    expected_output_format: Optional[str] = None  # 期望输出格式
    tone_preferences: List[str] = Field(default_factory=list)  # 语调偏好

    # 示例和参考
    provided_examples: List[str] = Field(default_factory=list)  # 用户提供的示例
    reference_materials: List[str] = Field(default_factory=list)  # 参考材料

    # 质量和元数据
    parsing_quality: List[QualityMetric] = Field(default_factory=list)  # 解析质量
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0)  # 整体置信度
    processing_time_ms: int = 0               # 处理时间（毫秒）
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据

    # 建议和提示
    suggestions: List[str] = Field(default_factory=list)  # 改进建议
    warnings: List[str] = Field(default_factory=list)    # 警告信息
    missing_info: List[str] = Field(default_factory=list) # 缺失信息

    def get_context_by_type(self, context_type: ContextType) -> List[ExtractedContext]:
        """根据类型获取上下文"""
        return [ctx for ctx in self.extracted_contexts if ctx.context_type == context_type]

    def add_context(self, context_type: ContextType, content: str,
                   importance: float = 0.5, source_position: int = 0) -> None:
        """添加上下文信息"""
        context = ExtractedContext(
            context_type=context_type,
            content=content,
            importance=importance,
            source_position=source_position
        )
        self.extracted_contexts.append(context)

    def get_quality_score(self, metric_name: str) -> Optional[float]:
        """获取特定质量指标的评分"""
        for metric in self.parsing_quality:
            if metric.metric_name == metric_name:
                return metric.score
        return None

    def add_quality_metric(self, metric_name: str, score: float,
                          description: Optional[str] = None) -> None:
        """添加质量指标"""
        metric = QualityMetric(
            metric_name=metric_name,
            score=score,
            description=description
        )
        self.parsing_quality.append(metric)

    def is_high_confidence(self, threshold: float = 0.75) -> bool:
        """判断是否为高置信度解析结果"""
        return self.overall_confidence >= threshold

    def get_summary(self) -> Dict[str, Any]:
        """获取解析结果摘要"""
        return {
            "request_id": self.request_id,
            "intent": self.intent.category,
            "confidence": self.overall_confidence,
            "prompt_type": self.suggested_prompt_type,
            "complexity": self.complexity_estimate,
            "main_objective": self.main_objective,
            "key_requirements_count": len(self.key_requirements),
            "has_domain": self.domain_info is not None,
            "context_count": len(self.extracted_contexts),
            "quality_score": sum(m.score for m in self.parsing_quality) / max(len(self.parsing_quality), 1)
        }


class RequirementsValidationError(Exception):
    """需求验证错误"""
    def __init__(self, message: str, field: Optional[str] = None,
                 validation_errors: Optional[List[str]] = None):
        self.message = message
        self.field = field
        self.validation_errors = validation_errors or []
        super().__init__(self.message)


class RequirementsParsingConfig(BaseModel):
    """需求解析配置"""
    model_config = ConfigDict(use_enum_values=True)

    # 解析参数
    min_input_length: int = 10                # 最小输入长度
    max_input_length: int = 5000             # 最大输入长度
    intent_confidence_threshold: float = 0.5  # 意图识别置信度阈值
    context_importance_threshold: float = 0.3 # 上下文重要性阈值

    # NLP 设置
    enable_sentiment_analysis: bool = True    # 启用情感分析
    enable_domain_detection: bool = True      # 启用领域检测
    enable_keyword_extraction: bool = True    # 启用关键词提取

    # 质量控制
    require_main_objective: bool = True       # 要求识别主要目标
    min_quality_score: float = 0.6           # 最小质量分数

    # 性能设置
    max_processing_time_ms: int = 30000       # 最大处理时间
    enable_caching: bool = True               # 启用缓存

    @field_validator('intent_confidence_threshold', 'context_importance_threshold', 'min_quality_score')
    @classmethod
    def validate_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("阈值必须在 0 到 1 之间")
        return v