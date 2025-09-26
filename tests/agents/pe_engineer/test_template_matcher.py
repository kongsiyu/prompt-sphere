"""
测试模板匹配器

验证TemplateMatcher类的各项功能，包括：
- 模板加载和解析
- 相似性计算
- 模板匹配和推荐
- 搜索功能
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from backend.app.agents.pe_engineer.optimizers.template_matcher import TemplateMatcher
from backend.app.agents.pe_engineer.schemas.prompts import (
    PromptTemplate, TemplateSearchCriteria, TemplateCategory,
    OptimizationStrategy
)
from backend.app.agents.pe_engineer.schemas.requirements import (
    ParsedRequirements, ParsedIntent, IntentCategory, DomainInfo
)
from backend.app.agents.pe_engineer.types import PromptType, ComplexityLevel


@pytest.fixture
def sample_templates_data():
    """示例模板数据"""
    return {
        "templates": [
            {
                "template_id": "test_001",
                "name": "通用写作模板",
                "category": "general_purpose",
                "description": "用于通用写作任务的基础模板",
                "template_content": "请写一篇关于{topic}的{content_type}，要求{requirements}。",
                "variables": ["topic", "content_type", "requirements"],
                "example_values": {
                    "topic": "人工智能",
                    "content_type": "文章",
                    "requirements": "内容准确、逻辑清晰"
                },
                "use_cases": ["文章写作", "报告撰写"],
                "tags": ["通用", "写作"],
                "complexity": "simple",
                "prompt_type": "general",
                "success_rate": 0.8,
                "usage_count": 100,
                "rating": 4.0,
                "is_active": True
            },
            {
                "template_id": "test_002",
                "name": "技术分析模板",
                "category": "technical_analysis",
                "description": "用于技术分析任务的专业模板",
                "template_content": "作为技术专家，请分析{system}的{aspect}，包括{analysis_points}。",
                "variables": ["system", "aspect", "analysis_points"],
                "example_values": {
                    "system": "分布式系统",
                    "aspect": "性能特征",
                    "analysis_points": "吞吐量、延迟、可扩展性"
                },
                "use_cases": ["系统分析", "技术评估"],
                "tags": ["技术", "分析"],
                "complexity": "complex",
                "prompt_type": "analytical",
                "success_rate": 0.75,
                "usage_count": 50,
                "rating": 4.2,
                "is_active": True
            },
            {
                "template_id": "test_003",
                "name": "创意写作模板",
                "category": "creative_writing",
                "description": "用于创意写作的模板",
                "template_content": "创作一个{genre}故事，主题是{theme}，包含{elements}。",
                "variables": ["genre", "theme", "elements"],
                "example_values": {
                    "genre": "科幻",
                    "theme": "时间旅行",
                    "elements": "冲突、转折、结局"
                },
                "use_cases": ["小说创作", "剧本写作"],
                "tags": ["创意", "故事"],
                "complexity": "intermediate",
                "prompt_type": "creative",
                "success_rate": 0.7,
                "usage_count": 30,
                "rating": 4.5,
                "is_active": True
            }
        ]
    }


@pytest.fixture
def temp_template_file(sample_templates_data):
    """创建临时模板文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_templates_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    yield temp_path

    # 清理
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def template_matcher(temp_template_file):
    """创建模板匹配器实例"""
    return TemplateMatcher(temp_template_file)


@pytest.fixture
def sample_requirements():
    """示例需求"""
    intent = ParsedIntent(
        category=IntentCategory.CREATE_PROMPT,
        confidence=0.9
    )

    domain_info = DomainInfo(
        name="技术分析",
        confidence=0.8,
        keywords=["技术", "分析", "系统"]
    )

    return ParsedRequirements(
        original_input="分析一个分布式系统的性能",
        intent=intent,
        main_objective="进行技术系统分析",
        key_requirements=["性能评估", "架构分析"],
        domain_info=domain_info
    )


class TestTemplateMatcher:
    """模板匹配器测试类"""

    def test_init_default_path(self):
        """测试默认路径初始化"""
        matcher = TemplateMatcher()
        assert matcher.template_file_path.endswith("prompt_templates.json")
        assert matcher.templates == []  # 文件可能不存在，模板为空

    def test_init_custom_path(self, temp_template_file):
        """测试自定义路径初始化"""
        matcher = TemplateMatcher(temp_template_file)
        assert matcher.template_file_path == temp_template_file

    @pytest.mark.asyncio
    async def test_load_templates_success(self, template_matcher):
        """测试成功加载模板"""
        await template_matcher._load_templates()

        assert len(template_matcher.templates) == 3
        assert len(template_matcher.template_index) == 3

        # 验证模板内容
        template = template_matcher.templates[0]
        assert template.template_id == "test_001"
        assert template.name == "通用写作模板"
        assert template.category == TemplateCategory.GENERAL_PURPOSE

    @pytest.mark.asyncio
    async def test_load_templates_file_not_exists(self):
        """测试文件不存在的情况"""
        matcher = TemplateMatcher("/non/existent/path.json")
        await matcher._load_templates()

        assert len(matcher.templates) == 0
        assert len(matcher.template_index) == 0

    @pytest.mark.asyncio
    async def test_find_matching_templates_basic(self, template_matcher):
        """测试基本模板匹配"""
        prompt = "请写一篇关于人工智能的技术文章"

        matches = await template_matcher.find_matching_templates(prompt)

        assert len(matches) > 0
        assert all(match.similarity_score >= 0 for match in matches)
        assert all(match.similarity_score <= 1 for match in matches)

        # 结果应该按相似度排序
        scores = [match.similarity_score for match in matches]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_find_matching_templates_with_requirements(self, template_matcher, sample_requirements):
        """测试带需求的模板匹配"""
        prompt = "分析分布式系统的性能特征"

        matches = await template_matcher.find_matching_templates(
            prompt, requirements=sample_requirements
        )

        assert len(matches) > 0

        # 技术分析模板应该排在前面
        best_match = matches[0]
        assert best_match.template.category == TemplateCategory.TECHNICAL_ANALYSIS

    @pytest.mark.asyncio
    async def test_find_matching_templates_with_criteria(self, template_matcher):
        """测试带搜索条件的模板匹配"""
        prompt = "创作一个科幻故事"
        criteria = TemplateSearchCriteria(
            categories=[TemplateCategory.CREATIVE_WRITING],
            complexity_levels=[ComplexityLevel.INTERMEDIATE]
        )

        matches = await template_matcher.find_matching_templates(
            prompt, criteria=criteria
        )

        assert len(matches) > 0
        assert all(match.template.category == TemplateCategory.CREATIVE_WRITING for match in matches)

    @pytest.mark.asyncio
    async def test_search_templates_by_category(self, template_matcher):
        """测试按类别搜索模板"""
        criteria = TemplateSearchCriteria(
            categories=[TemplateCategory.TECHNICAL_ANALYSIS]
        )

        templates = await template_matcher.search_templates(criteria)

        assert len(templates) == 1
        assert templates[0].category == TemplateCategory.TECHNICAL_ANALYSIS

    @pytest.mark.asyncio
    async def test_search_templates_by_query(self, template_matcher):
        """测试按查询文本搜索模板"""
        criteria = TemplateSearchCriteria(
            query="技术分析"
        )

        templates = await template_matcher.search_templates(criteria)

        assert len(templates) > 0
        # 技术分析模板应该排在前面
        assert any("技术" in template.name or "技术" in template.description for template in templates)

    @pytest.mark.asyncio
    async def test_search_templates_with_pagination(self, template_matcher):
        """测试分页搜索"""
        criteria = TemplateSearchCriteria(
            limit=2,
            offset=0
        )

        page1 = await template_matcher.search_templates(criteria)

        criteria.offset = 2
        page2 = await template_matcher.search_templates(criteria)

        assert len(page1) == 2
        assert len(page2) == 1  # 总共3个模板，第二页应该只有1个
        assert page1[0].template_id != page2[0].template_id

    @pytest.mark.asyncio
    async def test_search_templates_by_rating(self, template_matcher):
        """测试按评分搜索"""
        criteria = TemplateSearchCriteria(
            min_rating=4.3
        )

        templates = await template_matcher.search_templates(criteria)

        assert all(template.rating >= 4.3 for template in templates)

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(self, template_matcher):
        """测试成功获取模板"""
        template = await template_matcher.get_template_by_id("test_001")

        assert template is not None
        assert template.template_id == "test_001"
        assert template.name == "通用写作模板"

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, template_matcher):
        """测试获取不存在的模板"""
        template = await template_matcher.get_template_by_id("non_existent")

        assert template is None

    @pytest.mark.asyncio
    async def test_recommend_templates_for_requirements(self, template_matcher, sample_requirements):
        """测试基于需求推荐模板"""
        recommendations = await template_matcher.recommend_templates_for_requirements(
            sample_requirements, max_results=2
        )

        assert len(recommendations) <= 2
        assert len(recommendations) > 0

        # 应该推荐技术相关的模板
        assert any(match.template.category == TemplateCategory.TECHNICAL_ANALYSIS
                  for match in recommendations)


class TestSimilarityCalculation:
    """相似性计算测试"""

    @pytest.mark.asyncio
    async def test_calculate_text_similarity(self, template_matcher):
        """测试文本相似性计算"""
        text1 = "请写一篇关于人工智能的技术文章"
        text2 = "请写一篇关于机器学习的技术报告"
        text3 = "创作一个爱情故事"

        # 相似文本的相似度应该更高
        sim12 = await template_matcher._calculate_text_similarity(text1, text2)
        sim13 = await template_matcher._calculate_text_similarity(text1, text3)

        assert sim12 > sim13

    @pytest.mark.asyncio
    async def test_calculate_structure_similarity(self, template_matcher):
        """测试结构相似性计算"""
        prompt1 = "请分析系统性能。要求：包含延迟和吞吐量分析。"
        prompt2 = "请评估架构设计。要求：包含可扩展性和可靠性评估。"
        prompt3 = "写一个故事"

        # 结构相似的提示词相似度应该更高
        sim12 = await template_matcher._calculate_structure_similarity(prompt1, prompt2)
        sim13 = await template_matcher._calculate_structure_similarity(prompt1, prompt3)

        assert sim12 > sim13

    @pytest.mark.asyncio
    async def test_calculate_domain_similarity(self, template_matcher, sample_requirements):
        """测试领域相似性计算"""
        tech_prompt = "分析分布式系统的性能架构"
        creative_prompt = "创作一个科幻小说"

        tech_template = template_matcher.templates[1]  # 技术分析模板
        creative_template = template_matcher.templates[2]  # 创意写作模板

        tech_sim = await template_matcher._calculate_domain_similarity(
            tech_prompt, tech_template, sample_requirements
        )
        creative_sim = await template_matcher._calculate_domain_similarity(
            tech_prompt, creative_template, sample_requirements
        )

        assert tech_sim > creative_sim

    def test_preprocess_text(self, template_matcher):
        """测试文本预处理"""
        text = "请写一篇关于人工智能的技术文章，包含机器学习和深度学习。"
        processed = template_matcher._preprocess_text(text)

        assert "人工智能" in processed
        assert "技术" in processed
        assert "文章" in processed
        # 停用词应该被过滤
        assert "的" not in processed
        assert "一" not in processed

    def test_jaccard_similarity(self, template_matcher):
        """测试Jaccard相似性"""
        set1 = {"机器学习", "人工智能", "算法"}
        set2 = {"机器学习", "深度学习", "神经网络"}
        set3 = {"文学", "小说", "创作"}

        sim12 = template_matcher._jaccard_similarity(set1, set2)
        sim13 = template_matcher._jaccard_similarity(set1, set3)

        assert sim12 > 0  # 有共同元素
        assert sim13 == 0  # 没有共同元素
        assert sim12 > sim13

    def test_extract_structure_features(self, template_matcher):
        """测试结构特征提取"""
        complex_prompt = """
        请分析系统性能。

        要求：
        1. 评估延迟
        2. 分析吞吐量

        例如：可以参考Netflix的架构
        注意：避免过度优化
        """

        features = template_matcher._extract_structure_features(complex_prompt)

        assert features["sentence_count"] > 1
        assert features["numbered_items"] > 0
        assert features["instructions"] > 0
        assert features["examples"] > 0
        assert features["constraints"] > 0


class TestTemplateAnalysis:
    """模板分析测试"""

    @pytest.mark.asyncio
    async def test_identify_matching_features(self, template_matcher):
        """测试匹配特征识别"""
        prompt = "请分析分布式系统的性能架构，包含延迟和吞吐量评估"
        template = template_matcher.templates[1]  # 技术分析模板

        features = await template_matcher._identify_matching_features(
            prompt, template, None
        )

        assert len(features) > 0
        assert any("技术" in feature or "分析" in feature for feature in features)

    @pytest.mark.asyncio
    async def test_analyze_adaptation_needs_variables(self, template_matcher):
        """测试变量适配需求分析"""
        prompt = "分析系统性能"
        template = template_matcher.templates[1]  # 包含变量的模板

        adaptation_needed, suggestions = await template_matcher._analyze_adaptation_needs(
            prompt, template, None
        )

        assert adaptation_needed
        assert any("变量" in suggestion for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_analyze_adaptation_needs_length(self, template_matcher):
        """测试长度适配需求分析"""
        short_prompt = "分析"
        long_prompt = "请详细分析分布式系统的各种性能指标，包括但不限于延迟、吞吐量、可扩展性、可靠性、安全性、监控指标等多个方面，并提供具体的优化建议和实施方案。"

        template = template_matcher.templates[0]

        _, short_suggestions = await template_matcher._analyze_adaptation_needs(
            short_prompt, template, None
        )
        _, long_suggestions = await template_matcher._analyze_adaptation_needs(
            long_prompt, template, None
        )

        # 短提示词应该建议增加信息
        assert any("增加" in suggestion for suggestion in short_suggestions)
        # 长提示词应该建议简化
        assert any("简化" in suggestion for suggestion in long_suggestions)

    def test_infer_category_from_requirements(self, template_matcher):
        """测试从需求推断类别"""
        # 技术需求
        tech_requirements = ParsedRequirements(
            original_input="分析系统架构",
            intent=ParsedIntent(category=IntentCategory.ANALYZE_PROMPT, confidence=0.8),
            main_objective="分析技术系统的架构设计"
        )

        category = template_matcher._infer_category_from_requirements(tech_requirements)
        assert category == TemplateCategory.TECHNICAL_ANALYSIS

        # 创意需求
        creative_requirements = ParsedRequirements(
            original_input="写一个故事",
            intent=ParsedIntent(category=IntentCategory.CREATE_PROMPT, confidence=0.8),
            main_objective="创作一个有趣的故事"
        )

        category = template_matcher._infer_category_from_requirements(creative_requirements)
        assert category == TemplateCategory.CREATIVE_WRITING

        # 通用需求
        general_requirements = ParsedRequirements(
            original_input="帮助我完成任务",
            intent=ParsedIntent(category=IntentCategory.GENERAL_INQUIRY, confidence=0.8),
            main_objective="完成某个任务"
        )

        category = template_matcher._infer_category_from_requirements(general_requirements)
        assert category == TemplateCategory.GENERAL_PURPOSE


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self):
        """测试格式错误的JSON处理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            matcher = TemplateMatcher(temp_path)
            await matcher._load_templates()

            assert len(matcher.templates) == 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_invalid_template_data_handling(self):
        """测试无效模板数据处理"""
        invalid_data = {
            "templates": [
                {
                    "template_id": "invalid_001",
                    # 缺少必需字段
                    "name": "Invalid Template"
                },
                {
                    "template_id": "valid_001",
                    "name": "Valid Template",
                    "category": "general_purpose",
                    "description": "A valid template",
                    "template_content": "Test content",
                    "variables": [],
                    "example_values": {},
                    "use_cases": [],
                    "tags": [],
                    "complexity": "simple",
                    "prompt_type": "general",
                    "success_rate": 0.8,
                    "usage_count": 10,
                    "rating": 4.0,
                    "is_active": True
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_path = f.name

        try:
            matcher = TemplateMatcher(temp_path)
            await matcher._load_templates()

            # 只有有效的模板被加载
            assert len(matcher.templates) == 1
            assert matcher.templates[0].template_id == "valid_001"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_empty_template_list_handling(self, template_matcher):
        """测试空模板列表处理"""
        template_matcher.templates = []

        matches = await template_matcher.find_matching_templates("test prompt")
        assert len(matches) == 0

        templates = await template_matcher.search_templates(TemplateSearchCriteria())
        assert len(templates) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])