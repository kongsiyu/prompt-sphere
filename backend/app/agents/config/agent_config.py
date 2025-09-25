"""
Agent配置管理模块

提供Agent系统的配置管理功能，包括全局设置、单个Agent配置、
以及与外部服务（DashScope、Redis等）的集成配置。
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import os


class ModelProvider(str, Enum):
    """支持的模型提供商"""
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AgentType(str, Enum):
    """Agent类型枚举"""
    PE_ENGINEER = "pe_engineer"
    PEQA = "peqa"
    GENERIC = "generic"


class AgentSettings(BaseModel):
    """Agent全局设置"""

    # 基础配置
    max_concurrent_agents: int = Field(default=10, ge=1, le=100)
    default_timeout_seconds: int = Field(default=300, ge=10, le=3600)
    heartbeat_interval: int = Field(default=30, ge=5, le=300)
    health_check_interval: int = Field(default=60, ge=10, le=600)

    # 消息队列配置
    max_queue_size: int = Field(default=100, ge=10, le=1000)
    message_retention_hours: int = Field(default=24, ge=1, le=168)  # 最多保留7天

    # 负载均衡配置
    load_balance_strategy: str = Field(default="least_loaded")
    agent_selection_timeout: int = Field(default=5, ge=1, le=30)

    # 重试配置
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=2, ge=1, le=60)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)

    # 监控配置
    enable_metrics: bool = Field(default=True)
    metrics_interval: int = Field(default=60, ge=10, le=3600)
    task_history_size: int = Field(default=1000, ge=100, le=10000)

    # 日志配置
    log_level: str = Field(default="INFO")
    enable_detailed_logging: bool = Field(default=False)
    log_message_content: bool = Field(default=False)  # 安全考虑，默认不记录消息内容

    @field_validator('load_balance_strategy')
    @classmethod
    def validate_load_balance_strategy(cls, v):
        allowed_strategies = ["round_robin", "least_loaded", "weighted", "random"]
        if v not in allowed_strategies:
            raise ValueError(f"load_balance_strategy must be one of {allowed_strategies}")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()


class ModelConfig(BaseModel):
    """模型配置"""

    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None  # 从环境变量获取
    api_endpoint: Optional[str] = None

    # 模型参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

    # 超时和重试
    request_timeout: int = Field(default=60, ge=5, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)

    # 速率限制
    rate_limit_rpm: Optional[int] = Field(None, ge=1)  # 每分钟请求数
    rate_limit_tpm: Optional[int] = Field(None, ge=1)  # 每分钟Token数


class AgentTypeConfig(BaseModel):
    """特定Agent类型的配置"""

    agent_type: AgentType
    display_name: str
    description: str

    # 能力配置
    capabilities: List[str] = Field(default_factory=list)
    supported_task_types: List[str] = Field(default_factory=list)

    # 资源限制
    max_concurrent_tasks: int = Field(default=3, ge=1, le=20)
    max_queue_size: int = Field(default=50, ge=10, le=500)
    priority_weight: float = Field(default=1.0, ge=0.1, le=10.0)

    # 模型配置
    primary_model: ModelConfig
    fallback_models: List[ModelConfig] = Field(default_factory=list)

    # 特定参数
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)

    # 系统提示词
    system_prompt: Optional[str] = None
    system_prompt_template: Optional[str] = None

    @field_validator('supported_task_types', mode='before')
    @classmethod
    def validate_task_types(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class OrchestrationConfig(BaseModel):
    """编排器配置"""

    # 基础设置
    orchestrator_id: str = Field(default="main_orchestrator")
    enable_persistence: bool = Field(default=True)
    persistence_interval: int = Field(default=60, ge=10, le=3600)

    # Agent发现
    auto_discovery: bool = Field(default=True)
    discovery_interval: int = Field(default=30, ge=10, le=300)

    # 故障恢复
    enable_auto_recovery: bool = Field(default=True)
    recovery_timeout: int = Field(default=120, ge=30, le=600)
    max_recovery_attempts: int = Field(default=3, ge=1, le=10)

    # 任务分发
    task_distribution_strategy: str = Field(default="capability_based")
    enable_task_queuing: bool = Field(default=True)
    max_queued_tasks: int = Field(default=1000, ge=100, le=10000)

    # 监控和告警
    enable_monitoring: bool = Field(default=True)
    monitoring_interval: int = Field(default=30, ge=10, le=300)
    alert_thresholds: Dict[str, Any] = Field(default_factory=lambda: {
        "error_rate": 0.1,
        "response_time": 30,
        "queue_size": 0.8
    })


class AgentConfig:
    """Agent配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._settings = None
        self._agent_types = {}
        self._models = {}
        self._orchestration = None

        # 从环境变量和配置文件加载配置
        self._load_configuration()

    def _load_configuration(self):
        """加载配置"""
        # 加载基础设置
        self._settings = AgentSettings(
            max_concurrent_agents=int(os.getenv('AGENT_MAX_CONCURRENT', 10)),
            default_timeout_seconds=int(os.getenv('AGENT_DEFAULT_TIMEOUT', 300)),
            heartbeat_interval=int(os.getenv('AGENT_HEARTBEAT_INTERVAL', 30)),
            load_balance_strategy=os.getenv('AGENT_LOAD_BALANCE_STRATEGY', 'least_loaded'),
            log_level=os.getenv('AGENT_LOG_LEVEL', 'INFO')
        )

        # 加载编排器配置
        self._orchestration = OrchestrationConfig(
            orchestrator_id=os.getenv('ORCHESTRATOR_ID', 'main_orchestrator'),
            enable_persistence=os.getenv('ORCHESTRATOR_PERSISTENCE', 'true').lower() == 'true'
        )

        # 加载模型配置
        self._load_model_configs()

        # 加载Agent类型配置
        self._load_agent_type_configs()

    def _load_model_configs(self):
        """加载模型配置"""
        # DashScope配置
        dashscope_config = ModelConfig(
            provider=ModelProvider.DASHSCOPE,
            model_name=os.getenv('DASHSCOPE_MODEL', 'qwen-turbo'),
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            api_endpoint=os.getenv('DASHSCOPE_API_ENDPOINT'),
            temperature=float(os.getenv('DASHSCOPE_TEMPERATURE', 0.7)),
            max_tokens=int(os.getenv('DASHSCOPE_MAX_TOKENS', 4096))
        )
        self._models['dashscope_primary'] = dashscope_config

        # 可以添加更多模型配置
        # OpenAI配置 (如果需要)
        if os.getenv('OPENAI_API_KEY'):
            openai_config = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                api_key=os.getenv('OPENAI_API_KEY'),
                temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7)),
                max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', 4096))
            )
            self._models['openai_fallback'] = openai_config

    def _load_agent_type_configs(self):
        """加载Agent类型配置"""

        # PE Engineer配置
        pe_config = AgentTypeConfig(
            agent_type=AgentType.PE_ENGINEER,
            display_name="Prompt Engineering Agent",
            description="专门负责提示词工程和优化的Agent",
            capabilities=["prompt_generation", "prompt_optimization", "content_analysis"],
            supported_task_types=["generate_prompt", "optimize_prompt", "analyze_content"],
            max_concurrent_tasks=int(os.getenv('PE_AGENT_MAX_TASKS', 3)),
            primary_model=self._models.get('dashscope_primary'),
            fallback_models=[self._models.get('openai_fallback')] if 'openai_fallback' in self._models else [],
            system_prompt=self._get_pe_system_prompt(),
            custom_parameters={
                "focus_areas": ["clarity", "specificity", "effectiveness"],
                "optimization_techniques": ["few_shot", "chain_of_thought", "role_playing"]
            }
        )
        self._agent_types[AgentType.PE_ENGINEER] = pe_config

        # PEQA配置
        peqa_config = AgentTypeConfig(
            agent_type=AgentType.PEQA,
            display_name="Prompt Quality Assessment Agent",
            description="专门负责提示词质量评估的Agent",
            capabilities=["quality_assessment", "scoring", "improvement_suggestions"],
            supported_task_types=["assess_quality", "score_prompt", "suggest_improvements"],
            max_concurrent_tasks=int(os.getenv('PEQA_AGENT_MAX_TASKS', 2)),
            primary_model=self._models.get('dashscope_primary'),
            fallback_models=[self._models.get('openai_fallback')] if 'openai_fallback' in self._models else [],
            system_prompt=self._get_peqa_system_prompt(),
            custom_parameters={
                "assessment_criteria": ["clarity", "completeness", "effectiveness", "safety"],
                "scoring_scale": {"min": 0, "max": 100, "pass_threshold": 70}
            }
        )
        self._agent_types[AgentType.PEQA] = peqa_config

    def _get_pe_system_prompt(self) -> str:
        """获取PE Agent系统提示词"""
        return """
你是一个专业的提示词工程师(Prompt Engineer)，专门负责生成和优化高质量的AI提示词。

你的核心能力包括：
1. 根据用户需求生成清晰、具体、有效的提示词
2. 优化现有提示词以提高输出质量
3. 分析提示词的结构和逻辑
4. 应用各种提示词技巧（如few-shot、chain-of-thought等）

工作原则：
- 确保提示词清晰明确，避免歧义
- 根据任务类型选择合适的提示词结构
- 考虑上下文和约束条件
- 注重可重现性和一致性
- 遵循安全和伦理准则

请始终以专业、准确、有帮助的方式回应用户请求。
""".strip()

    def _get_peqa_system_prompt(self) -> str:
        """获取PEQA Agent系统提示词"""
        return """
你是一个专业的提示词质量评估专家(Prompt Engineering Quality Assessor)，负责评估提示词的质量并提供改进建议。

评估维度：
1. 清晰度 - 提示词是否清晰明确，易于理解
2. 完整性 - 是否包含所有必要的信息和约束
3. 有效性 - 是否能够产生期望的输出结果
4. 安全性 - 是否符合安全和伦理准则

评分标准：
- 90-100分：优秀，提示词设计精良，各方面都表现出色
- 80-89分：良好，提示词质量较高，有少量改进空间
- 70-79分：合格，提示词基本可用，需要一些改进
- 60-69分：需要改进，提示词存在明显问题
- 0-59分：不合格，提示词需要重新设计

请为每个提示词提供详细的评估报告，包括具体评分和改进建议。
""".strip()

    @property
    def settings(self) -> AgentSettings:
        """获取全局设置"""
        return self._settings

    @property
    def orchestration(self) -> OrchestrationConfig:
        """获取编排器配置"""
        return self._orchestration

    def get_agent_config(self, agent_type: AgentType) -> Optional[AgentTypeConfig]:
        """获取特定Agent类型的配置"""
        return self._agent_types.get(agent_type)

    def get_model_config(self, model_key: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self._models.get(model_key)

    def get_all_agent_types(self) -> List[AgentType]:
        """获取所有可用的Agent类型"""
        return list(self._agent_types.keys())

    def get_capabilities_by_type(self, agent_type: AgentType) -> List[str]:
        """获取特定Agent类型的能力列表"""
        config = self._agent_types.get(agent_type)
        return config.capabilities if config else []

    def update_agent_config(
        self,
        agent_type: AgentType,
        **kwargs
    ) -> bool:
        """更新Agent配置"""
        try:
            if agent_type not in self._agent_types:
                return False

            config = self._agent_types[agent_type]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            return True
        except Exception as e:
            print(f"Error updating agent config: {e}")
            return False

    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置的完整性和正确性"""
        issues = []
        warnings = []

        # 检查基础配置
        if not self._settings:
            issues.append("Missing global settings")

        # 检查模型配置
        for model_key, model_config in self._models.items():
            if not model_config.api_key and model_config.provider in [ModelProvider.DASHSCOPE, ModelProvider.OPENAI]:
                issues.append(f"Missing API key for {model_key}")

        # 检查Agent类型配置
        for agent_type, config in self._agent_types.items():
            if not config.primary_model:
                issues.append(f"Missing primary model for {agent_type}")

            if not config.capabilities:
                warnings.append(f"No capabilities defined for {agent_type}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# 全局配置实例
agent_config = AgentConfig()