"""
错题导出服务 - AI英语教学系统
支持将错题导出为Markdown、PDF、Word格式
"""
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import Mistake, MistakeStatus, MistakeType
from app.models.student import Student
from app.models.user import User

# 导入 Word 渲染服务
try:
    from app.services.word_renderer_service import get_word_renderer_service
    WORD_SUPPORT = True
except ImportError:
    WORD_SUPPORT = False
    get_word_renderer_service = None


class MistakeExportService:
    """
    错题导出服务类

    核心功能：
    1. 收集并组织错题数据
    2. 生成学习报告统计数据
    3. 渲染Markdown格式的学习报告
    4. 支持格式转换（PDF、Word）
    """

    def __init__(self, db: AsyncSession):
        """
        初始化导出服务

        Args:
            db: 数据库会话
        """
        self.db = db
        # 初始化Jinja2环境
        self.template_env = Environment(
            loader=FileSystemLoader('app/templates'),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 注册自定义过滤器
        self.template_env.filters['get_status_name'] = self._get_status_name
        self.template_env.filters['get_type_name'] = self._get_type_name

        # 初始化 Word 渲染器
        self.word_renderer = None
        if WORD_SUPPORT and get_word_renderer_service:
            try:
                self.word_renderer = get_word_renderer_service()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to initialize Word renderer: {e}. Word export will be disabled."
                )

    async def prepare_export_data(
        self,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
        single_mistake_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        准备导出数据

        Args:
            student_id: 学生ID
            filters: 筛选条件（status, mistake_type, topic等）
            single_mistake_id: 单个错题ID（导出单个错题时使用）

        Returns:
            包含所有导出所需数据的字典
        """
        # 获取学生信息
        student = await self._get_student_info(student_id)

        # 获取错题数据
        if single_mistake_id:
            mistakes = await self._get_single_mistake(single_mistake_id, student_id)
        else:
            mistakes = await self._get_filtered_mistakes(student_id, filters)

        # 生成统计数据
        statistics = await self._generate_export_statistics(mistakes)

        # 按类别组织错题
        categorized_mistakes = self._categorize_mistakes(mistakes)

        # 生成目录
        table_of_contents = self._generate_table_of_contents(
            categorized_mistakes,
            single_mistake_mode=bool(single_mistake_id)
        )

        return {
            'student': student,
            'export_date': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            'statistics': statistics,
            'mistakes': mistakes,
            'categorized_mistakes': categorized_mistakes,
            'table_of_contents': table_of_contents,
            'is_single_export': bool(single_mistake_id),
        }

    async def render_markdown_report(
        self,
        export_data: Dict[str, Any],
    ) -> str:
        """
        渲染Markdown格式的学习报告

        Args:
            export_data: 导出数据字典

        Returns:
            Markdown格式的报告文本
        """
        template = self.template_env.get_template('mistake_report.md.j2')

        markdown_content = template.render(**export_data)

        return markdown_content

    async def export_as_markdown(
        self,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
        single_mistake_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        导出为Markdown格式

        Args:
            student_id: 学生ID
            filters: 筛选条件
            single_mistake_id: 单个错题ID

        Returns:
            (文件名, Markdown内容)
        """
        # 准备数据
        export_data = await self.prepare_export_data(
            student_id, filters, single_mistake_id
        )

        # 渲染Markdown
        markdown_content = await self.render_markdown_report(export_data)

        # 生成文件名
        filename = self._generate_filename(export_data, 'md')

        return filename, markdown_content

    async def export_as_pdf(
        self,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
        single_mistake_id: Optional[str] = None,
    ) -> tuple[str, bytes]:
        """
        导出为PDF格式

        Args:
            student_id: 学生ID
            filters: 筛选条件
            single_mistake_id: 单个错题ID

        Returns:
            (文件名, PDF字节数据)

        Raises:
            RuntimeError: PDF 渲染服务不可用
        """
        # 检查 PDF 渲染器是否可用
        if self.pdf_renderer is None:
            raise RuntimeError(
                "PDF export is not available. Please install required dependencies: "
                "markdown2, weasyprint"
            )

        # 先生成Markdown
        filename_md, markdown_content = await self.export_as_markdown(
            student_id, filters, single_mistake_id
        )

        # 准备导出数据以获取标题
        export_data = await self.prepare_export_data(
            student_id, filters, single_mistake_id
        )

        # 生成 PDF 标题
        if single_mistake_id:
            mistake = export_data['mistakes'][0]
            title = f"{export_data['student']['name']} - 错题详情"
        else:
            title = f"{export_data['student']['name']}的错题本"

        # Markdown 转 PDF
        filename = filename_md.replace('.md', '.pdf')
        pdf_bytes = await self.pdf_renderer.render_markdown_to_pdf(
            markdown_content=markdown_content,
            title=title,
        )

        return filename, pdf_bytes

    async def export_as_word(
        self,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
        single_mistake_id: Optional[str] = None,
    ) -> tuple[str, bytes]:
        """
        导出为Word格式

        Args:
            student_id: 学生ID
            filters: 筛选条件
            single_mistake_id: 单个错题ID

        Returns:
            (文件名, Word字节数据)

        Raises:
            RuntimeError: Word 渲染服务不可用
        """
        # 检查 Word 渲染器是否可用
        if self.word_renderer is None:
            raise RuntimeError(
                "Word export is not available. Please install required dependencies: "
                "python-docx"
            )

        # 获取学生信息用于标题
        student_info = await self._get_student_info(student_id)
        student_name = student_info.get('name', '学生')

        # 先生成Markdown
        filename_md, markdown_content = await self.export_as_markdown(
            student_id, filters, single_mistake_id
        )

        # 生成标题
        if single_mistake_id:
            title = f"{student_name} - 错题详情"
        else:
            title = f"{student_name}的错题本"

        # Markdown转Word
        filename = filename_md.replace('.md', '.docx')
        docx_bytes = self.word_renderer.markdown_to_docx_bytes(
            markdown_content=markdown_content,
            title=title,
            author=student_name,
        )

        return filename, docx_bytes

    async def _get_student_info(self, student_id: str) -> Dict[str, Any]:
        """获取学生信息"""
        import uuid

        student_uuid = uuid.UUID(student_id)
        query = select(Student).where(Student.id == student_uuid)
        result = await self.db.execute(query)
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 获取用户信息
        user_query = select(User).where(User.id == student.user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        return {
            'id': str(student.id),
            'name': user.full_name if user else '未知',
            'english_name': student.student_no if student.student_no else '',
            'level': student.current_cefr_level if student.current_cefr_level else 'N/A',
            'student_id': student.student_no if student.student_no else '',
        }

    async def _get_single_mistake(
        self,
        mistake_id: str,
        student_id: str,
    ) -> List[Mistake]:
        """获取单个错题"""
        import uuid

        mistake_uuid = uuid.UUID(mistake_id)
        student_uuid = uuid.UUID(student_id)

        query = select(Mistake).where(
            Mistake.id == mistake_uuid,
            Mistake.student_id == student_uuid,
        )
        result = await self.db.execute(query)
        mistake = result.scalar_one_or_none()

        if not mistake:
            raise ValueError(f"错题不存在: {mistake_id}")

        return [mistake]

    async def _get_filtered_mistakes(
        self,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Mistake]:
        """获取筛选后的错题列表"""
        import uuid

        student_uuid = uuid.UUID(student_id)
        query = select(Mistake).where(Mistake.student_id == student_uuid)

        # 应用筛选条件
        if filters:
            if 'status' in filters and filters['status']:
                query = query.where(Mistake.status == filters['status'])

            if 'mistake_type' in filters and filters['mistake_type']:
                query = query.where(Mistake.mistake_type == filters['mistake_type'])

            if 'topic' in filters and filters['topic']:
                query = query.where(Mistake.topic == filters['topic'])

            if 'knowledge_point' in filters and filters['knowledge_point']:
                # knowledge_points是JSON数组，使用包含查询
                query = query.where(
                    Mistake.knowledge_points.contains([filters['knowledge_point']])
                )

        # 按更新时间倒序排列
        query = query.order_by(Mistake.updated_at.desc())

        result = await self.db.execute(query)
        mistakes = result.scalars().all()

        return list(mistakes)

    async def _generate_export_statistics(
        self,
        mistakes: List[Mistake],
    ) -> Dict[str, Any]:
        """生成导出统计数据"""
        total = len(mistakes)

        if total == 0:
            return {
                'total': 0,
                'by_status': {},
                'by_type': {},
                'mastery_rate': 0,
                'avg_mistake_count': 0,
            }

        # 按状态统计
        by_status = {}
        for status in MistakeStatus:
            count = sum(1 for m in mistakes if m.status == status.value)
            if count > 0:
                status_name = self._get_status_name(status.value)
                by_status[status_name] = {
                    'count': count,
                    'percentage': round(count / total * 100, 1),
                }

        # 按类型统计
        by_type = {}
        for m in mistakes:
            type_name = self._get_type_name(m.mistake_type)
            if type_name not in by_type:
                by_type[type_name] = 0
            by_type[type_name] += 1

        # 计算掌握率
        mastered_count = sum(1 for m in mistakes if m.is_mastered)
        mastery_rate = round(mastered_count / total * 100, 1) if total > 0 else 0

        # 平均错误次数
        avg_mistake_count = round(
            sum(m.mistake_count for m in mistakes) / total, 1
        ) if total > 0 else 0

        return {
            'total': total,
            'by_status': by_status,
            'by_type': by_type,
            'mastery_rate': mastery_rate,
            'avg_mistake_count': avg_mistake_count,
        }

    def _categorize_mistakes(
        self,
        mistakes: List[Mistake],
    ) -> Dict[str, List[Mistake]]:
        """按类别组织错题"""
        categorized = {
            '按状态': {},
            '按类型': {},
            '按主题': {},
        }

        # 按状态分类
        for status in MistakeStatus:
            status_mistakes = [m for m in mistakes if m.status == status.value]
            if status_mistakes:
                status_name = self._get_status_name(status.value)
                categorized['按状态'][status_name] = status_mistakes

        # 按类型分类
        for mistake in mistakes:
            type_name = self._get_type_name(mistake.mistake_type)
            if type_name not in categorized['按类型']:
                categorized['按类型'][type_name] = []
            categorized['按类型'][type_name].append(mistake)

        # 按主题分类
        for mistake in mistakes:
            topic = mistake.topic or '未分类'
            if topic not in categorized['按主题']:
                categorized['按主题'][topic] = []
            categorized['按主题'][topic].append(mistake)

        return categorized

    def _generate_table_of_contents(
        self,
        categorized_mistakes: Dict[str, Dict[str, List[Mistake]]],
        single_mistake_mode: bool = False,
    ) -> List[Dict[str, Any]]:
        """生成目录"""
        toc = []

        toc.append({
            'title': '一、学习概况',
            'anchor': '学习概况',
            'level': 1,
        })

        toc.append({
            'title': '二、错题统计',
            'anchor': '错题统计',
            'level': 1,
        })

        if not single_mistake_mode:
            toc.append({
                'title': '三、错题详情',
                'anchor': '错题详情',
                'level': 1,
            })

            # 添加分类章节
            section_num = 1
            for category, items in categorized_mistakes.items():
                if items:
                    toc.append({
                        'title': f'3.{section_num} 按{category.split("按")[1]}分类',
                        'anchor': f'按{category.split("按")[1]}分类',
                        'level': 2,
                    })
                    section_num += 1
        else:
            toc.append({
                'title': '三、错题详情',
                'anchor': '错题详情',
                'level': 1,
            })

        toc.append({
            'title': '四、学习建议',
            'anchor': '学习建议',
            'level': 1,
        })

        return toc

    def _generate_filename(
        self,
        export_data: Dict[str, Any],
        extension: str,
    ) -> str:
        """生成文件名"""
        student_name = export_data['student']['name']
        export_date = datetime.now().strftime('%Y%m%d')

        if export_data['is_single_export']:
            mistake = export_data['mistakes'][0]
            return f"{student_name}_错题_{mistake.id.hex[:8]}_{export_date}.{extension}"
        else:
            return f"{student_name}_错题本_{export_date}.{extension}"

    @staticmethod
    def _get_status_name(status: str) -> str:
        """获取状态中文名称"""
        status_names = {
            'pending': '待复习',
            'reviewing': '复习中',
            'mastered': '已掌握',
            'ignored': '已忽略',
        }
        return status_names.get(status, status)

    @staticmethod
    def _get_type_name(mistake_type: str) -> str:
        """获取类型中文名称"""
        type_names = {
            'grammar': '语法',
            'vocabulary': '词汇',
            'reading': '阅读理解',
            'listening': '听力理解',
            'writing': '写作',
            'speaking': '口语',
            'pronunciation': '发音',
            'comprehension': '理解',
        }
        return type_names.get(mistake_type, mistake_type)


# 创建服务工厂函数
def get_mistake_export_service(db: AsyncSession) -> MistakeExportService:
    """
    获取错题导出服务实例

    Args:
        db: 数据库会话

    Returns:
        MistakeExportService: 错题导出服务实例
    """
    return MistakeExportService(db)
