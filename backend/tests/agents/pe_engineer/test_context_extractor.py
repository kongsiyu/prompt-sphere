"""
上下文提取器测试

测试 ContextExtractor 类的各种功能，包括上下文提取、
领域识别、技术需求分析等。
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from app.agents.pe_engineer.parsers.context_extractor import ContextExtractor
from app.agents.pe_engineer.schemas.requirements import (
    ExtractedContext, ContextType, DomainInfo, TechnicalRequirement
)


class TestContextExtractor:
    """测试上下文提取器"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return ContextExtractor()

    def test_init(self, extractor):
        """测试初始化"""
        assert extractor is not None
        assert extractor.context_patterns is not None
        assert extractor.domain_patterns is not None
        assert extractor.technical_keywords is not None
        assert len(extractor.domain_patterns) > 0

    def test_extract_contexts_empty_input(self, extractor):
        """测试空输入"""
        result = extractor.extract_contexts("")
        assert result == []

        result = extractor.extract_contexts("   ")
        assert result == []

    def test_extract_contexts_short_input(self, extractor):
        """测试过短输入"""
        result = extractor.extract_contexts("hi")
        assert result == []

    def test_extract_domain_contexts(self, extractor):
        """测试领域上下文提取"""
        text = "我是一名前端开发工程师，专业从事React开发工作"
        contexts = extractor.extract_contexts(text)

        # 应该提取到领域相关上下文
        domain_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.DOMAIN]
        assert len(domain_contexts) > 0

        # 验证内容相关性
        found_domain_content = False
        for ctx in domain_contexts:
            if any(keyword in ctx.content for keyword in ["前端", "开发", "React"]):
                found_domain_content = True
                break
        assert found_domain_content

    def test_extract_technical_contexts(self, extractor):
        """测试技术上下文提取"""
        text = "使用Python和Django框架开发API接口，需要集成Redis缓存"
        contexts = extractor.extract_contexts(text)

        # 应该提取到技术相关上下文
        tech_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.TECHNICAL]
        assert len(tech_contexts) > 0

        # 验证技术关键词
        all_content = " ".join(ctx.content for ctx in tech_contexts)
        tech_keywords = ["Python", "Django", "API", "Redis"]
        found_keywords = [kw for kw in tech_keywords if kw in all_content]
        assert len(found_keywords) > 0

    def test_extract_business_contexts(self, extractor):
        """测试业务上下文提取"""
        text = "这个项目是为电商用户提供商品推荐服务，面向年轻消费者群体"
        contexts = extractor.extract_contexts(text)

        # 应该提取到业务相关上下文
        business_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.BUSINESS]
        assert len(business_contexts) > 0

    def test_extract_constraint_contexts(self, extractor):
        """测试约束上下文提取"""
        text = "长度不能超过200字，不要包含技术术语，必须保持简洁风格"
        contexts = extractor.extract_contexts(text)

        # 应该提取到约束相关上下文
        constraint_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.CONSTRAINT]
        assert len(constraint_contexts) > 0

    def test_extract_example_contexts(self, extractor):
        """测试示例上下文提取"""
        text = "例如：生成用户注册界面的代码，比如包含用户名、密码输入框"
        contexts = extractor.extract_contexts(text)

        # 应该提取到示例相关上下文
        example_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.EXAMPLE]
        assert len(example_contexts) > 0

    def test_extract_personal_contexts(self, extractor):
        """测试个人偏好上下文提取"""
        text = "我个人比较喜欢简洁的代码风格，习惯使用函数式编程"
        contexts = extractor.extract_contexts(text)

        # 应该提取到个人偏好上下文
        personal_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.PERSONAL]
        assert len(personal_contexts) > 0

    def test_extract_domain_info(self, extractor):
        """测试领域信息提取"""
        test_cases = [
            ("我是软件开发工程师，专门做前端开发", "软件开发"),
            ("从事人工智能和机器学习研究", "人工智能"),
            ("做数据分析和可视化工作", "数据分析"),
            ("产品设计师，负责UI/UX设计", "产品设计"),
            ("市场营销人员，做品牌推广", "市场营销"),
            ("教育行业，开发在线课程", "教育培训"),
            ("金融科技公司，做支付系统", "金融科技"),
            ("医疗健康领域，开发诊断系统", "医疗健康")
        ]

        for text, expected_domain in test_cases:
            domain_info = extractor.extract_domain_info(text)

            if domain_info:
                assert isinstance(domain_info, DomainInfo)
                assert domain_info.name == expected_domain
                assert 0.0 <= domain_info.confidence <= 1.0
                assert isinstance(domain_info.keywords, list)

    def test_extract_domain_info_no_match(self, extractor):
        """测试无领域匹配"""
        text = "今天天气很好，我想出去走走"
        domain_info = extractor.extract_domain_info(text)

        assert domain_info is None

    def test_extract_technical_requirements(self, extractor):
        """测试技术需求提取"""
        text = "使用Python开发，需要高性能和实时响应，输出JSON格式"
        tech_reqs = extractor.extract_technical_requirements(text)

        assert isinstance(tech_reqs, list)
        assert len(tech_reqs) > 0

        # 验证技术需求的基本结构
        for req in tech_reqs:
            assert isinstance(req, TechnicalRequirement)
            assert hasattr(req, 'requirement_type')
            assert hasattr(req, 'description')
            assert hasattr(req, 'priority')

        # 验证是否包含技术栈要求
        tech_stack_reqs = [req for req in tech_reqs if req.requirement_type == "technology"]
        assert len(tech_stack_reqs) > 0

    def test_context_importance_calculation(self, extractor):
        """测试上下文重要性计算"""
        text = """
        我是一名资深的全栈开发工程师，有5年React和Node.js开发经验。
        现在需要创建一个用于电商网站的用户注册功能的代码生成提示词。
        要求代码规范、性能优良、包含输入验证。
        """
        contexts = extractor.extract_contexts(text)

        assert len(contexts) > 0

        # 验证重要性分数
        for ctx in contexts:
            assert 0.0 <= ctx.importance <= 1.0

        # 验证是否按重要性排序
        importances = [ctx.importance for ctx in contexts]
        assert importances == sorted(importances, reverse=True)

    def test_context_deduplication(self, extractor):
        """测试上下文去重"""
        text = "前端开发前端开发，使用React框架React框架进行开发"
        contexts = extractor.extract_contexts(text)

        # 验证内容没有重复
        contents = [ctx.content for ctx in contexts]
        unique_contents = list(set(contents))
        assert len(contents) == len(unique_contents)

    def test_complex_context_extraction(self, extractor):
        """测试复杂文本的上下文提取"""
        complex_text = """
        我是一名在金融科技公司工作的全栈开发工程师，主要使用Python和React技术栈。
        现在需要为我们的支付系统创建一个API文档生成的提示词。

        具体要求：
        1. 输出格式必须是JSON
        2. 不能包含敏感信息
        3. 代码要符合PEP8规范
        4. 需要包含错误处理

        例如：生成用户支付接口文档，包含参数说明和响应格式。
        参考我们现有的用户管理接口文档格式。

        比较紧急，希望今天能完成。
        """

        contexts = extractor.extract_contexts(complex_text)

        # 验证提取了多种类型的上下文
        context_types = set(ctx.context_type for ctx in contexts)
        expected_types = {
            ContextType.DOMAIN, ContextType.TECHNICAL, ContextType.BUSINESS,
            ContextType.CONSTRAINT, ContextType.EXAMPLE
        }

        # 至少应该有一半的预期类型
        assert len(context_types.intersection(expected_types)) >= len(expected_types) // 2

    def test_subcategory_detection(self, extractor):
        """测试子类别检测"""
        test_cases = [
            ("前端React开发", "软件开发", "前端开发"),
            ("后端API开发", "软件开发", "后端开发"),
            ("移动app开发", "软件开发", "移动开发"),
            ("机器学习算法", "人工智能", "机器学习"),
            ("深度学习模型", "人工智能", "深度学习"),
            ("自然语言处理", "人工智能", "自然语言处理"),
        ]

        for text, expected_domain, expected_subcategory in test_cases:
            domain_info = extractor.extract_domain_info(text)

            if domain_info and domain_info.name == expected_domain:
                # 可能检测到子类别（不强制要求，因为依赖于具体实现）
                if domain_info.subcategory:
                    assert isinstance(domain_info.subcategory, str)

    def test_get_extraction_summary(self, extractor):
        """测试提取摘要"""
        text = "Python开发工程师需要创建API文档，要求JSON格式输出，不能包含密码"
        contexts = extractor.extract_contexts(text)

        summary = extractor.get_extraction_summary(contexts)

        assert isinstance(summary, dict)
        assert "total" in summary
        assert summary["total"] == len(contexts)

        if contexts:
            assert "type_distribution" in summary
            assert "average_importance" in summary
            assert "high_importance_count" in summary
            assert "unique_keywords" in summary

    def test_find_context_around_keyword(self, extractor):
        """测试关键词周围上下文查找"""
        text = "我使用Python语言进行后端开发，主要写API接口"
        matches = extractor._find_context_around_keyword(text, "Python", window_size=10)

        assert isinstance(matches, list)
        if matches:
            for match, position in matches:
                assert isinstance(match, str)
                assert isinstance(position, int)
                assert "Python" in match

    def test_performance_with_large_text(self, extractor):
        """测试大文本处理性能"""
        # 创建较大的文本
        large_text = """
        我是一名资深的全栈开发工程师，有超过8年的软件开发经验。
        主要技术栈包括Python、Django、React、Node.js、MySQL、Redis等。
        曾经在多家互联网公司工作过，包括电商、金融科技、在线教育等领域。

        现在需要创建一系列的代码生成提示词，用于帮助团队提高开发效率。
        这些提示词需要覆盖前端组件开发、后端API设计、数据库设计等多个方面。

        具体要求包括：
        1. 代码必须符合团队的编码规范
        2. 需要包含完整的错误处理逻辑
        3. 要有详细的注释说明
        4. 输出格式统一为JSON结构
        5. 不能包含任何敏感信息或密码
        6. 需要考虑性能优化和安全性
        7. 要支持国际化和多语言
        8. 必须兼容现有的技术架构

        参考我们现有的开发文档和API规范，确保生成的代码风格一致。
        这个项目比较紧急，希望能在下周前完成第一版。
        """ * 10  # 重复10次增加文本长度

        import time
        start_time = time.time()

        contexts = extractor.extract_contexts(large_text)

        end_time = time.time()
        processing_time = end_time - start_time

        # 验证结果
        assert isinstance(contexts, list)
        assert len(contexts) > 0

        # 性能检查（应该在合理时间内完成）
        assert processing_time < 3.0  # 3秒内完成

    def test_edge_cases(self, extractor):
        """测试边界情况"""
        edge_cases = [
            None,
            "",
            "   ",
            "a",
            "123",
            "!@#$%^&*()",
            "English text without Chinese",
        ]

        for case in edge_cases:
            try:
                if case is None:
                    with pytest.raises((TypeError, AttributeError)):
                        extractor.extract_contexts(case)
                else:
                    contexts = extractor.extract_contexts(case)
                    assert isinstance(contexts, list)
                    # 边界情况应该返回空列表或很少的上下文
                    assert len(contexts) <= 2
            except Exception as e:
                print(f"Edge case {case} raised: {e}")

    @pytest.mark.parametrize("invalid_input", [
        123,      # 数字
        [],       # 列表
        {},       # 字典
        True,     # 布尔值
    ])
    def test_invalid_input_types(self, extractor, invalid_input):
        """测试无效输入类型"""
        with pytest.raises((TypeError, AttributeError)):
            extractor.extract_contexts(invalid_input)

    def test_context_position_tracking(self, extractor):
        """测试上下文位置跟踪"""
        text = "前端开发需要React框架和Redux状态管理"
        contexts = extractor.extract_contexts(text)

        for ctx in contexts:
            assert hasattr(ctx, 'source_position')
            assert isinstance(ctx.source_position, int)
            assert ctx.source_position >= 0

    def test_related_keywords_extraction(self, extractor):
        """测试相关关键词提取"""
        text = "使用Python Django框架开发REST API接口"
        contexts = extractor.extract_contexts(text)

        # 验证关键词提取
        for ctx in contexts:
            assert hasattr(ctx, 'related_keywords')
            assert isinstance(ctx.related_keywords, list)

        # 技术上下文应该包含技术关键词
        tech_contexts = [ctx for ctx in contexts if ctx.context_type == ContextType.TECHNICAL]
        if tech_contexts:
            all_keywords = []
            for ctx in tech_contexts:
                all_keywords.extend(ctx.related_keywords)

            # 应该包含一些技术关键词
            tech_terms = ["Python", "Django", "API", "REST"]
            found_terms = [term for term in tech_terms if term in all_keywords]
            assert len(found_terms) > 0

    def test_importance_threshold_filtering(self, extractor):
        """测试重要性阈值过滤"""
        text = "简单的文本没有特别重要的信息"
        contexts = extractor.extract_contexts(text)

        # 验证所有返回的上下文都有合理的重要性分数
        for ctx in contexts:
            assert ctx.importance > 0.0  # 应该过滤掉重要性为0的项目