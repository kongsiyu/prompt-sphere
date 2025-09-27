"""
PEQA Agent 类型定义

定义 Prompt Engineering Quality Assessment Agent 相关的数据类型和结构，
包括质量评估、评分、改进建议等核心功能的类型定义。
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import uuid4


class QualityDimension(str, Enum):
    """质量评估维度"""
    CLARITY = "clarity"              # 清晰度
    SPECIFICITY = "specificity"      # 具体性
    COMPLETENESS = "completeness"    # 完整性
    EFFECTIVENESS = "effectiveness"  # 有效性
    ROBUSTNESS = "robustness"       # 鲁棒性


class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "excellent"    # 优秀 (0.9-1.0)
    GOOD = "good"             # 良好 (0.7-0.9)
    FAIR = "fair"             # 一般 (0.5-0.7)
    POOR = "poor"             # 较差 (0.3-0.5)
    VERY_POOR = "very_poor"   # 很差 (0.0-0.3)


class ImprovementPriority(str, Enum):
    """改进优先级"""
    CRITICAL = "critical"     # 关键
    HIGH = "high"            # 高
    MEDIUM = "medium"        # 中
    LOW = "low"              # 低


class ImprovementCategory(str, Enum):
    """改进类别"""
    STRUCTURE = "structure"           # 结构改进
    CLARITY = "clarity"              # 清晰度改进
    SPECIFICITY = "specificity"      # 具体性改进
    COMPLETENESS = "completeness"    # 完整性改进
    EFFECTIVENESS = "effectiveness"  # 有效性改进
    ROBUSTNESS = "robustness"       # 鲁棒性改进
    CONTEXT = "context"             # 上下文改进
    EXAMPLES = "examples"           # 示例改进
    CONSTRAINTS = "constraints"     # 约束改进
    TONE = "tone"                   # 语调改进


class ReportFormat(str, Enum):
    """报告格式"""
    JSON = "json"           # JSON格式
    HTML = "html"           # HTML格式
    MARKDOWN = "markdown"   # Markdown格式
    PDF = "pdf"             # PDF格式
    TEXT = "text"           # 纯文本格式
    CSV = "csv"             # CSV格式


class BenchmarkType(str, Enum):
    """基准测试类型"""
    PERFORMANCE = "performance"     # 性能测试
    QUALITY = "quality"            # 质量测试
    SCALABILITY = "scalability"    # 可扩展性测试
    ACCURACY = "accuracy"          # 准确性测试


class QualityScore(BaseModel):
    """质量评分"""
    dimension: QualityDimension      # 质量维度
    score: float = Field(ge=0.0, le=1.0)  # 评分 (0-1)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)  # 置信度
    reasoning: Optional[str] = None  # 评分理由
    evidence: List[str] = Field(default_factory=list)  # 支持证据
    issues: List[str] = Field(default_factory=list)    # 发现的问题


class Improvement(BaseModel):
    """改进建议"""
    improvement_id: str = Field(default_factory=lambda: str(uuid4()))
    category: ImprovementCategory    # 改进类别
    priority: ImprovementPriority    # 优先级
    title: str                       # 建议标题
    description: str                 # 建议描述
    before_example: Optional[str] = None    # 改进前示例
    after_example: Optional[str] = None     # 改进后示例
    impact_score: float = Field(ge=0.0, le=1.0)  # 影响评分
    difficulty: str = "medium"       # 实施难度 (easy, medium, hard)
    estimated_improvement: float = Field(ge=0.0, le=1.0)  # 预估改进幅度
    rationale: Optional[str] = None  # 理由说明


class QualityAssessment(BaseModel):
    """质量评估结果"""
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_content: str              # 被评估的提示词
    assessed_at: datetime = Field(default_factory=datetime.now)

    # 评分结果
    overall_score: float = Field(ge=0.0, le=1.0)  # 总体评分
    dimension_scores: Dict[QualityDimension, QualityScore]  # 各维度评分
    quality_level: QualityLevel      # 质量等级
    confidence_level: float = Field(ge=0.0, le=1.0)  # 整体置信度

    # 分析结果
    strengths: List[str] = Field(default_factory=list)      # 优势
    weaknesses: List[str] = Field(default_factory=list)     # 不足
    improvement_suggestions: List[Improvement] = Field(default_factory=list)  # 改进建议

    # 详细分析
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: int = 0      # 处理时间

    def get_dimension_score(self, dimension: QualityDimension) -> float:
        """获取特定维度的评分"""
        return self.dimension_scores.get(dimension, QualityScore(dimension=dimension, score=0.0)).score

    def get_top_issues(self, limit: int = 3) -> List[str]:
        """获取主要问题"""
        all_issues = []
        for score in self.dimension_scores.values():
            all_issues.extend(score.issues)
        return all_issues[:limit]


class AssessmentReport(BaseModel):
    """评估报告"""
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    assessment: QualityAssessment    # 评估结果
    report_format: ReportFormat      # 报告格式
    generated_at: datetime = Field(default_factory=datetime.now)

    # 报告内容
    executive_summary: str           # 执行摘要
    detailed_content: str           # 详细内容
    recommendations: List[str] = Field(default_factory=list)  # 推荐行动

    # 元数据
    report_version: str = "1.0"
    language: str = "zh"
    generated_by: str = "PEQA Agent"


class BenchmarkResult(BaseModel):
    """基准测试结果"""
    benchmark_id: str = Field(default_factory=lambda: str(uuid4()))
    benchmark_type: BenchmarkType    # 测试类型
    executed_at: datetime = Field(default_factory=datetime.now)

    # 测试结果
    total_prompts: int              # 测试提示词总数
    average_score: float = Field(ge=0.0, le=1.0)  # 平均评分
    highest_score: float = Field(ge=0.0, le=1.0)  # 最高评分
    lowest_score: float = Field(ge=0.0, le=1.0)   # 最低评分

    # 性能指标
    total_processing_time_ms: int   # 总处理时间
    average_processing_time_ms: float  # 平均处理时间
    throughput: float               # 吞吐量 (prompts/second)

    # 详细结果
    individual_results: List[QualityAssessment] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

    def get_quality_distribution(self) -> Dict[QualityLevel, int]:
        """获取质量等级分布"""
        distribution = {level: 0 for level in QualityLevel}
        for result in self.individual_results:
            distribution[result.quality_level] += 1
        return distribution


class AssessmentRequest(BaseModel):
    """评估请求"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_content: str              # 要评估的提示词
    assessment_options: Dict[str, Any] = Field(default_factory=dict)  # 评估选项
    focus_dimensions: List[QualityDimension] = Field(default_factory=list)  # 重点维度
    include_suggestions: bool = True  # 是否包含改进建议
    detailed_analysis: bool = True   # 是否进行详细分析
    created_at: datetime = Field(default_factory=datetime.now)


class BatchAssessmentRequest(BaseModel):
    """批量评估请求"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    prompts: List[str]               # 要评估的提示词列表
    assessment_options: Dict[str, Any] = Field(default_factory=dict)
    include_summary: bool = True     # 是否包含汇总
    parallel_processing: bool = True  # 是否并行处理
    created_at: datetime = Field(default_factory=datetime.now)


class ImprovementPlan(BaseModel):
    """改进计划"""
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    original_assessment: QualityAssessment  # 原始评估
    planned_improvements: List[Improvement]  # 计划的改进

    # 计划详情
    priority_order: List[str]        # 优先级顺序 (improvement_id列表)
    estimated_total_improvement: float = Field(ge=0.0, le=1.0)  # 预估总改进幅度
    implementation_timeline: Dict[str, str] = Field(default_factory=dict)  # 实施时间线

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None


class QualityCriteria(BaseModel):
    """质量标准"""
    criteria_id: str = Field(default_factory=lambda: str(uuid4()))
    dimension: QualityDimension      # 适用维度

    # 评分标准
    excellent_threshold: float = Field(ge=0.0, le=1.0, default=0.9)
    good_threshold: float = Field(ge=0.0, le=1.0, default=0.7)
    fair_threshold: float = Field(ge=0.0, le=1.0, default=0.5)
    poor_threshold: float = Field(ge=0.0, le=1.0, default=0.3)

    # 评估要素
    evaluation_factors: List[str] = Field(default_factory=list)
    weight_factors: Dict[str, float] = Field(default_factory=dict)

    # 描述
    description: str                 # 标准描述
    examples: Dict[str, str] = Field(default_factory=dict)  # 示例

    @field_validator('good_threshold', 'fair_threshold', 'poor_threshold')
    @classmethod
    def validate_thresholds(cls, v, info):
        """验证阈值顺序"""
        if info.field_name == 'good_threshold' and hasattr(info, 'data'):
            if v >= info.data.get('excellent_threshold', 1.0):
                raise ValueError("good_threshold必须小于excellent_threshold")
        return v


# 异常类定义
class PEQAError(Exception):
    """PEQA通用错误"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AssessmentError(PEQAError):
    """评估错误"""
    pass


class InvalidPromptError(PEQAError):
    """无效提示词错误"""
    def __init__(self, prompt: str, reason: str):
        self.prompt = prompt
        self.reason = reason
        super().__init__(f"无效的提示词: {reason}")


class ScoringError(PEQAError):
    """评分错误"""
    pass


class ImprovementGenerationError(PEQAError):
    """改进建议生成错误"""
    pass


class ReportGenerationError(PEQAError):
    """报告生成错误"""
    pass


class BenchmarkError(PEQAError):
    """基准测试错误"""
    pass