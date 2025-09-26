"""
模板匹配器

实现提示词模板匹配和推荐功能，包括语义相似性计算、
模板评分和适配建议等。
"""

import re
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple, Set
from pathlib import Path
import difflib
from collections import Counter
import math

from ..schemas.prompts import (
    PromptTemplate, TemplateMatch, TemplateSearchCriteria,
    TemplateCategory, OptimizationStrategy, TemplateNotFoundError
)
from ..schemas.requirements import ParsedRequirements
from ..types import PromptType, ComplexityLevel

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """
    模板匹配器

    负责从模板库中找到最匹配的提示词模板，
    提供语义相似性计算和模板推荐功能。
    """

    def __init__(self, template_file_path: Optional[str] = None):
        """
        初始化模板匹配器

        Args:
            template_file_path: 模板文件路径，如果为None则使用默认路径
        """
        self.template_file_path = template_file_path or self._get_default_template_path()
        self.templates: List[PromptTemplate] = []
        self.template_index: Dict[str, PromptTemplate] = {}

        # 停用词列表（用于文本相似性计算）
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没',
            '看', '好', '自己', '这', '那', '什么', '可以', '但是', '如果', '因为',
            '所以', '请', '或者', '还是', '以及', '以便', '为了', '由于'
        }

        # 领域关键词词典
        self.domain_keywords = {
            TemplateCategory.CREATIVE_WRITING: {
                '写作', '创作', '文章', '故事', '小说', '诗歌', '剧本', '创意',
                '想象', '情节', '人物', '描述', '叙述', '风格', '文学'
            },
            TemplateCategory.TECHNICAL_ANALYSIS: {
                '分析', '技术', '系统', '算法', '架构', '设计', '实现', '优化',
                '性能', '评估', '测试', '调试', '代码', '程序', '开发'
            },
            TemplateCategory.BUSINESS_STRATEGY: {
                '商业', '战略', '市场', '营销', '销售', '客户', '产品', '服务',
                '竞争', '分析', '规划', '管理', '运营', '财务', '投资'
            },
            TemplateCategory.EDUCATIONAL: {
                '教育', '教学', '学习', '课程', '培训', '知识', '技能', '理解',
                '解释', '说明', '指导', '练习', '作业', '考试', '评价'
            },
            TemplateCategory.RESEARCH: {
                '研究', '调查', '实验', '数据', '统计', '分析', '假设', '理论',
                '方法', '结果', '结论', '文献', '综述', '论文', '报告'
            },
            TemplateCategory.CODING: {
                '编程', '代码', '函数', '变量', '算法', '数据结构', '调试',
                '测试', '重构', '优化', '架构', 'API', '接口', '库', '框架'
            },
            TemplateCategory.MARKETING: {
                '营销', '推广', '广告', '品牌', '宣传', '传播', '媒体', '内容',
                '用户', '客户', '转化', '渠道', '策略', '活动', '效果'
            },
            TemplateCategory.DATA_ANALYSIS: {
                '数据', '分析', '统计', '图表', '趋势', '模式', '预测', '挖掘',
                '可视化', '报表', '指标', 'KPI', '洞察', '建模', '算法'
            },
            TemplateCategory.ROLE_PLAYING: {
                '角色', '扮演', '情景', '模拟', '对话', '互动', '场景', '人物',
                '身份', '背景', '设定', '剧情', '演示', '表演', '体验'
            }
        }

        # 初始化时加载模板
        asyncio.create_task(self._load_templates())

        logger.info(f"模板匹配器已初始化，模板文件路径: {self.template_file_path}")

    def _get_default_template_path(self) -> str:
        """获取默认模板文件路径"""
        current_dir = Path(__file__).parent.parent
        return str(current_dir / "templates" / "prompt_templates.json")

    async def _load_templates(self) -> None:
        """加载模板文件"""
        try:
            template_path = Path(self.template_file_path)
            if not template_path.exists():
                logger.warning(f"模板文件不存在: {self.template_file_path}")
                self.templates = []
                return

            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            self.templates = []
            self.template_index = {}

            for template_dict in template_data.get('templates', []):
                try:
                    template = PromptTemplate(**template_dict)
                    self.templates.append(template)
                    self.template_index[template.template_id] = template
                except Exception as e:
                    logger.warning(f"解析模板失败: {e}, 数据: {template_dict}")
                    continue

            logger.info(f"成功加载 {len(self.templates)} 个模板")

        except Exception as e:
            logger.error(f"加载模板文件失败: {e}", exc_info=True)
            self.templates = []
            self.template_index = {}

    async def find_matching_templates(
        self,
        prompt: str,
        requirements: Optional[ParsedRequirements] = None,
        criteria: Optional[TemplateSearchCriteria] = None,
        max_results: int = 5
    ) -> List[TemplateMatch]:
        """
        查找匹配的模板

        Args:
            prompt: 输入提示词
            requirements: 解析后的需求（可选）
            criteria: 搜索条件（可选）
            max_results: 最大返回结果数

        Returns:
            匹配的模板列表
        """
        try:
            if not self.templates:
                await self._load_templates()

            if not self.templates:
                logger.warning("没有可用的模板")
                return []

            # 预过滤模板
            candidate_templates = await self._filter_templates(criteria)

            if not candidate_templates:
                logger.warning("没有符合条件的候选模板")
                return []

            # 计算相似性并生成匹配结果
            matches = []
            for template in candidate_templates:
                similarity_score = await self._calculate_similarity(
                    prompt, template, requirements
                )

                if similarity_score > 0.1:  # 最低相似性阈值
                    matching_features = await self._identify_matching_features(
                        prompt, template, requirements
                    )

                    adaptation_needed, adaptation_suggestions = await self._analyze_adaptation_needs(
                        prompt, template, requirements
                    )

                    match = TemplateMatch(
                        template=template,
                        similarity_score=similarity_score,
                        matching_features=matching_features,
                        adaptation_needed=adaptation_needed,
                        adaptation_suggestions=adaptation_suggestions
                    )
                    matches.append(match)

            # 按相似性得分排序
            matches.sort(key=lambda x: x.similarity_score, reverse=True)

            return matches[:max_results]

        except Exception as e:
            logger.error(f"查找匹配模板时发生错误: {e}", exc_info=True)
            return []

    async def search_templates(
        self, criteria: TemplateSearchCriteria
    ) -> List[PromptTemplate]:
        """
        搜索模板

        Args:
            criteria: 搜索条件

        Returns:
            匹配的模板列表
        """
        try:
            if not self.templates:
                await self._load_templates()

            # 过滤模板
            filtered_templates = await self._filter_templates(criteria)

            # 如果有查询文本，计算相关性得分
            if criteria.query:
                scored_templates = []
                for template in filtered_templates:
                    relevance_score = await self._calculate_query_relevance(
                        criteria.query, template
                    )
                    scored_templates.append((template, relevance_score))

                # 按相关性排序
                scored_templates.sort(key=lambda x: x[1], reverse=True)
                filtered_templates = [t[0] for t[1] in scored_templates]

            # 应用分页
            start_idx = criteria.offset
            end_idx = start_idx + criteria.limit
            return filtered_templates[start_idx:end_idx]

        except Exception as e:
            logger.error(f"搜索模板时发生错误: {e}", exc_info=True)
            return []

    async def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """
        根据ID获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果不存在则返回None
        """
        if not self.template_index:
            await self._load_templates()

        return self.template_index.get(template_id)

    async def recommend_templates_for_requirements(
        self,
        requirements: ParsedRequirements,
        max_results: int = 3
    ) -> List[TemplateMatch]:
        """
        基于需求推荐模板

        Args:
            requirements: 解析后的需求
            max_results: 最大返回结果数

        Returns:
            推荐的模板列表
        """
        try:
            # 构建搜索条件
            criteria = TemplateSearchCriteria(
                categories=[self._infer_category_from_requirements(requirements)],
                prompt_types=[requirements.suggested_prompt_type],
                complexity_levels=[requirements.complexity_estimate],
                limit=max_results * 2  # 获取更多候选项
            )

            # 构建伪查询文本用于匹配
            query_parts = [requirements.main_objective]
            query_parts.extend(requirements.key_requirements)
            query_text = " ".join(query_parts)

            # 查找匹配的模板
            matches = await self.find_matching_templates(
                query_text, requirements, criteria, max_results
            )

            return matches

        except Exception as e:
            logger.error(f"推荐模板时发生错误: {e}", exc_info=True)
            return []

    # 私有方法 - 过滤和搜索
    async def _filter_templates(
        self, criteria: Optional[TemplateSearchCriteria]
    ) -> List[PromptTemplate]:
        """根据条件过滤模板"""
        if not criteria:
            return [t for t in self.templates if t.is_active]

        filtered = []
        for template in self.templates:
            # 基本活跃状态检查
            if not template.is_active and criteria.is_active:
                continue

            # 类别过滤
            if criteria.categories and template.category not in criteria.categories:
                continue

            # 提示词类型过滤
            if criteria.prompt_types and template.prompt_type not in criteria.prompt_types:
                continue

            # 复杂度过滤
            if criteria.complexity_levels and template.complexity not in criteria.complexity_levels:
                continue

            # 标签过滤
            if criteria.tags:
                template_tags_set = set(template.tags)
                criteria_tags_set = set(criteria.tags)
                if not criteria_tags_set.intersection(template_tags_set):
                    continue

            # 评分过滤
            if template.rating < criteria.min_rating:
                continue

            # 成功率过滤
            if template.success_rate < criteria.min_success_rate:
                continue

            filtered.append(template)

        return filtered

    async def _calculate_similarity(
        self,
        prompt: str,
        template: PromptTemplate,
        requirements: Optional[ParsedRequirements]
    ) -> float:
        """计算提示词与模板的相似性"""
        # 文本相似性 (40%)
        text_similarity = await self._calculate_text_similarity(
            prompt, template.template_content
        )

        # 结构相似性 (25%)
        structure_similarity = await self._calculate_structure_similarity(
            prompt, template.template_content
        )

        # 领域相似性 (20%)
        domain_similarity = await self._calculate_domain_similarity(
            prompt, template, requirements
        )

        # 用途相似性 (15%)
        use_case_similarity = await self._calculate_use_case_similarity(
            prompt, template.use_cases
        )

        # 综合相似性计算
        total_similarity = (
            text_similarity * 0.4 +
            structure_similarity * 0.25 +
            domain_similarity * 0.2 +
            use_case_similarity * 0.15
        )

        return min(total_similarity, 1.0)

    async def _calculate_text_similarity(
        self, text1: str, text2: str
    ) -> float:
        """计算文本相似性"""
        # 预处理文本
        words1 = self._preprocess_text(text1)
        words2 = self._preprocess_text(text2)

        # 使用Jaccard相似性
        jaccard_sim = self._jaccard_similarity(words1, words2)

        # 使用序列匹配
        sequence_sim = difflib.SequenceMatcher(None, text1, text2).ratio()

        # 综合相似性
        return (jaccard_sim * 0.7 + sequence_sim * 0.3)

    async def _calculate_structure_similarity(
        self, prompt: str, template_content: str
    ) -> float:
        """计算结构相似性"""
        prompt_features = self._extract_structure_features(prompt)
        template_features = self._extract_structure_features(template_content)

        # 计算特征重叠度
        total_features = set(prompt_features.keys()) | set(template_features.keys())
        if not total_features:
            return 0.0

        similarity_score = 0.0
        for feature in total_features:
            prompt_value = prompt_features.get(feature, 0)
            template_value = template_features.get(feature, 0)

            # 计算特征相似性
            if prompt_value == template_value == 0:
                feature_sim = 1.0  # 两者都没有该特征
            elif prompt_value == 0 or template_value == 0:
                feature_sim = 0.0  # 一个有一个没有
            else:
                feature_sim = min(prompt_value, template_value) / max(prompt_value, template_value)

            similarity_score += feature_sim

        return similarity_score / len(total_features)

    async def _calculate_domain_similarity(
        self,
        prompt: str,
        template: PromptTemplate,
        requirements: Optional[ParsedRequirements]
    ) -> float:
        """计算领域相似性"""
        # 从提示词中提取领域关键词
        prompt_domain_scores = {}
        for category, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in prompt)
            if score > 0:
                prompt_domain_scores[category] = score

        # 如果没有检测到明确领域，使用需求信息
        if not prompt_domain_scores and requirements and requirements.domain_info:
            domain_name = requirements.domain_info.name.lower()
            for category, keywords in self.domain_keywords.items():
                if any(keyword in domain_name for keyword in keywords):
                    prompt_domain_scores[category] = 1

        # 计算与模板类别的相似性
        if not prompt_domain_scores:
            return 0.3  # 默认中等相似性

        template_category = template.category
        prompt_score = prompt_domain_scores.get(template_category, 0)
        max_prompt_score = max(prompt_domain_scores.values())

        if max_prompt_score == 0:
            return 0.3

        return prompt_score / max_prompt_score

    async def _calculate_use_case_similarity(
        self, prompt: str, use_cases: List[str]
    ) -> float:
        """计算用途相似性"""
        if not use_cases:
            return 0.5  # 默认中等相似性

        max_similarity = 0.0
        prompt_words = self._preprocess_text(prompt)

        for use_case in use_cases:
            use_case_words = self._preprocess_text(use_case)
            similarity = self._jaccard_similarity(prompt_words, use_case_words)
            max_similarity = max(max_similarity, similarity)

        return max_similarity

    async def _calculate_query_relevance(
        self, query: str, template: PromptTemplate
    ) -> float:
        """计算查询与模板的相关性"""
        query_words = self._preprocess_text(query)

        # 检查名称相关性
        name_words = self._preprocess_text(template.name)
        name_relevance = self._jaccard_similarity(query_words, name_words)

        # 检查描述相关性
        desc_words = self._preprocess_text(template.description)
        desc_relevance = self._jaccard_similarity(query_words, desc_words)

        # 检查标签相关性
        tag_relevance = 0.0
        if template.tags:
            tag_text = " ".join(template.tags)
            tag_words = self._preprocess_text(tag_text)
            tag_relevance = self._jaccard_similarity(query_words, tag_words)

        # 综合相关性
        return (name_relevance * 0.4 + desc_relevance * 0.4 + tag_relevance * 0.2)

    # 私有方法 - 特征提取和分析
    def _preprocess_text(self, text: str) -> Set[str]:
        """预处理文本，提取有效词汇"""
        # 转小写并分词
        words = re.findall(r'[\u4e00-\u9fff]+|\w+', text.lower())

        # 移除停用词和短词
        filtered_words = {
            word for word in words
            if len(word) > 1 and word not in self.stop_words
        }

        return filtered_words

    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """计算Jaccard相似性"""
        if not set1 and not set2:
            return 1.0

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _extract_structure_features(self, text: str) -> Dict[str, int]:
        """提取结构特征"""
        features = {}

        # 句子数量
        sentences = re.split(r'[。！？.!?]+', text)
        features['sentence_count'] = len([s for s in sentences if s.strip()])

        # 段落数量
        features['paragraph_count'] = len(text.split('\n\n'))

        # 列表项数量
        features['list_items'] = len(re.findall(r'[•·\-\*]\s', text))

        # 编号项数量
        features['numbered_items'] = len(re.findall(r'\d+\.\s', text))

        # 标题数量
        features['headings'] = len(re.findall(r'^\s*#+\s', text, re.MULTILINE))

        # 指令数量
        features['instructions'] = len(re.findall(r'请.*?[。！？\n]', text))

        # 示例数量
        features['examples'] = len(re.findall(r'例如|比如|示例', text))

        # 约束数量
        features['constraints'] = len(re.findall(r'不要|避免|禁止', text))

        # 变量数量（模板特有）
        features['variables'] = len(re.findall(r'\{[^}]+\}', text))

        return features

    async def _identify_matching_features(
        self,
        prompt: str,
        template: PromptTemplate,
        requirements: Optional[ParsedRequirements]
    ) -> List[str]:
        """识别匹配的特征"""
        features = []

        # 文本相似性特征
        prompt_words = self._preprocess_text(prompt)
        template_words = self._preprocess_text(template.template_content)
        common_words = prompt_words & template_words

        if len(common_words) > 5:
            features.append(f"共同关键词: {len(common_words)}个")

        # 结构特征
        prompt_structure = self._extract_structure_features(prompt)
        template_structure = self._extract_structure_features(template.template_content)

        for feature_name, prompt_value in prompt_structure.items():
            template_value = template_structure.get(feature_name, 0)
            if prompt_value > 0 and template_value > 0:
                features.append(f"结构相似: {feature_name}")

        # 领域特征
        template_keywords = self.domain_keywords.get(template.category, set())
        matching_domain_keywords = [kw for kw in template_keywords if kw in prompt]
        if matching_domain_keywords:
            features.append(f"领域匹配: {', '.join(matching_domain_keywords[:3])}")

        # 用途特征
        for use_case in template.use_cases:
            use_case_words = self._preprocess_text(use_case)
            if len(prompt_words & use_case_words) > 2:
                features.append(f"用途匹配: {use_case}")
                break

        return features

    async def _analyze_adaptation_needs(
        self,
        prompt: str,
        template: PromptTemplate,
        requirements: Optional[ParsedRequirements]
    ) -> Tuple[bool, List[str]]:
        """分析适配需求"""
        suggestions = []
        adaptation_needed = False

        # 检查变量替换需求
        template_variables = re.findall(r'\{([^}]+)\}', template.template_content)
        if template_variables:
            adaptation_needed = True
            suggestions.append(f"需要替换变量: {', '.join(template_variables)}")

        # 检查长度适配
        prompt_length = len(prompt)
        template_length = len(template.template_content)
        length_ratio = prompt_length / max(template_length, 1)

        if length_ratio < 0.5:
            suggestions.append("建议增加更多详细信息")
        elif length_ratio > 2.0:
            suggestions.append("建议简化和精炼内容")

        # 检查复杂度适配
        if requirements:
            req_complexity = requirements.complexity_estimate
            template_complexity = template.complexity

            if req_complexity != template_complexity:
                if req_complexity.value == "simple" and template_complexity.value != "simple":
                    suggestions.append("建议简化模板内容以匹配简单复杂度")
                elif req_complexity.value == "complex" and template_complexity.value == "simple":
                    suggestions.append("建议增加更多详细要求和说明")

        # 检查结构适配
        prompt_structure = self._extract_structure_features(prompt)
        template_structure = self._extract_structure_features(template.template_content)

        if template_structure.get('examples', 0) > 0 and prompt_structure.get('examples', 0) == 0:
            suggestions.append("建议在提示词中添加具体示例")

        if template_structure.get('constraints', 0) > 0 and prompt_structure.get('constraints', 0) == 0:
            suggestions.append("建议添加必要的约束条件")

        # 如果有建议，则需要适配
        if suggestions:
            adaptation_needed = True

        return adaptation_needed, suggestions

    def _infer_category_from_requirements(
        self, requirements: ParsedRequirements
    ) -> TemplateCategory:
        """从需求推断模板类别"""
        main_objective = requirements.main_objective.lower()

        # 基于主要目标的关键词匹配
        category_patterns = {
            TemplateCategory.CREATIVE_WRITING: ['写', '创作', '编写', '文章', '故事'],
            TemplateCategory.TECHNICAL_ANALYSIS: ['分析', '技术', '系统', '架构'],
            TemplateCategory.BUSINESS_STRATEGY: ['商业', '战略', '市场', '营销'],
            TemplateCategory.EDUCATIONAL: ['教育', '教学', '学习', '培训'],
            TemplateCategory.RESEARCH: ['研究', '调查', '实验', '数据'],
            TemplateCategory.CODING: ['编程', '代码', '开发', '程序'],
            TemplateCategory.MARKETING: ['营销', '推广', '广告', '品牌'],
            TemplateCategory.DATA_ANALYSIS: ['数据', '统计', '分析', '图表'],
            TemplateCategory.ROLE_PLAYING: ['角色', '扮演', '模拟', '对话']
        }

        best_match = TemplateCategory.GENERAL_PURPOSE
        max_matches = 0

        for category, patterns in category_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in main_objective)
            if matches > max_matches:
                max_matches = matches
                best_match = category

        return best_match