"""
意图解析器

使用自然语言处理技术分析用户输入，识别用户的主要意图，
包括意图分类、置信度评估、关键词提取等功能。
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter

from ..schemas.requirements import (
    ParsedIntent, IntentCategory, SentimentType, ConfidenceLevel
)

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    """意图模式定义"""
    category: IntentCategory
    keywords: List[str]
    patterns: List[str]  # 正则表达式模式
    weight: float = 1.0
    context_hints: List[str] = None  # 上下文提示


class IntentParser:
    """
    意图解析器

    使用规则引擎和关键词匹配技术识别用户意图，
    支持多种意图类型和置信度评估。
    """

    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.sentiment_patterns = self._load_sentiment_patterns()
        self.keyword_weights = self._load_keyword_weights()

    def _load_intent_patterns(self) -> Dict[IntentCategory, List[IntentPattern]]:
        """加载意图模式"""
        patterns = {
            IntentCategory.CREATE_PROMPT: [
                IntentPattern(
                    category=IntentCategory.CREATE_PROMPT,
                    keywords=["创建", "生成", "制作", "写", "帮我写", "做一个", "设计"],
                    patterns=[
                        r"(帮我|请|能否|可以).*?(创建|生成|制作|写|做).*?(提示词|prompt|指令)",
                        r"(我想|我需要|想要).*?(创建|生成|制作).*?",
                        r"(写一个|做一个|生成一个|创建一个).*?(提示词|prompt)",
                        r"如何.*?(创建|制作|写).*?(提示词|prompt)"
                    ],
                    weight=1.5,
                    context_hints=["提示词", "prompt", "指令", "对话"]
                ),
                IntentPattern(
                    category=IntentCategory.CREATE_PROMPT,
                    keywords=["新的", "从头", "开始", "构建"],
                    patterns=[
                        r"从头.*?(开始|创建|制作)",
                        r"新的.*?(提示词|prompt)",
                        r"重新.*?(写|创建|制作)"
                    ],
                    weight=1.2
                )
            ],
            IntentCategory.OPTIMIZE_PROMPT: [
                IntentPattern(
                    category=IntentCategory.OPTIMIZE_PROMPT,
                    keywords=["优化", "改进", "改善", "提升", "修改", "完善", "调整"],
                    patterns=[
                        r"(优化|改进|改善|提升|修改|完善|调整).*?(提示词|prompt)",
                        r"(这个|现有的|当前的).*?提示词.*?(不好|有问题|需要|改进)",
                        r"如何.*?(优化|改进|改善).*?",
                        r"让.*?(提示词|prompt).*?(更好|更有效)"
                    ],
                    weight=1.5
                ),
                IntentPattern(
                    category=IntentCategory.OPTIMIZE_PROMPT,
                    keywords=["效果不好", "不满意", "有问题", "改善"],
                    patterns=[
                        r"(效果|结果).*?(不好|不满意|有问题)",
                        r"(提示词|prompt).*?(效果|结果).*?(不理想|不好)"
                    ],
                    weight=1.3
                )
            ],
            IntentCategory.ANALYZE_PROMPT: [
                IntentPattern(
                    category=IntentCategory.ANALYZE_PROMPT,
                    keywords=["分析", "评估", "检查", "评价", "判断", "看看"],
                    patterns=[
                        r"(分析|评估|检查|评价|判断).*?(提示词|prompt)",
                        r"(看看|帮我看|检查一下).*?(提示词|prompt)",
                        r"(这个|现有的).*?提示词.*?怎么样",
                        r"(质量|效果|性能).*?如何"
                    ],
                    weight=1.4
                )
            ],
            IntentCategory.GET_TEMPLATE: [
                IntentPattern(
                    category=IntentCategory.GET_TEMPLATE,
                    keywords=["模板", "示例", "例子", "参考", "样本"],
                    patterns=[
                        r"(有没有|给我|提供).*?(模板|示例|例子|参考)",
                        r"(模板|示例|例子).*?(提示词|prompt)",
                        r"参考.*?(其他|别人|现有)",
                        r"类似的.*?(提示词|prompt|例子)"
                    ],
                    weight=1.3
                )
            ],
            IntentCategory.GENERAL_INQUIRY: [
                IntentPattern(
                    category=IntentCategory.GENERAL_INQUIRY,
                    keywords=["什么是", "如何", "怎么", "为什么", "问", "了解"],
                    patterns=[
                        r"(什么是|什么叫).*?提示词",
                        r"(如何|怎么|怎样).*?(写|创建|使用).*?提示词",
                        r"(为什么|为啥).*?",
                        r"(提示词|prompt).*?(是什么|有什么|作用)"
                    ],
                    weight=1.0
                )
            ]
        }
        return patterns

    def _load_sentiment_patterns(self) -> Dict[SentimentType, List[str]]:
        """加载情感模式"""
        return {
            SentimentType.POSITIVE: [
                "好的", "很好", "棒", "太好了", "谢谢", "非常好", "满意", "喜欢", "完美"
            ],
            SentimentType.NEGATIVE: [
                "不好", "糟糕", "失望", "不满意", "有问题", "错误", "失败", "不行", "烦"
            ],
            SentimentType.URGENT: [
                "紧急", "急", "赶紧", "立即", "马上", "快", "尽快", "很急", "时间紧"
            ],
            SentimentType.CONFUSED: [
                "不明白", "困惑", "不懂", "搞不清", "不知道", "迷茫", "不理解", "疑惑"
            ]
        }

    def _load_keyword_weights(self) -> Dict[str, float]:
        """加载关键词权重"""
        return {
            # 高权重关键词
            "提示词": 2.0,
            "prompt": 2.0,
            "指令": 1.8,
            "对话": 1.5,

            # 中权重关键词
            "创建": 1.3,
            "生成": 1.3,
            "优化": 1.4,
            "改进": 1.3,
            "分析": 1.2,

            # 低权重关键词
            "帮助": 1.0,
            "问题": 1.1,
            "需要": 1.0,
            "想要": 1.0
        }

    def parse_intent(self, text: str) -> ParsedIntent:
        """
        解析用户输入的意图

        Args:
            text: 用户输入的文本

        Returns:
            ParsedIntent: 解析后的意图对象
        """
        if not text or len(text.strip()) < 3:
            return self._create_unknown_intent(text, "输入文本过短")

        # 预处理文本
        processed_text = self._preprocess_text(text)

        # 提取关键词
        keywords = self._extract_keywords(processed_text)

        # 计算各意图的置信度
        intent_scores = self._calculate_intent_scores(processed_text, keywords)

        # 识别情感倾向
        sentiment = self._analyze_sentiment(processed_text)

        # 评估紧急程度
        urgency_level = self._assess_urgency(processed_text)

        # 选择最佳意图
        best_intent, confidence = self._select_best_intent(intent_scores)

        # 生成备选意图
        alternative_intents = self._generate_alternatives(intent_scores, best_intent)

        return ParsedIntent(
            category=best_intent,
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            keywords=keywords,
            sentiment=sentiment,
            urgency_level=urgency_level,
            alternative_intents=alternative_intents
        )

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转换为小写
        processed = text.lower().strip()

        # 移除多余的空白字符
        processed = re.sub(r'\s+', ' ', processed)

        # 移除特殊字符但保留中文和基本标点
        processed = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()]', ' ', processed)

        return processed

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []

        # 基于词典的关键词匹配
        for keyword, weight in self.keyword_weights.items():
            if keyword.lower() in text:
                keywords.append(keyword)

        # 提取动词和名词（简化实现）
        action_words = re.findall(r'(创建|生成|制作|写|做|优化|改进|分析|检查|评估)', text)
        noun_words = re.findall(r'(提示词|prompt|指令|模板|示例|问题|需求)', text)

        keywords.extend(action_words)
        keywords.extend(noun_words)

        # 去重并返回
        return list(set(keywords))

    def _calculate_intent_scores(self, text: str, keywords: List[str]) -> Dict[IntentCategory, float]:
        """计算各意图的置信度分数"""
        scores = {category: 0.0 for category in IntentCategory}

        for category, patterns_list in self.intent_patterns.items():
            category_score = 0.0

            for pattern in patterns_list:
                # 关键词匹配得分
                keyword_score = 0.0
                for keyword in pattern.keywords:
                    if keyword in text:
                        weight = self.keyword_weights.get(keyword, 1.0)
                        keyword_score += pattern.weight * weight

                # 正则表达式匹配得分
                regex_score = 0.0
                for regex_pattern in pattern.patterns:
                    if re.search(regex_pattern, text):
                        regex_score += pattern.weight * 2.0  # 正则匹配权重较高

                # 上下文提示得分
                context_score = 0.0
                if pattern.context_hints:
                    for hint in pattern.context_hints:
                        if hint in text:
                            context_score += pattern.weight * 0.5

                pattern_total = keyword_score + regex_score + context_score
                category_score = max(category_score, pattern_total)

            scores[category] = category_score

        # 归一化分数
        max_score = max(scores.values()) if any(scores.values()) else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def _analyze_sentiment(self, text: str) -> SentimentType:
        """分析情感倾向"""
        sentiment_counts = {sentiment: 0 for sentiment in SentimentType}

        for sentiment, words in self.sentiment_patterns.items():
            for word in words:
                if word in text:
                    sentiment_counts[sentiment] += 1

        # 选择出现频率最高的情感
        max_sentiment = max(sentiment_counts, key=sentiment_counts.get)

        # 如果没有检测到明显情感，返回中性
        if sentiment_counts[max_sentiment] == 0:
            return SentimentType.NEUTRAL

        return max_sentiment

    def _assess_urgency(self, text: str) -> int:
        """评估紧急程度 (1-5级)"""
        urgency_indicators = {
            "紧急": 5, "急": 4, "赶紧": 4, "立即": 5, "马上": 4,
            "快": 3, "尽快": 4, "很急": 5, "时间紧": 4
        }

        max_urgency = 1
        for indicator, level in urgency_indicators.items():
            if indicator in text:
                max_urgency = max(max_urgency, level)

        return max_urgency

    def _select_best_intent(self, scores: Dict[IntentCategory, float]) -> Tuple[IntentCategory, float]:
        """选择最佳意图"""
        if not any(scores.values()):
            return IntentCategory.UNKNOWN, 0.0

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]

        # 如果置信度过低，标记为未知意图
        if confidence < 0.3:
            return IntentCategory.UNKNOWN, confidence

        return best_intent, confidence

    def _generate_alternatives(self, scores: Dict[IntentCategory, float],
                              best_intent: IntentCategory) -> List[Dict[str, Any]]:
        """生成备选意图"""
        alternatives = []

        # 排序所有意图分数
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 取前3个，但排除最佳意图
        for intent, score in sorted_scores[1:4]:
            if score > 0.1:  # 只保留有一定置信度的备选项
                alternatives.append({
                    "category": intent.value,
                    "confidence": score,
                    "description": self._get_intent_description(intent)
                })

        return alternatives

    def _get_intent_description(self, intent: IntentCategory) -> str:
        """获取意图描述"""
        descriptions = {
            IntentCategory.CREATE_PROMPT: "创建新的提示词",
            IntentCategory.OPTIMIZE_PROMPT: "优化现有提示词",
            IntentCategory.ANALYZE_PROMPT: "分析提示词质量",
            IntentCategory.GET_TEMPLATE: "获取提示词模板",
            IntentCategory.CUSTOM_REQUEST: "自定义请求",
            IntentCategory.GENERAL_INQUIRY: "一般性询问",
            IntentCategory.UNKNOWN: "未识别的意图"
        }
        return descriptions.get(intent, "未知意图")

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """根据置信度数值获取置信度级别"""
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

    def _create_unknown_intent(self, text: str, reason: str) -> ParsedIntent:
        """创建未知意图对象"""
        return ParsedIntent(
            category=IntentCategory.UNKNOWN,
            confidence=0.0,
            confidence_level=ConfidenceLevel.VERY_LOW,
            keywords=[],
            sentiment=SentimentType.NEUTRAL,
            urgency_level=1,
            alternative_intents=[{
                "category": IntentCategory.GENERAL_INQUIRY.value,
                "confidence": 0.1,
                "description": "可能是一般性询问",
                "reason": reason
            }]
        )

    def batch_parse_intents(self, texts: List[str]) -> List[ParsedIntent]:
        """批量解析意图"""
        results = []
        for text in texts:
            try:
                intent = self.parse_intent(text)
                results.append(intent)
            except Exception as e:
                logger.error(f"解析意图失败: {text[:50]}... - {str(e)}")
                results.append(self._create_unknown_intent(text, f"解析错误: {str(e)}"))

        return results

    def get_intent_statistics(self, parsed_intents: List[ParsedIntent]) -> Dict[str, Any]:
        """获取意图统计信息"""
        total = len(parsed_intents)
        if total == 0:
            return {}

        # 统计各意图类型
        category_counts = Counter(intent.category for intent in parsed_intents)

        # 统计置信度分布
        confidence_levels = Counter(intent.confidence_level for intent in parsed_intents)

        # 计算平均置信度
        avg_confidence = sum(intent.confidence for intent in parsed_intents) / total

        # 统计情感分布
        sentiment_counts = Counter(intent.sentiment for intent in parsed_intents)

        return {
            "total_intents": total,
            "category_distribution": dict(category_counts),
            "confidence_distribution": dict(confidence_levels),
            "average_confidence": avg_confidence,
            "sentiment_distribution": dict(sentiment_counts),
            "high_confidence_ratio": sum(1 for intent in parsed_intents
                                       if intent.confidence >= 0.75) / total
        }