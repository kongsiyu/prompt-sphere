"""
PEQA (Prompt Engineering Quality Assessment) Agent Package

提供提示词质量评估、评分、改进建议生成和详细报告创建的完整解决方案。

主要组件:
- PEQAAgent: 主要的质量评估Agent
- QualityScorer: 多维度质量评分器
- ImprovementEngine: 改进建议生成引擎
- ReportGenerator: 报告生成器
- Config: 配置管理

主要功能:
- 多维度质量评估 (清晰度、具体性、完整性、有效性、鲁棒性)
- 智能改进建议生成
- 多格式报告输出
- 性能基准测试
- 批量评估处理
"""

from .PEQAAgent import PEQAAgent
from .QualityScorer import QualityScorer
from .ImprovementEngine import ImprovementEngine
from .ReportGenerator import ReportGenerator
from .config import PEQAConfig, get_default_config, load_config

from .types import (
    # 核心类型
    QualityAssessment,
    QualityScore,
    Improvement,
    AssessmentReport,
    BenchmarkResult,

    # 枚举类型
    QualityDimension,
    QualityLevel,
    ImprovementPriority,
    ImprovementCategory,
    ReportFormat,
    BenchmarkType,

    # 请求类型
    AssessmentRequest,
    BatchAssessmentRequest,

    # 异常类型
    PEQAError,
    AssessmentError,
    InvalidPromptError,
    ScoringError,
    ImprovementGenerationError,
    ReportGenerationError,
    BenchmarkError
)

# 版本信息
__version__ = "1.0.0"
__author__ = "PEQA Team"
__description__ = "Prompt Engineering Quality Assessment Agent"

# 导出的公共接口
__all__ = [
    # 主要组件
    "PEQAAgent",
    "QualityScorer",
    "ImprovementEngine",
    "ReportGenerator",
    "PEQAConfig",

    # 配置函数
    "get_default_config",
    "load_config",

    # 核心数据类型
    "QualityAssessment",
    "QualityScore",
    "Improvement",
    "AssessmentReport",
    "BenchmarkResult",

    # 枚举类型
    "QualityDimension",
    "QualityLevel",
    "ImprovementPriority",
    "ImprovementCategory",
    "ReportFormat",
    "BenchmarkType",

    # 请求类型
    "AssessmentRequest",
    "BatchAssessmentRequest",

    # 异常类型
    "PEQAError",
    "AssessmentError",
    "InvalidPromptError",
    "ScoringError",
    "ImprovementGenerationError",
    "ReportGenerationError",
    "BenchmarkError",

    # 版本信息
    "__version__"
]


def create_peqa_agent(config_path: str = None) -> PEQAAgent:
    """
    创建PEQA Agent实例的便捷函数

    Args:
        config_path: 配置文件路径，可选

    Returns:
        PEQAAgent: 配置好的PEQA Agent实例
    """
    config = load_config(config_path)
    return PEQAAgent(config)


async def quick_assess(prompt: str, config_path: str = None) -> QualityAssessment:
    """
    快速评估提示词质量的便捷函数

    Args:
        prompt: 要评估的提示词
        config_path: 配置文件路径，可选

    Returns:
        QualityAssessment: 评估结果
    """
    agent = create_peqa_agent(config_path)
    return await agent.assess_prompt(prompt)


async def batch_assess(prompts: list, config_path: str = None) -> dict:
    """
    批量评估提示词质量的便捷函数

    Args:
        prompts: 要评估的提示词列表
        config_path: 配置文件路径，可选

    Returns:
        dict: 批量评估结果
    """
    agent = create_peqa_agent(config_path)

    from .types import BatchAssessmentRequest
    request = BatchAssessmentRequest(prompts=prompts)

    return await agent.batch_assess(request)


def get_supported_dimensions() -> list:
    """
    获取支持的质量评估维度

    Returns:
        list: 支持的维度列表
    """
    return [dimension.value for dimension in QualityDimension]


def get_supported_formats() -> list:
    """
    获取支持的报告格式

    Returns:
        list: 支持的格式列表
    """
    return [format.value for format in ReportFormat]


def validate_prompt(prompt: str) -> dict:
    """
    验证提示词基本格式

    Args:
        prompt: 要验证的提示词

    Returns:
        dict: 验证结果，包含是否有效和错误信息
    """
    try:
        from .PEQAAgent import PEQAAgent

        # 创建临时agent进行验证
        agent = PEQAAgent()
        agent._validate_prompt(prompt)

        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }
    except InvalidPromptError as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"验证过程出错: {str(e)}"],
            "warnings": []
        }


# 包级别的配置
DEFAULT_CONFIG = get_default_config()

# 日志配置
import logging

def setup_logging(level: str = "INFO"):
    """
    设置PEQA包的日志配置

    Args:
        level: 日志级别
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 设置PEQA相关模块的日志级别
    peqa_logger = logging.getLogger('app.agents.peqa')
    peqa_logger.setLevel(getattr(logging, level.upper()))


# 包初始化时的操作
setup_logging(DEFAULT_CONFIG.get_logging_config("level", "INFO"))