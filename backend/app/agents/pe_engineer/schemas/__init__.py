"""
PE Engineer Agent Schemas

数据模式定义模块，包含需求解析和提示词优化相关的数据结构和验证规则。
"""

from .requirements import (
    IntentCategory, ContextType, SentimentType, ConfidenceLevel,
    ParsedIntent, ExtractedContext, DomainInfo, TechnicalRequirement,
    QualityMetric, ParsedRequirements, RequirementsValidationError,
    RequirementsParsingConfig
)

from .prompts import (
    OptimizationStrategy, QualityDimension, TemplateCategory, OptimizationLevel,
    PromptElement, QualityScore, OptimizationSuggestion, PromptTemplate,
    TemplateMatch, PromptAnalysis, OptimizedPrompt, PromptCreationRequest,
    PromptOptimizationRequest, TemplateSearchCriteria, PromptOptimizationResult,
    OptimizationConfig, PromptOptimizationError, TemplateNotFoundError,
    InvalidPromptError
)

__all__ = [
    # Requirements schemas
    'IntentCategory', 'ContextType', 'SentimentType', 'ConfidenceLevel',
    'ParsedIntent', 'ExtractedContext', 'DomainInfo', 'TechnicalRequirement',
    'QualityMetric', 'ParsedRequirements', 'RequirementsValidationError',
    'RequirementsParsingConfig',

    # Prompts schemas
    'OptimizationStrategy', 'QualityDimension', 'TemplateCategory', 'OptimizationLevel',
    'PromptElement', 'QualityScore', 'OptimizationSuggestion', 'PromptTemplate',
    'TemplateMatch', 'PromptAnalysis', 'OptimizedPrompt', 'PromptCreationRequest',
    'PromptOptimizationRequest', 'TemplateSearchCriteria', 'PromptOptimizationResult',
    'OptimizationConfig', 'PromptOptimizationError', 'TemplateNotFoundError',
    'InvalidPromptError'
]
