"""
上下文提取器

从用户输入中提取相关的上下文信息，包括领域信息、技术要求、
约束条件、示例等，为需求解析提供丰富的背景信息。
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from ..schemas.requirements import (
    ExtractedContext, ContextType, DomainInfo, TechnicalRequirement
)

logger = logging.getLogger(__name__)


@dataclass
class ContextPattern:
    """上下文模式定义"""
    context_type: ContextType
    keywords: List[str]
    patterns: List[str]  # 正则表达式
    weight: float = 1.0
    min_importance: float = 0.3


@dataclass
class DomainPattern:
    """领域模式定义"""
    domain_name: str
    keywords: List[str]
    indicators: List[str]  # 领域指示词
    weight: float = 1.0


class ContextExtractor:
    """
    上下文提取器

    使用规则引擎和模式匹配技术从用户输入中提取
    各种类型的上下文信息。
    """

    def __init__(self):
        self.context_patterns = self._load_context_patterns()
        self.domain_patterns = self._load_domain_patterns()
        self.technical_keywords = self._load_technical_keywords()
        self.constraint_indicators = self._load_constraint_indicators()
        self.example_indicators = self._load_example_indicators()

    def _load_context_patterns(self) -> Dict[ContextType, List[ContextPattern]]:
        """加载上下文模式"""
        return {
            ContextType.DOMAIN: [
                ContextPattern(
                    context_type=ContextType.DOMAIN,
                    keywords=["领域", "行业", "专业", "在", "做", "工作", "从事"],
                    patterns=[
                        r"(在|从事|工作在|专业是|领域是|行业是)[\s]*([^\s，。！？；]+)",
                        r"([^\s，。！？；]+)(领域|行业|专业|方面)",
                        r"(我是|做)[\s]*([^\s，。！？；]+)(工作|开发|设计)"
                    ],
                    weight=1.5
                ),
                ContextPattern(
                    context_type=ContextType.DOMAIN,
                    keywords=["技术", "开发", "设计", "管理", "运营", "营销", "教育"],
                    patterns=[
                        r"(技术|开发|设计|管理|运营|营销|教育)(相关|方面|工作)",
                        r"(前端|后端|全栈|移动|AI|数据|产品)[\s]*(开发|工程师)"
                    ],
                    weight=1.3
                )
            ],
            ContextType.TECHNICAL: [
                ContextPattern(
                    context_type=ContextType.TECHNICAL,
                    keywords=["技术", "API", "接口", "框架", "库", "工具", "平台"],
                    patterns=[
                        r"(使用|采用|基于|通过)[\s]*([^\s，。！？；]+)(技术|框架|工具|平台)",
                        r"(API|接口|SDK)[\s]*([^\s，。！？；]+)",
                        r"([^\s，。！？；]+)(版本|v\d+)"
                    ],
                    weight=1.4
                ),
                ContextPattern(
                    context_type=ContextType.TECHNICAL,
                    keywords=["编程语言", "Python", "JavaScript", "Java", "C++", "Go"],
                    patterns=[
                        r"(Python|JavaScript|Java|C\+\+|Go|PHP|Ruby|Swift|Kotlin|TypeScript)",
                        r"(编程语言|语言)[\s]*([^\s，。！？；]+)"
                    ],
                    weight=1.3
                )
            ],
            ContextType.BUSINESS: [
                ContextPattern(
                    context_type=ContextType.BUSINESS,
                    keywords=["业务", "商业", "项目", "产品", "服务", "客户", "用户"],
                    patterns=[
                        r"(业务|商业|项目|产品|服务)[\s]*([^\s，。！？；]+)",
                        r"(面向|针对|为了)[\s]*([^\s，。！？；]+)(用户|客户|群体)",
                        r"(解决|处理|实现)[\s]*([^\s，。！？；]+)(问题|需求|目标)"
                    ],
                    weight=1.2
                )
            ],
            ContextType.CONSTRAINT: [
                ContextPattern(
                    context_type=ContextType.CONSTRAINT,
                    keywords=["限制", "约束", "不能", "不要", "避免", "禁止", "要求"],
                    patterns=[
                        r"(不能|不要|避免|禁止|限制|约束)[\s]*([^\s，。！？；]+)",
                        r"(必须|一定要|要求)[\s]*([^\s，。！？；]+)",
                        r"(长度|字数|时间)[\s]*(不超过|限制|要求)[\s]*([^\s，。！？；]+)"
                    ],
                    weight=1.6
                )
            ],
            ContextType.EXAMPLE: [
                ContextPattern(
                    context_type=ContextType.EXAMPLE,
                    keywords=["例如", "比如", "举例", "示例", "样例", "像"],
                    patterns=[
                        r"(例如|比如|举例|示例|样例)[:：]?[\s]*([^，。！？；]+)",
                        r"像[\s]*([^\s，。！？；]+)[\s]*(这样|一样)",
                        r"参考[\s]*([^\s，。！？；]+)"
                    ],
                    weight=1.4
                )
            ],
            ContextType.PERSONAL: [
                ContextPattern(
                    context_type=ContextType.PERSONAL,
                    keywords=["我", "我的", "个人", "习惯", "偏好", "喜欢", "风格"],
                    patterns=[
                        r"(我|个人)[\s]*(喜欢|偏好|习惯|倾向)[\s]*([^\s，。！？；]+)",
                        r"(我的|个人的)[\s]*([^\s，。！？；]+)(风格|方式|习惯)"
                    ],
                    weight=1.1
                )
            ]
        }

    def _load_domain_patterns(self) -> List[DomainPattern]:
        """加载领域模式"""
        return [
            DomainPattern(
                domain_name="软件开发",
                keywords=["开发", "编程", "代码", "软件", "程序", "系统"],
                indicators=["前端", "后端", "全栈", "移动", "web", "app", "API"],
                weight=1.5
            ),
            DomainPattern(
                domain_name="人工智能",
                keywords=["AI", "机器学习", "深度学习", "神经网络", "算法", "模型"],
                indicators=["ML", "DL", "CNN", "RNN", "BERT", "GPT", "训练", "预测"],
                weight=1.6
            ),
            DomainPattern(
                domain_name="数据分析",
                keywords=["数据", "分析", "统计", "可视化", "报表", "指标"],
                indicators=["数据库", "SQL", "pandas", "numpy", "可视化", "Dashboard"],
                weight=1.4
            ),
            DomainPattern(
                domain_name="产品设计",
                keywords=["产品", "设计", "用户体验", "UI", "UX", "交互"],
                indicators=["原型", "wireframe", "用户研究", "可用性", "界面"],
                weight=1.3
            ),
            DomainPattern(
                domain_name="市场营销",
                keywords=["营销", "推广", "品牌", "运营", "增长", "获客"],
                indicators=["SEO", "SEM", "社交媒体", "内容营销", "转化率"],
                weight=1.2
            ),
            DomainPattern(
                domain_name="教育培训",
                keywords=["教育", "培训", "学习", "教学", "课程", "知识"],
                indicators=["在线教育", "MOOC", "学习路径", "考试", "认证"],
                weight=1.1
            ),
            DomainPattern(
                domain_name="金融科技",
                keywords=["金融", "银行", "支付", "投资", "理财", "保险"],
                indicators=["fintech", "区块链", "数字货币", "风控", "合规"],
                weight=1.3
            ),
            DomainPattern(
                domain_name="医疗健康",
                keywords=["医疗", "健康", "医院", "诊断", "治疗", "药物"],
                indicators=["电子病历", "远程医疗", "医学影像", "基因", "生物信息"],
                weight=1.4
            )
        ]

    def _load_technical_keywords(self) -> Dict[str, float]:
        """加载技术关键词及其权重"""
        return {
            # 编程语言
            "Python": 1.5, "JavaScript": 1.5, "Java": 1.4, "C++": 1.4,
            "Go": 1.3, "TypeScript": 1.3, "PHP": 1.2, "Ruby": 1.2,

            # 框架和库
            "React": 1.4, "Vue": 1.4, "Angular": 1.4, "Django": 1.3,
            "Flask": 1.3, "Spring": 1.3, "Express": 1.2, "Laravel": 1.2,

            # 数据库
            "MySQL": 1.3, "PostgreSQL": 1.3, "MongoDB": 1.3, "Redis": 1.2,
            "Oracle": 1.2, "SQLite": 1.1,

            # 云平台
            "AWS": 1.4, "Azure": 1.4, "GCP": 1.4, "阿里云": 1.3, "腾讯云": 1.3,

            # 工具
            "Docker": 1.3, "Kubernetes": 1.3, "Git": 1.2, "Jenkins": 1.2,

            # AI/ML
            "TensorFlow": 1.5, "PyTorch": 1.5, "Keras": 1.4, "Scikit-learn": 1.3,
        }

    def _load_constraint_indicators(self) -> List[str]:
        """加载约束指示词"""
        return [
            "不能", "不要", "禁止", "避免", "限制", "约束", "要求",
            "必须", "一定要", "需要", "应该", "不得", "不可",
            "长度", "字数", "时间", "格式", "风格", "语调"
        ]

    def _load_example_indicators(self) -> List[str]:
        """加载示例指示词"""
        return [
            "例如", "比如", "举例", "示例", "样例", "像", "参考",
            "例子", "案例", "实例", "模板", "样本"
        ]

    def extract_contexts(self, text: str) -> List[ExtractedContext]:
        """
        从文本中提取所有上下文信息

        Args:
            text: 输入文本

        Returns:
            List[ExtractedContext]: 提取的上下文列表
        """
        if not text or len(text.strip()) < 5:
            return []

        contexts = []
        processed_text = self._preprocess_text(text)

        # 提取各种类型的上下文
        for context_type, patterns in self.context_patterns.items():
            extracted = self._extract_context_by_type(processed_text, context_type, patterns)
            contexts.extend(extracted)

        # 去重和合并相似的上下文
        contexts = self._deduplicate_contexts(contexts)

        # 计算重要性分数
        contexts = self._calculate_importance(contexts, processed_text)

        # 按重要性排序
        contexts.sort(key=lambda x: x.importance, reverse=True)

        return contexts

    def extract_domain_info(self, text: str) -> Optional[DomainInfo]:
        """
        提取领域信息

        Args:
            text: 输入文本

        Returns:
            Optional[DomainInfo]: 识别的领域信息
        """
        processed_text = self._preprocess_text(text)
        domain_scores = defaultdict(float)
        domain_keywords = defaultdict(list)

        for domain_pattern in self.domain_patterns:
            score = 0.0

            # 关键词匹配
            for keyword in domain_pattern.keywords:
                if keyword in processed_text:
                    score += domain_pattern.weight * 1.0
                    domain_keywords[domain_pattern.domain_name].append(keyword)

            # 指示词匹配
            for indicator in domain_pattern.indicators:
                if indicator.lower() in processed_text:
                    score += domain_pattern.weight * 1.5
                    domain_keywords[domain_pattern.domain_name].append(indicator)

            if score > 0:
                domain_scores[domain_pattern.domain_name] = score

        if not domain_scores:
            return None

        # 选择得分最高的领域
        best_domain = max(domain_scores, key=domain_scores.get)
        max_score = domain_scores[best_domain]

        # 计算置信度
        total_score = sum(domain_scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0

        return DomainInfo(
            name=best_domain,
            confidence=min(confidence, 1.0),
            keywords=list(set(domain_keywords[best_domain])),
            subcategory=self._detect_subcategory(best_domain, processed_text)
        )

    def extract_technical_requirements(self, text: str) -> List[TechnicalRequirement]:
        """
        提取技术要求

        Args:
            text: 输入文本

        Returns:
            List[TechnicalRequirement]: 技术要求列表
        """
        requirements = []
        processed_text = self._preprocess_text(text)

        # 提取技术栈要求
        tech_requirements = self._extract_tech_stack_requirements(processed_text)
        requirements.extend(tech_requirements)

        # 提取性能要求
        performance_requirements = self._extract_performance_requirements(processed_text)
        requirements.extend(performance_requirements)

        # 提取格式要求
        format_requirements = self._extract_format_requirements(processed_text)
        requirements.extend(format_requirements)

        return requirements

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转换为小写并移除多余空白
        processed = re.sub(r'\\s+', ' ', text.lower().strip())

        # 保留中文、英文、数字和基本标点
        processed = re.sub(r'[^\\u4e00-\\u9fff\\w\\s.,!?;:()\\-+=/]', ' ', processed)

        return processed

    def _extract_context_by_type(self, text: str, context_type: ContextType,
                                patterns: List[ContextPattern]) -> List[ExtractedContext]:
        """按类型提取上下文"""
        contexts = []

        for pattern in patterns:
            # 关键词匹配
            for keyword in pattern.keywords:
                if keyword in text:
                    context_matches = self._find_context_around_keyword(text, keyword)
                    for match, position in context_matches:
                        contexts.append(ExtractedContext(
                            context_type=context_type,
                            content=match,
                            importance=pattern.weight * 0.5,
                            source_position=position,
                            related_keywords=[keyword]
                        ))

            # 正则表达式匹配
            for regex_pattern in pattern.patterns:
                matches = re.finditer(regex_pattern, text)
                for match in matches:
                    content = match.group(0).strip()
                    if len(content) > 2:  # 过滤太短的匹配
                        contexts.append(ExtractedContext(
                            context_type=context_type,
                            content=content,
                            importance=pattern.weight * 0.8,
                            source_position=match.start(),
                            related_keywords=self._extract_keywords_from_match(content)
                        ))

        return contexts

    def _find_context_around_keyword(self, text: str, keyword: str,
                                   window_size: int = 20) -> List[Tuple[str, int]]:
        """在关键词周围寻找上下文"""
        matches = []
        start = 0

        while True:
            pos = text.find(keyword, start)
            if pos == -1:
                break

            # 提取关键词前后的文本
            start_pos = max(0, pos - window_size)
            end_pos = min(len(text), pos + len(keyword) + window_size)
            context = text[start_pos:end_pos].strip()

            if context and len(context) > len(keyword) + 5:
                matches.append((context, pos))

            start = pos + 1

        return matches

    def _extract_keywords_from_match(self, text: str) -> List[str]:
        """从匹配的文本中提取关键词"""
        # 简化的关键词提取
        keywords = []
        for tech, weight in self.technical_keywords.items():
            if tech.lower() in text.lower():
                keywords.append(tech)

        return keywords

    def _deduplicate_contexts(self, contexts: List[ExtractedContext]) -> List[ExtractedContext]:
        """去重上下文"""
        unique_contexts = []
        seen_contents = set()

        for context in contexts:
            # 简化内容用于比较
            simplified = re.sub(r'\\s+', ' ', context.content.lower().strip())

            if simplified not in seen_contents and len(simplified) > 3:
                seen_contents.add(simplified)
                unique_contexts.append(context)

        return unique_contexts

    def _calculate_importance(self, contexts: List[ExtractedContext],
                            original_text: str) -> List[ExtractedContext]:
        """计算上下文重要性"""
        text_length = len(original_text)

        for context in contexts:
            # 基础重要性
            base_importance = context.importance

            # 长度因子
            length_factor = min(1.0, len(context.content) / 50)

            # 位置因子（开头的内容通常更重要）
            position_factor = 1.0 - (context.source_position / text_length) * 0.3

            # 关键词密度因子
            keyword_factor = len(context.related_keywords) * 0.1

            # 最终重要性
            final_importance = min(1.0, base_importance * (1 + length_factor + position_factor + keyword_factor))
            context.importance = final_importance

        return contexts

    def _detect_subcategory(self, domain: str, text: str) -> Optional[str]:
        """检测子类别"""
        subcategories = {
            "软件开发": {
                "前端开发": ["前端", "前端开发", "UI", "用户界面", "React", "Vue", "Angular"],
                "后端开发": ["后端", "后端开发", "API", "服务器", "数据库", "微服务"],
                "移动开发": ["移动", "移动开发", "app", "Android", "iOS", "React Native"],
                "全栈开发": ["全栈", "全栈开发", "前后端"]
            },
            "人工智能": {
                "机器学习": ["机器学习", "ML", "算法", "模型训练"],
                "深度学习": ["深度学习", "DL", "神经网络", "CNN", "RNN"],
                "自然语言处理": ["NLP", "自然语言", "文本处理", "语言模型"],
                "计算机视觉": ["计算机视觉", "图像", "视觉", "图片识别"]
            }
        }

        if domain in subcategories:
            for subcategory, keywords in subcategories[domain].items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        return subcategory

        return None

    def _extract_tech_stack_requirements(self, text: str) -> List[TechnicalRequirement]:
        """提取技术栈要求"""
        requirements = []

        # 检测编程语言要求
        for tech, weight in self.technical_keywords.items():
            if tech.lower() in text:
                requirements.append(TechnicalRequirement(
                    requirement_type="technology",
                    description=f"使用 {tech}",
                    priority=int(weight * 3),
                    examples=[tech]
                ))

        return requirements

    def _extract_performance_requirements(self, text: str) -> List[TechnicalRequirement]:
        """提取性能要求"""
        requirements = []

        performance_patterns = [
            (r"(快速|高效|性能|速度)", "performance", "性能要求"),
            (r"(实时|即时|立即)", "realtime", "实时性要求"),
            (r"(稳定|可靠|健壮)", "reliability", "稳定性要求"),
            (r"(扩展|伸缩|可扩展)", "scalability", "扩展性要求")
        ]

        for pattern, req_type, description in performance_patterns:
            if re.search(pattern, text):
                requirements.append(TechnicalRequirement(
                    requirement_type=req_type,
                    description=description,
                    priority=3
                ))

        return requirements

    def _extract_format_requirements(self, text: str) -> List[TechnicalRequirement]:
        """提取格式要求"""
        requirements = []

        format_patterns = [
            (r"JSON", "json_format", "JSON格式输出"),
            (r"XML", "xml_format", "XML格式输出"),
            (r"表格|table", "table_format", "表格格式输出"),
            (r"列表|list", "list_format", "列表格式输出"),
            (r"markdown|md", "markdown_format", "Markdown格式输出")
        ]

        for pattern, req_type, description in format_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                requirements.append(TechnicalRequirement(
                    requirement_type=req_type,
                    description=description,
                    priority=2
                ))

        return requirements

    def get_extraction_summary(self, contexts: List[ExtractedContext]) -> Dict[str, Any]:
        """获取提取摘要"""
        if not contexts:
            return {"total": 0}

        # 按类型统计
        type_counts = defaultdict(int)
        total_importance = 0.0

        for context in contexts:
            type_counts[context.context_type.value] += 1
            total_importance += context.importance

        return {
            "total": len(contexts),
            "type_distribution": dict(type_counts),
            "average_importance": total_importance / len(contexts) if contexts else 0.0,
            "high_importance_count": sum(1 for ctx in contexts if ctx.importance >= 0.7),
            "unique_keywords": len(set().union(*[ctx.related_keywords for ctx in contexts]))
        }