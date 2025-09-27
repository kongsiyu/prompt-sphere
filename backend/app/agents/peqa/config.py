"""
PEQA Agent 配置管理

定义PEQA质量评估Agent的配置参数、默认值和配置验证逻辑。
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from .types import QualityDimension


class PEQAConfig(BaseModel):
    """PEQA Agent配置"""

    # 模型配置
    model_name: str = Field(default="qwen-max", description="使用的AI模型名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="请求超时时间")

    # 评估配置
    max_prompt_length: int = Field(default=10000, ge=100, description="最大提示词长度")
    enable_parallel_processing: bool = Field(default=True, description="启用并行处理")
    batch_size: int = Field(default=5, ge=1, le=20, description="批处理大小")

    # 质量维度权重
    dimension_weights: Dict[QualityDimension, float] = Field(
        default_factory=lambda: {
            QualityDimension.CLARITY: 0.25,         # 清晰度 25%
            QualityDimension.SPECIFICITY: 0.20,     # 具体性 20%
            QualityDimension.COMPLETENESS: 0.20,    # 完整性 20%
            QualityDimension.EFFECTIVENESS: 0.20,   # 有效性 20%
            QualityDimension.ROBUSTNESS: 0.15       # 鲁棒性 15%
        },
        description="质量维度权重分配"
    )

    # 质量阈值
    quality_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "excellent": 0.90,    # 优秀
            "good": 0.70,         # 良好
            "fair": 0.50,         # 一般
            "poor": 0.30          # 较差
        },
        description="质量等级阈值"
    )

    # 评分配置
    scoring_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "use_ai_scoring": True,           # 使用AI评分
            "confidence_threshold": 0.7,     # 置信度阈值
            "require_evidence": True,        # 要求提供证据
            "max_evidence_items": 5,         # 最大证据数量
            "enable_caching": True,          # 启用缓存
            "cache_ttl_seconds": 3600        # 缓存TTL
        },
        description="评分相关配置"
    )

    # 改进建议配置
    improvement_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_suggestions": 10,           # 最大建议数量
            "min_impact_score": 0.1,        # 最小影响分数
            "prioritize_high_impact": True, # 优先高影响建议
            "include_examples": True,       # 包含示例
            "group_by_category": True       # 按类别分组
        },
        description="改进建议相关配置"
    )

    # 报告配置
    report_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_format": "detailed",   # 默认报告格式
            "include_charts": False,        # 包含图表
            "language": "zh",               # 报告语言
            "max_report_length": 50000,     # 最大报告长度
            "enable_templates": True        # 启用模板
        },
        description="报告生成相关配置"
    )

    # 基准测试配置
    benchmark_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_sample_size": 100,     # 默认样本大小
            "enable_performance_monitoring": True,  # 启用性能监控
            "save_results": True,           # 保存结果
            "compare_with_baseline": False  # 与基线对比
        },
        description="基准测试相关配置"
    )

    # 日志配置
    logging_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",                # 日志级别
            "enable_file_logging": True,    # 启用文件日志
            "log_file_path": "logs/peqa.log",  # 日志文件路径
            "max_log_file_size_mb": 100,    # 最大日志文件大小
            "log_retention_days": 30        # 日志保留天数
        },
        description="日志相关配置"
    )

    @field_validator('dimension_weights')
    @classmethod
    def validate_dimension_weights(cls, v):
        """验证维度权重"""
        if not v:
            raise ValueError("维度权重不能为空")

        # 检查权重总和
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"维度权重总和必须为1.0，当前为{total_weight}")

        # 检查权重范围
        for dimension, weight in v.items():
            if not 0 <= weight <= 1:
                raise ValueError(f"维度 {dimension} 的权重必须在0-1之间，当前为{weight}")

        return v

    @field_validator('quality_thresholds')
    @classmethod
    def validate_quality_thresholds(cls, v):
        """验证质量阈值"""
        required_keys = {"excellent", "good", "fair", "poor"}
        if not all(key in v for key in required_keys):
            raise ValueError(f"质量阈值必须包含所有必需的键: {required_keys}")

        # 检查阈值顺序
        thresholds = [v["excellent"], v["good"], v["fair"], v["poor"]]
        if thresholds != sorted(thresholds, reverse=True):
            raise ValueError("质量阈值必须按降序排列")

        # 检查阈值范围
        for key, threshold in v.items():
            if not 0 <= threshold <= 1:
                raise ValueError(f"阈值 {key} 必须在0-1之间，当前为{threshold}")

        return v

    def get_dimension_weight(self, dimension: QualityDimension) -> float:
        """获取维度权重"""
        return self.dimension_weights.get(dimension, 0.0)

    def get_quality_threshold(self, level: str) -> float:
        """获取质量阈值"""
        return self.quality_thresholds.get(level, 0.0)

    def is_parallel_processing_enabled(self) -> bool:
        """是否启用并行处理"""
        return self.enable_parallel_processing

    def get_scoring_config(self, key: str, default: Any = None) -> Any:
        """获取评分配置"""
        return self.scoring_config.get(key, default)

    def get_improvement_config(self, key: str, default: Any = None) -> Any:
        """获取改进配置"""
        return self.improvement_config.get(key, default)

    def get_report_config(self, key: str, default: Any = None) -> Any:
        """获取报告配置"""
        return self.report_config.get(key, default)

    def get_benchmark_config(self, key: str, default: Any = None) -> Any:
        """获取基准测试配置"""
        return self.benchmark_config.get(key, default)

    def get_logging_config(self, key: str, default: Any = None) -> Any:
        """获取日志配置"""
        return self.logging_config.get(key, default)

    @classmethod
    def from_env(cls) -> "PEQAConfig":
        """从环境变量创建配置"""
        config_dict = {}

        # 从环境变量读取基本配置
        env_mappings = {
            "PEQA_MODEL_NAME": "model_name",
            "PEQA_API_KEY": "api_key",
            "PEQA_BASE_URL": "base_url",
            "PEQA_MAX_RETRIES": ("max_retries", int),
            "PEQA_TIMEOUT": ("timeout_seconds", int),
            "PEQA_MAX_PROMPT_LENGTH": ("max_prompt_length", int),
            "PEQA_ENABLE_PARALLEL": ("enable_parallel_processing", lambda x: x.lower() == "true"),
            "PEQA_BATCH_SIZE": ("batch_size", int)
        }

        for env_key, mapping in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                if isinstance(mapping, tuple):
                    field_name, converter = mapping
                    try:
                        config_dict[field_name] = converter(value)
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"无效的环境变量值 {env_key}={value}: {e}")
                else:
                    config_dict[mapping] = value

        return cls(**config_dict)

    @classmethod
    def from_file(cls, config_path: str) -> "PEQAConfig":
        """从配置文件创建配置"""
        import json
        import yaml

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                config_dict = json.load(f)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config_dict = yaml.safe_load(f)
            else:
                raise ValueError("不支持的配置文件格式，支持 .json 和 .yaml")

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    def save_to_file(self, config_path: str) -> None:
        """保存到配置文件"""
        import json
        import yaml

        config_dict = self.to_dict()

        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError("不支持的配置文件格式，支持 .json 和 .yaml")

    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置有效性"""
        issues = []
        warnings = []

        # 检查权重总和
        weight_sum = sum(self.dimension_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            issues.append(f"维度权重总和不为1.0: {weight_sum}")

        # 检查阈值逻辑
        thresholds = self.quality_thresholds
        if thresholds["good"] >= thresholds["excellent"]:
            issues.append("good阈值不应大于或等于excellent阈值")

        # 检查性能配置
        if self.batch_size > 10 and not self.enable_parallel_processing:
            warnings.append("较大的批处理大小但未启用并行处理可能影响性能")

        # 检查超时配置
        if self.timeout_seconds < 10:
            warnings.append("超时时间过短可能导致评估失败")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# 默认配置实例
DEFAULT_PEQA_CONFIG = PEQAConfig()


def get_default_config() -> PEQAConfig:
    """获取默认配置"""
    return DEFAULT_PEQA_CONFIG


def create_config_from_env() -> PEQAConfig:
    """从环境变量创建配置"""
    return PEQAConfig.from_env()


def load_config(config_path: Optional[str] = None) -> PEQAConfig:
    """
    加载配置

    优先级: 配置文件 > 环境变量 > 默认配置
    """
    if config_path and os.path.exists(config_path):
        return PEQAConfig.from_file(config_path)

    # 尝试从环境变量创建
    try:
        return PEQAConfig.from_env()
    except Exception:
        # 回退到默认配置
        return get_default_config()