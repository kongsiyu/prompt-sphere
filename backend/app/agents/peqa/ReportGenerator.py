"""
报告生成器

负责生成详细的质量评估报告，支持多种格式输出。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import (
    QualityAssessment, AssessmentReport, ReportFormat,
    QualityDimension, QualityLevel, Improvement,
    ReportGenerationError
)
from .config import PEQAConfig


class ReportGenerator:
    """报告生成器"""

    def __init__(self, config: PEQAConfig):
        """初始化报告生成器"""
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def generate_report(self, assessment: QualityAssessment,
                            format: str = "detailed") -> AssessmentReport:
        """
        生成评估报告

        Args:
            assessment: 质量评估结果
            format: 报告格式类型

        Returns:
            AssessmentReport: 生成的报告
        """
        try:
            # 生成执行摘要
            executive_summary = self._generate_executive_summary(assessment)

            # 生成详细内容
            detailed_content = await self._generate_detailed_content(assessment, format)

            # 生成推荐行动
            recommendations = self._generate_recommendations(assessment)

            report = AssessmentReport(
                assessment=assessment,
                report_format=ReportFormat.MARKDOWN,  # 默认格式
                executive_summary=executive_summary,
                detailed_content=detailed_content,
                recommendations=recommendations,
                language=self.config.get_report_config("language", "zh")
            )

            return report

        except Exception as e:
            self.logger.error(f"报告生成失败: {str(e)}")
            raise ReportGenerationError(f"报告生成失败: {str(e)}")

    def _generate_executive_summary(self, assessment: QualityAssessment) -> str:
        """生成执行摘要"""
        quality_level_cn = {
            QualityLevel.EXCELLENT: "优秀",
            QualityLevel.GOOD: "良好",
            QualityLevel.FAIR: "一般",
            QualityLevel.POOR: "较差",
            QualityLevel.VERY_POOR: "很差"
        }

        level_text = quality_level_cn.get(assessment.quality_level, "未知")
        score_text = f"{assessment.overall_score:.2f}"

        summary = f"""
# 提示词质量评估摘要

**总体评分**: {score_text}/1.00 ({level_text})
**置信度**: {assessment.confidence_level:.2f}
**评估时间**: {assessment.assessed_at.strftime('%Y-%m-%d %H:%M:%S')}

## 快速洞察
- **主要优势**: {len(assessment.strengths)}项
- **改进空间**: {len(assessment.weaknesses)}项
- **建议行动**: {len(assessment.improvement_suggestions)}项

## 质量概况
该提示词的整体质量为{level_text}级别，在{len(assessment.dimension_scores)}个评估维度中表现如下：
"""

        # 添加维度概况
        for dimension, score in assessment.dimension_scores.items():
            dimension_cn = {
                QualityDimension.CLARITY: "清晰度",
                QualityDimension.SPECIFICITY: "具体性",
                QualityDimension.COMPLETENESS: "完整性",
                QualityDimension.EFFECTIVENESS: "有效性",
                QualityDimension.ROBUSTNESS: "鲁棒性"
            }
            dim_name = dimension_cn.get(dimension, dimension.value)
            summary += f"- **{dim_name}**: {score.score:.2f}\n"

        return summary.strip()

    async def _generate_detailed_content(self, assessment: QualityAssessment, format: str) -> str:
        """生成详细内容"""
        if format == "detailed":
            return self._generate_detailed_analysis(assessment)
        elif format == "summary":
            return self._generate_summary_analysis(assessment)
        elif format == "compact":
            return self._generate_compact_analysis(assessment)
        else:
            return self._generate_detailed_analysis(assessment)

    def _generate_detailed_analysis(self, assessment: QualityAssessment) -> str:
        """生成详细分析报告"""
        content = f"""
# 详细质量分析报告

## 提示词内容
```
{assessment.prompt_content}
```

## 维度评分详情

"""

        dimension_names = {
            QualityDimension.CLARITY: "清晰度",
            QualityDimension.SPECIFICITY: "具体性",
            QualityDimension.COMPLETENESS: "完整性",
            QualityDimension.EFFECTIVENESS: "有效性",
            QualityDimension.ROBUSTNESS: "鲁棒性"
        }

        for dimension, score in assessment.dimension_scores.items():
            dim_name = dimension_names.get(dimension, dimension.value)
            content += f"""
### {dim_name} - {score.score:.2f}/1.00

**评分理由**: {score.reasoning or '基于算法自动评估'}

**优势表现**:
"""
            for evidence in score.evidence:
                content += f"- {evidence}\n"

            if score.issues:
                content += f"""
**发现问题**:
"""
                for issue in score.issues:
                    content += f"- {issue}\n"

            content += f"\n**置信度**: {score.confidence:.2f}\n"

        # 添加优势分析
        if assessment.strengths:
            content += """
## 优势分析

"""
            for strength in assessment.strengths:
                content += f"- {strength}\n"

        # 添加不足分析
        if assessment.weaknesses:
            content += """
## 改进空间

"""
            for weakness in assessment.weaknesses:
                content += f"- {weakness}\n"

        # 添加改进建议
        if assessment.improvement_suggestions:
            content += """
## 改进建议

"""
            for i, improvement in enumerate(assessment.improvement_suggestions, 1):
                priority_cn = {
                    "critical": "🔴 关键",
                    "high": "🟠 高",
                    "medium": "🟡 中",
                    "low": "🟢 低"
                }
                priority_text = priority_cn.get(improvement.priority.value, improvement.priority.value)

                content += f"""
### {i}. {improvement.title} ({priority_text})

**描述**: {improvement.description}

**预期影响**: {improvement.impact_score:.2f}
**实施难度**: {improvement.difficulty}
**预估改进**: {improvement.estimated_improvement:.2f}

"""
                if improvement.before_example and improvement.after_example:
                    content += f"""
**改进示例**:
- 改进前: `{improvement.before_example}`
- 改进后: `{improvement.after_example}`

"""

                if improvement.rationale:
                    content += f"**实施理由**: {improvement.rationale}\n\n"

        # 添加技术细节
        content += f"""
## 技术细节

- **处理时间**: {assessment.processing_time_ms}ms
- **提示词长度**: {len(assessment.prompt_content)}字符
- **词数**: {len(assessment.prompt_content.split())}个
- **评估维度**: {len(assessment.dimension_scores)}个
- **置信度**: {assessment.confidence_level:.2f}

"""

        return content

    def _generate_summary_analysis(self, assessment: QualityAssessment) -> str:
        """生成摘要分析"""
        content = f"""
# 质量评估摘要

**整体评分**: {assessment.overall_score:.2f}/1.00
**质量等级**: {assessment.quality_level.value}

## 各维度表现
"""
        for dimension, score in assessment.dimension_scores.items():
            content += f"- {dimension.value}: {score.score:.2f}\n"

        content += f"""
## 主要发现
- 优势: {len(assessment.strengths)}项
- 问题: {len(assessment.weaknesses)}项
- 建议: {len(assessment.improvement_suggestions)}项

## 建议行动
"""
        for improvement in assessment.improvement_suggestions[:3]:  # 只显示前3个
            content += f"- {improvement.title}\n"

        return content

    def _generate_compact_analysis(self, assessment: QualityAssessment) -> str:
        """生成紧凑分析"""
        content = f"""
评分: {assessment.overall_score:.2f} | 等级: {assessment.quality_level.value}
维度: 清晰度{assessment.get_dimension_score(QualityDimension.CLARITY):.2f} 具体性{assessment.get_dimension_score(QualityDimension.SPECIFICITY):.2f} 完整性{assessment.get_dimension_score(QualityDimension.COMPLETENESS):.2f}
建议: {len(assessment.improvement_suggestions)}项改进
"""
        return content.strip()

    def _generate_recommendations(self, assessment: QualityAssessment) -> List[str]:
        """生成推荐行动"""
        recommendations = []

        # 基于质量等级的建议
        if assessment.quality_level == QualityLevel.VERY_POOR:
            recommendations.append("立即重写提示词，明确任务目标和具体要求")
            recommendations.append("添加详细的背景信息和约束条件")
        elif assessment.quality_level == QualityLevel.POOR:
            recommendations.append("重点改进清晰度和具体性")
            recommendations.append("添加具体示例和格式要求")
        elif assessment.quality_level == QualityLevel.FAIR:
            recommendations.append("优化表达方式，增强专业性")
            recommendations.append("考虑边界情况和错误处理")
        elif assessment.quality_level == QualityLevel.GOOD:
            recommendations.append("进行细节优化以达到优秀水平")
            recommendations.append("增强鲁棒性考虑")
        else:  # EXCELLENT
            recommendations.append("保持当前质量，定期评估优化")

        # 基于具体问题的建议
        if assessment.improvement_suggestions:
            top_suggestion = assessment.improvement_suggestions[0]
            recommendations.append(f"优先处理: {top_suggestion.title}")

        # 基于维度分析的建议
        low_score_dimensions = [
            dim for dim, score in assessment.dimension_scores.items()
            if score.score < 0.5
        ]

        if low_score_dimensions:
            dim_names = {
                QualityDimension.CLARITY: "清晰度",
                QualityDimension.SPECIFICITY: "具体性",
                QualityDimension.COMPLETENESS: "完整性",
                QualityDimension.EFFECTIVENESS: "有效性",
                QualityDimension.ROBUSTNESS: "鲁棒性"
            }
            low_dims = [dim_names.get(dim, dim.value) for dim in low_score_dimensions]
            recommendations.append(f"重点提升: {', '.join(low_dims)}")

        return recommendations

    async def export_report(self, report: AssessmentReport,
                          export_format: ReportFormat,
                          file_path: Optional[str] = None) -> str:
        """
        导出报告到文件

        Args:
            report: 评估报告
            export_format: 导出格式
            file_path: 文件路径

        Returns:
            str: 导出的内容或文件路径
        """
        try:
            if export_format == ReportFormat.JSON:
                import json
                content = json.dumps(report.model_dump(), indent=2, ensure_ascii=False)
            elif export_format == ReportFormat.HTML:
                content = self._convert_to_html(report)
            elif export_format == ReportFormat.MARKDOWN:
                content = report.detailed_content
            elif export_format == ReportFormat.TEXT:
                content = self._convert_to_text(report)
            elif export_format == ReportFormat.CSV:
                content = self._convert_to_csv(report)
            else:
                raise ReportGenerationError(f"不支持的导出格式: {export_format}")

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return file_path
            else:
                return content

        except Exception as e:
            raise ReportGenerationError(f"报告导出失败: {str(e)}")

    def _convert_to_html(self, report: AssessmentReport) -> str:
        """转换为HTML格式"""
        # 简化的HTML转换
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PEQA质量评估报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        .score {{ font-size: 24px; font-weight: bold; color: #007acc; }}
        .dimension {{ margin: 10px 0; }}
        .improvement {{ border-left: 3px solid #007acc; padding-left: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>提示词质量评估报告</h1>
    <div class="score">总体评分: {report.assessment.overall_score:.2f}</div>
    <p><strong>质量等级</strong>: {report.assessment.quality_level.value}</p>
    <p><strong>评估时间</strong>: {report.assessment.assessed_at}</p>

    <h2>执行摘要</h2>
    <pre>{report.executive_summary}</pre>

    <h2>详细内容</h2>
    <pre>{report.detailed_content}</pre>
</body>
</html>
"""
        return html

    def _convert_to_text(self, report: AssessmentReport) -> str:
        """转换为纯文本格式"""
        text = f"""
PEQA质量评估报告
================

总体评分: {report.assessment.overall_score:.2f}
质量等级: {report.assessment.quality_level.value}
评估时间: {report.assessment.assessed_at}

执行摘要
--------
{report.executive_summary}

详细内容
--------
{report.detailed_content}

推荐行动
--------
"""
        for i, rec in enumerate(report.recommendations, 1):
            text += f"{i}. {rec}\n"

        return text

    def _convert_to_csv(self, report: AssessmentReport) -> str:
        """转换为CSV格式"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow(['指标', '数值', '说明'])

        # 写入基本信息
        writer.writerow(['总体评分', f"{report.assessment.overall_score:.2f}", '0-1分制'])
        writer.writerow(['质量等级', report.assessment.quality_level.value, ''])
        writer.writerow(['置信度', f"{report.assessment.confidence_level:.2f}", ''])

        # 写入维度评分
        for dimension, score in report.assessment.dimension_scores.items():
            writer.writerow([f'{dimension.value}评分', f"{score.score:.2f}", score.reasoning or ''])

        # 写入统计信息
        writer.writerow(['优势数量', len(report.assessment.strengths), ''])
        writer.writerow(['问题数量', len(report.assessment.weaknesses), ''])
        writer.writerow(['建议数量', len(report.assessment.improvement_suggestions), ''])
        writer.writerow(['处理时间', f"{report.assessment.processing_time_ms}ms", ''])

        return output.getvalue()