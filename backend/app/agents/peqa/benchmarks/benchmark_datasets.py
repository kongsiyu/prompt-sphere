"""
PEQA基准测试数据集

提供标准化的测试数据集用于性能、质量、准确性基准测试
"""

from typing import Dict, List, Any
from ..types import QualityDimension


class BenchmarkDatasets:
    """基准测试数据集"""

    @staticmethod
    def get_performance_test_prompts() -> List[str]:
        """性能测试提示词集合（用于吞吐量和延迟测试）"""
        return [
            # 短提示词 (< 50字符)
            "写代码",
            "分析数据",
            "创建报告",
            "优化性能",
            "设计系统",

            # 中等提示词 (50-200字符)
            "请为我编写一个Python函数，用于计算两个数字的平均值。",
            "分析这份销售数据，找出增长趋势和异常值。",
            "创建一个详细的项目进度报告，包含时间线和里程碑。",
            "优化数据库查询性能，减少响应时间到100ms以内。",
            "设计一个微服务架构，支持高并发和横向扩展。",

            # 长提示词 (200-500字符)
            "作为一名资深的数据科学家，请为我设计一个完整的机器学习项目方案。项目目标是预测客户流失，需要包含数据收集、预处理、特征工程、模型选择、训练、评估和部署的完整流程。请提供详细的技术栈选择理由和实施时间表。",
            "请帮我创建一个企业级的客户关系管理系统设计方案。系统需要支持销售流程管理、客户数据分析、营销自动化和报表生成功能。要求使用微服务架构，支持10万并发用户，并且具备高可用性和数据安全保障。请提供详细的架构图和技术选型说明。",

            # 复杂提示词 (500+字符)
            "我正在开发一个智能推荐系统，用于电商平台的商品推荐。系统需要处理用户行为数据（浏览、购买、评价）、商品属性数据（类别、价格、品牌、描述）和实时上下文信息（时间、地点、设备）。请为我设计一个综合的推荐算法框架，包括协同过滤、内容推荐、深度学习模型等多种方法的融合。同时需要考虑冷启动问题、实时性要求、A/B测试框架和推荐结果的可解释性。请提供详细的系统架构、算法选择、数据流设计和性能优化策略。",
        ]

    @staticmethod
    def get_quality_test_cases() -> List[Dict[str, Any]]:
        """质量测试用例（带预期评分）"""
        return [
            {
                "prompt": "请为我创建一个Python函数，计算列表中所有数字的平均值，要求处理空列表和非数字值的异常情况。",
                "expected_score": 0.85,
                "expected_level": "good",
                "expected_dimensions": {
                    QualityDimension.CLARITY: 0.9,
                    QualityDimension.SPECIFICITY: 0.8,
                    QualityDimension.COMPLETENESS: 0.8,
                    QualityDimension.EFFECTIVENESS: 0.9,
                    QualityDimension.ROBUSTNESS: 0.8
                },
                "expected_issues": []
            },
            {
                "prompt": "写代码",
                "expected_score": 0.15,
                "expected_level": "very_poor",
                "expected_dimensions": {
                    QualityDimension.CLARITY: 0.2,
                    QualityDimension.SPECIFICITY: 0.1,
                    QualityDimension.COMPLETENESS: 0.1,
                    QualityDimension.EFFECTIVENESS: 0.2,
                    QualityDimension.ROBUSTNESS: 0.1
                },
                "expected_issues": ["clarity", "specificity", "completeness"]
            },
            {
                "prompt": "分析销售数据并生成报告",
                "expected_score": 0.45,
                "expected_level": "fair",
                "expected_dimensions": {
                    QualityDimension.CLARITY: 0.6,
                    QualityDimension.SPECIFICITY: 0.3,
                    QualityDimension.COMPLETENESS: 0.4,
                    QualityDimension.EFFECTIVENESS: 0.6,
                    QualityDimension.ROBUSTNESS: 0.3
                },
                "expected_issues": ["specificity", "completeness"]
            },
            {
                "prompt": "作为一个专业的Python开发工程师，请为我编写一个完整的数据分析脚本。要求：1)读取CSV文件data.csv，2)计算销售额的平均值、中位数和标准差，3)生成可视化图表保存为sales_analysis.png，4)输出详细的统计报告。请包含错误处理和代码注释。",
                "expected_score": 0.92,
                "expected_level": "excellent",
                "expected_dimensions": {
                    QualityDimension.CLARITY: 0.95,
                    QualityDimension.SPECIFICITY: 0.9,
                    QualityDimension.COMPLETENESS: 0.9,
                    QualityDimension.EFFECTIVENESS: 0.95,
                    QualityDimension.ROBUSTNESS: 0.9
                },
                "expected_issues": []
            }
        ]

    @staticmethod
    def get_scalability_test_prompts() -> List[str]:
        """可扩展性测试基础提示词"""
        return [
            "请创建一个Web应用",
            "分析用户行为数据，找出关键模式",
            "设计数据库schema支持电商系统",
            "优化API性能提升响应速度",
            "实现用户认证和权限管理系统"
        ]

    @staticmethod
    def get_accuracy_gold_standard() -> List[Dict[str, Any]]:
        """准确性测试黄金标准数据集"""
        return [
            {
                "prompt": "请帮我写一个hello world程序",
                "ground_truth": {
                    "overall_score": 0.3,
                    "quality_level": "poor",
                    "dimension_scores": {
                        "clarity": 0.6,
                        "specificity": 0.2,
                        "completeness": 0.2,
                        "effectiveness": 0.4,
                        "robustness": 0.2
                    },
                    "expected_issues": ["specificity", "completeness"],
                    "improvement_categories": ["specificity", "completeness"]
                }
            },
            {
                "prompt": "作为一名经验丰富的软件架构师，请为我设计一个高性能的分布式缓存系统。系统需要支持：1)数据分片和负载均衡，2)故障检测和自动恢复，3)数据一致性保证，4)监控和告警功能。请提供详细的架构设计、技术选型理由、部署方案和性能优化策略。",
                "ground_truth": {
                    "overall_score": 0.88,
                    "quality_level": "good",
                    "dimension_scores": {
                        "clarity": 0.9,
                        "specificity": 0.85,
                        "completeness": 0.9,
                        "effectiveness": 0.9,
                        "robustness": 0.85
                    },
                    "expected_issues": [],
                    "improvement_categories": []
                }
            },
            {
                "prompt": "优化代码性能",
                "ground_truth": {
                    "overall_score": 0.2,
                    "quality_level": "very_poor",
                    "dimension_scores": {
                        "clarity": 0.3,
                        "specificity": 0.1,
                        "completeness": 0.1,
                        "effectiveness": 0.2,
                        "robustness": 0.1
                    },
                    "expected_issues": ["clarity", "specificity", "completeness", "effectiveness"],
                    "improvement_categories": ["clarity", "specificity", "completeness"]
                }
            }
        ]

    @staticmethod
    def get_stress_test_prompts(count: int = 1000) -> List[str]:
        """压力测试提示词生成器"""
        base_prompts = BenchmarkDatasets.get_performance_test_prompts()

        # 扩展到指定数量
        prompts = []
        for i in range(count):
            base_prompt = base_prompts[i % len(base_prompts)]
            # 添加变化使每个提示词略有不同
            varied_prompt = f"{base_prompt} (测试编号: {i+1})"
            prompts.append(varied_prompt)

        return prompts

    @staticmethod
    def get_domain_specific_prompts() -> Dict[str, List[str]]:
        """领域特定测试提示词"""
        return {
            "programming": [
                "编写一个Python爬虫抓取新闻标题",
                "实现二分查找算法并分析时间复杂度",
                "设计RESTful API接口规范",
                "创建React组件处理表单验证",
                "优化SQL查询提升数据库性能"
            ],
            "data_analysis": [
                "分析用户留存率变化趋势",
                "构建销售预测模型",
                "设计A/B测试统计分析",
                "创建数据可视化仪表板",
                "实现实时数据流处理"
            ],
            "business": [
                "制定产品营销策略",
                "分析竞争对手优劣势",
                "设计客户满意度调研方案",
                "优化业务流程提升效率",
                "制定数字化转型计划"
            ],
            "creative": [
                "写一个科幻小说开头",
                "设计品牌logo和视觉识别",
                "创作广告文案吸引目标客户",
                "编写技术文档和使用手册",
                "设计用户体验流程"
            ]
        }

    @staticmethod
    def get_edge_case_prompts() -> List[str]:
        """边界情况测试提示词"""
        return [
            "",  # 空提示词
            " ",  # 只有空格
            "a",  # 单字符
            "?" * 100,  # 重复字符
            "写" + "一个很长的" * 50 + "程序",  # 超长提示词
            "Write code in English mixed with 中文 and special chars !@#$%",  # 混合语言和特殊字符
            "\n\n\n多行\n\n提示词\n\n测试\n\n",  # 多换行符
            "🚀🔥💡📊🎯" * 20,  # 大量emoji
        ]

    @staticmethod
    def generate_synthetic_dataset(size: int, complexity_distribution: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        生成合成测试数据集

        Args:
            size: 数据集大小
            complexity_distribution: 复杂度分布 {"simple": 0.3, "medium": 0.5, "complex": 0.2}
        """
        if complexity_distribution is None:
            complexity_distribution = {"simple": 0.4, "medium": 0.4, "complex": 0.2}

        datasets = []
        simple_templates = [
            "创建{object}",
            "分析{data}",
            "优化{target}",
            "设计{system}",
            "实现{feature}"
        ]

        medium_templates = [
            "请为我{action}一个{object}，要求{requirement}",
            "作为{role}，帮我{action}{target}，需要考虑{constraint}",
            "分析{data}并生成{output}，包含{details}"
        ]

        complex_templates = [
            "作为一名专业的{expert}，请为我设计一个{system}。要求：1){req1}，2){req2}，3){req3}。请提供详细的{deliverable}和{timeline}。",
            "我需要实现一个{complex_system}，它应该具备{feature1}、{feature2}和{feature3}功能。请考虑{constraint1}、{constraint2}的限制，并提供{solution_type}和{implementation_details}。"
        ]

        # 计算各复杂度的数量
        simple_count = int(size * complexity_distribution["simple"])
        medium_count = int(size * complexity_distribution["medium"])
        complex_count = size - simple_count - medium_count

        # 生成不同复杂度的提示词
        for i in range(simple_count):
            template = simple_templates[i % len(simple_templates)]
            prompt = template.format(
                object=f"工具{i}",
                data=f"数据{i}",
                target=f"目标{i}",
                system=f"系统{i}",
                feature=f"功能{i}"
            )
            datasets.append({
                "prompt": prompt,
                "complexity": "simple",
                "expected_score_range": (0.2, 0.5)
            })

        for i in range(medium_count):
            template = medium_templates[i % len(medium_templates)]
            prompt = template.format(
                action=f"创建",
                object=f"应用{i}",
                requirement=f"高性能和可扩展性",
                role=f"开发工程师",
                target=f"系统{i}",
                constraint=f"资源限制",
                data=f"用户数据",
                output=f"报告",
                details=f"趋势分析"
            )
            datasets.append({
                "prompt": prompt,
                "complexity": "medium",
                "expected_score_range": (0.4, 0.7)
            })

        for i in range(complex_count):
            template = complex_templates[i % len(complex_templates)]
            prompt = template.format(
                expert=f"系统架构师",
                system=f"分布式系统{i}",
                req1=f"高并发处理",
                req2=f"数据一致性",
                req3=f"故障恢复",
                deliverable=f"架构设计",
                timeline=f"实施计划",
                complex_system=f"智能推荐系统{i}",
                feature1=f"实时计算",
                feature2=f"机器学习",
                feature3=f"个性化推荐",
                constraint1=f"延迟要求",
                constraint2=f"成本控制",
                solution_type=f"技术方案",
                implementation_details=f"实现细节"
            )
            datasets.append({
                "prompt": prompt,
                "complexity": "complex",
                "expected_score_range": (0.6, 0.9)
            })

        return datasets