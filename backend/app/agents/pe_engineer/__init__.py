"""
PE Engineer Agent 模块

Prompt Engineering 工程师 Agent 的主要模块，提供以下功能：
- 自然语言需求解析
- 动态表单生成
- 提示词创建和优化
- 模板管理

使用方式：
    from app.agents.pe_engineer import PEEngineerAgent, PETaskType, RequirementsParsed

    # 创建 Agent 实例
    agent = PEEngineerAgent()

    # 启动 Agent
    await agent.start()

    # 解析需求
    requirements = await agent.parse_requirements("帮我写一个销售邮件的提示词")

    # 生成表单
    form = await agent.generate_form(requirements)

    # 创建提示词
    prompt = await agent.create_prompt(form_data)

    # 优化提示词
    optimized = await agent.optimize_prompt(existing_prompt)
"""

from .PEEngineerAgent import PEEngineerAgent
from .types import (
    # 枚举类型
    PromptType,
    FormFieldType,
    ComplexityLevel,
    PETaskType,

    # 数据模型
    RequirementsParsed,
    DynamicForm,
    FormField,
    FormSection,
    OptimizedPrompt,
    PromptTemplate,
    OptimizationSuggestion,
    PETaskData,
    PEResponse,

    # 常量
    COMMON_FORM_FIELDS,
    OPTIMIZATION_TECHNIQUES
)
from .config import (
    PEEngineerConfig,
    DashScopeConfig,
    ProcessingConfig,
    RequirementsParsingConfig,
    FormGenerationConfig,
    PromptCreationConfig,
    OptimizationConfig,
    TemplateConfig,
    get_config,
    update_config
)

__all__ = [
    # 主要类
    "PEEngineerAgent",

    # 枚举
    "PromptType",
    "FormFieldType",
    "ComplexityLevel",
    "PETaskType",

    # 数据模型
    "RequirementsParsed",
    "DynamicForm",
    "FormField",
    "FormSection",
    "OptimizedPrompt",
    "PromptTemplate",
    "OptimizationSuggestion",
    "PETaskData",
    "PEResponse",

    # 配置
    "PEEngineerConfig",
    "DashScopeConfig",
    "ProcessingConfig",
    "RequirementsParsingConfig",
    "FormGenerationConfig",
    "PromptCreationConfig",
    "OptimizationConfig",
    "TemplateConfig",
    "get_config",
    "update_config",

    # 常量
    "COMMON_FORM_FIELDS",
    "OPTIMIZATION_TECHNIQUES"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "PE Engineer Team"
__description__ = "Prompt Engineering Agent for AI System"

# 快速创建 Agent 实例的便捷函数
def create_agent(config: PEEngineerConfig = None) -> PEEngineerAgent:
    """
    创建 PE Engineer Agent 实例

    Args:
        config: 可选的配置对象，如果不提供则使用默认配置

    Returns:
        PEEngineerAgent: 配置好的 Agent 实例

    Example:
        agent = create_agent()
        await agent.start()
    """
    return PEEngineerAgent(config)

# 快速任务创建函数
def create_parse_task(user_input: str, sender_id: str = "user") -> dict:
    """
    创建需求解析任务数据

    Args:
        user_input: 用户输入文本
        sender_id: 发送者ID

    Returns:
        dict: 任务数据字典
    """
    task_data = PETaskData(
        task_type=PETaskType.PARSE_REQUIREMENTS,
        input_data={"user_input": user_input}
    )

    return {
        "sender_id": sender_id,
        "recipient_id": "pe_engineer_001",
        "task_type": "PE_ENGINEER",
        "task_data": task_data.dict()
    }

def create_form_task(requirements: RequirementsParsed, sender_id: str = "user") -> dict:
    """
    创建表单生成任务数据

    Args:
        requirements: 解析后的需求对象
        sender_id: 发送者ID

    Returns:
        dict: 任务数据字典
    """
    task_data = PETaskData(
        task_type=PETaskType.GENERATE_FORM,
        input_data={"requirements": requirements.dict()}
    )

    return {
        "sender_id": sender_id,
        "recipient_id": "pe_engineer_001",
        "task_type": "PE_ENGINEER",
        "task_data": task_data.dict()
    }

def create_prompt_task(form_data: dict, sender_id: str = "user") -> dict:
    """
    创建提示词生成任务数据

    Args:
        form_data: 表单数据字典
        sender_id: 发送者ID

    Returns:
        dict: 任务数据字典
    """
    task_data = PETaskData(
        task_type=PETaskType.CREATE_PROMPT,
        input_data={"form_data": form_data}
    )

    return {
        "sender_id": sender_id,
        "recipient_id": "pe_engineer_001",
        "task_type": "PE_ENGINEER",
        "task_data": task_data.dict()
    }

def create_optimize_task(prompt: str, sender_id: str = "user") -> dict:
    """
    创建提示词优化任务数据

    Args:
        prompt: 要优化的提示词
        sender_id: 发送者ID

    Returns:
        dict: 任务数据字典
    """
    task_data = PETaskData(
        task_type=PETaskType.OPTIMIZE_PROMPT,
        input_data={"prompt": prompt}
    )

    return {
        "sender_id": sender_id,
        "recipient_id": "pe_engineer_001",
        "task_type": "PE_ENGINEER",
        "task_data": task_data.dict()
    }