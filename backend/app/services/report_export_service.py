"""
学习报告导出服务 - AI英语教学系统
支持将学习报告导出为 PDF 或图片格式
"""
import os
from datetime import datetime
from typing import Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pdf_renderer_service import get_pdf_renderer_service


class ReportExportService:
    """学习报告导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_as_pdf(
        self,
        report_data: Dict
    ) -> Tuple[str, bytes]:
        """
        导出学习报告为 PDF

        Args:
            report_data: 报告数据

        Returns:
            (文件名, PDF内容)
        """
        # 获取 PDF 渲染服务
        renderer = get_pdf_renderer_service(self.db)

        # 渲染 Markdown 报告
        markdown_content = await self._render_markdown_report(report_data)

        # 转换为 PDF
        pdf_content = await renderer.render_markdown_to_pdf(markdown_content)

        # 生成文件名
        title = report_data.get("title", "学习报告")
        period_end = report_data.get("period_end", "")
        if period_end:
            date_str = datetime.fromisoformat(period_end).strftime("%Y%m%d")
        else:
            date_str = datetime.now().strftime("%Y%m%d")

        filename = f"{title}_{date_str}.pdf"

        return filename, pdf_content

    async def export_as_image(
        self,
        report_data: Dict
    ) -> Tuple[str, bytes]:
        """
        导出学习报告为图片

        Args:
            report_data: 报告数据

        Returns:
            (文件名, 图片内容)

        Note:
            当前为占位实现，返回一个简单的文本提示
        """
        # TODO: 实现 Playwright 截图功能
        # 需要添加 playwright 依赖
        # 当前返回占位内容

        title = report_data.get("title", "学习报告")
        period_end = report_data.get("period_end", "")
        if period_end:
            date_str = datetime.fromisoformat(period_end).strftime("%Y%m%d")
        else:
            date_str = datetime.now().strftime("%Y%m%d")

        filename = f"{title}_{date_str}_image.png"

        # 占位实现：返回一个简单的文本图片提示
        # 实际使用 Playwright 生成图片
        placeholder = f"""图片导出功能开发中

请使用 PDF 导出功能，或稍后再试。

报告：{title}
日期：{date_str}
"""

        # 返回占位内容（实际应该是 PNG 图片）
        return filename, placeholder.encode("utf-8")

    async def _render_markdown_report(
        self,
        report_data: Dict
    ) -> str:
        """渲染 Markdown 报告"""
        # 获取统计数据
        stats = report_data.get("statistics", {})
        ability = report_data.get("ability_analysis", {})
        weak = report_data.get("weak_points", {})
        recommendations = report_data.get("recommendations", {})
        ai_insights = report_data.get("ai_insights")

        # 构建报告内容
        lines = []

        # 标题
        title = report_data.get("title", "学习报告")
        period_start = report_data.get("period_start", "")
        period_end = report_data.get("period_end", "")

        if period_start and period_end:
            start_date = datetime.fromisoformat(period_start).strftime("%Y年%m月%d日")
            end_date = datetime.fromisoformat(period_end).strftime("%Y年%m月%d日")
            lines.append(f"# {title}")
            lines.append(f"\n> **统计周期**: {start_date} 至 {end_date}\n")
        else:
            lines.append(f"# {title}\n")

        lines.append("---\n")

        # 学习概况
        lines.append("## 学习概况")
        lines.append("")
        lines.append("### 整体统计")
        lines.append("")
        lines.append("| 统计项 | 数值 |")
        lines.append("|--------|------|")
        lines.append(f"| **练习次数** | {stats.get('total_practices', 0)} 次 |")
        lines.append(f"| **完成率** | {stats.get('completion_rate', 0)}% |")
        lines.append(f"| **平均正确率** | {stats.get('avg_correct_rate', 0)}% |")
        lines.append(f"| **学习时长** | {stats.get('total_duration_hours', 0):.1f} 小时 |")
        lines.append(f"| **错题数量** | {stats.get('total_mistakes', 0)} 道 |")
        lines.append("")

        # 学习状态分布
        status_dist = stats.get("mistake_by_status", {})
        if status_dist:
            lines.append("### 错题状态分布")
            lines.append("")
            for status, count in status_dist.items():
                status_map = {
                    "pending": "待复习",
                    "reviewing": "复习中",
                    "mastered": "已掌握",
                    "ignored": "已忽略",
                }
                lines.append(f"- **{status_map.get(status, status)}**: {count} 道")
            lines.append("")

        # 能力分析
        lines.append("---")
        lines.append("## 能力分析")
        lines.append("")

        # 能力雷达图数据（文本形式）
        radar = ability.get("ability_radar", [])
        if radar:
            lines.append("### 各项能力水平")
            lines.append("")
            lines.append("| 能力 | 水平 |")
            lines.append("|------|------|")
            for item in radar:
                lines.append(f"| {item['name']} | {item['value']:.0f} |")
            lines.append("")

        # 最强和最弱项
        strongest = ability.get("strongest_area")
        weakest = ability.get("weakest_area")

        if strongest or weakest:
            lines.append("### 能力评估")
            lines.append("")

            if strongest:
                lines.append(f"- **最强项**: {strongest['name']} (水平: {strongest['level']:.0f})")
            if weakest:
                lines.append(f"- **最弱项**: {weakest['name']} (水平: {weakest['level']:.0f})")
            lines.append("")

        # 薄弱环节分析
        lines.append("---")
        lines.append("## 薄弱环节分析")
        lines.append("")

        weak_points = weak.get("top_weak_points", [])
        if weak_points:
            lines.append("### 需要重点关注的知识点")
            lines.append("")
            for i, wp in enumerate(weak_points[:5], 1):
                lines.append(f"{i}. **{wp['point']}** - 出错 {wp['count']} 次")
            lines.append("")

        # 按主题的薄弱点
        by_topic = weak.get("by_topic", {})
        if by_topic:
            lines.append("### 按主题分类")
            lines.append("")
            for topic, count in sorted(by_topic.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{topic}**: {count} 个错题")
            lines.append("")

        # 学习建议
        lines.append("---")
        lines.append("## 学习建议")
        lines.append("")

        recs = recommendations.get("recommendations", [])
        if recs:
            lines.append("### 个性化建议")
            lines.append("")

            for rec in recs:
                priority_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢",
                }
                emoji = priority_emoji.get(rec.get("priority", "low"), "•")
                lines.append(f"{emoji} **{rec['title']}** ({rec.get('category', '建议')})")
                lines.append(f"   {rec['description']}")
                lines.append("")

        # AI 洞察
        if ai_insights:
            lines.append("---")
            lines.append("## AI 学习洞察")
            lines.append("")
            lines.append(f"{ai_insights}")
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append("")
        lines.append(f"*报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}*")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("> 💡 **提示**: 这份报告基于你的学习数据生成，建议定期查看以跟踪学习进步。")

        return "\n".join(lines)


def get_report_export_service(db: AsyncSession) -> ReportExportService:
    """获取报告导出服务实例"""
    return ReportExportService(db)
