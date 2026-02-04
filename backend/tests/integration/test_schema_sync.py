"""
数据库模式同步测试

验证 SQLAlchemy 模型定义与实际数据库表结构保持一致
防止因模型与数据库不匹配导致的运行时错误

这类错误通常在:
- 手动修改数据库结构后忘记更新模型
- 运行 Alembic 迁移后模型定义不同步
- 多人开发时数据库状态不一致
"""
import asyncio
from typing import Dict, List, Set, Tuple
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import class_mapper, ColumnProperty

from app.db.base import Base
from app.models import (
    User, Student, Teacher, Organization,
    Practice, Mistake, Conversation, Content,
    LearningReport, LessonPlan, KnowledgeGraph
)
from tests.conftest import TEST_DATABASE_URL


# ============================================================================
# 表结构同步测试
# ============================================================================

@pytest.mark.asyncio
class TestDatabaseSchemaSync:
    """
    数据库模式同步测试

    确保:
    1. 所有模型都有对应的数据库表
    2. 表结构与模型定义一致（列名、类型、约束等）
    3. 外键关系正确设置
    """

    async def test_all_models_have_tables(self, db_engine: AsyncEngine):
        """
        测试所有模型都有对应的数据库表

        如果这个测试失败，说明:
        1. 模型定义了但没有对应的数据库表
        2. 需要运行 Alembic 迁移或手动创建表
        """
        async with db_engine.connect() as conn:
            # 获取数据库中的所有表
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            db_tables = {row[0] for row in result}

        # 获取所有模型定义的表名
        model_tables = {mapper.tables[0].name for mapper in Base.registry.mappers}

        # 检查是否有模型没有对应的表
        missing_tables = model_tables - db_tables

        if missing_tables:
            pytest.fail(
                f"以下模型没有对应的数据库表: {missing_tables}\n"
                f"请运行: alembic upgrade head"
            )

    async def test_practice_table_schema(self, db_engine: AsyncEngine):
        """
        测试 practices 表结构与 Practice 模型一致

        这是之前出现问题的地方，需要特别关注:
        - completed_questions 列存在
        - correct_rate 列存在
        - started_at 和 completed_at 列存在
        """
        async with db_engine.connect() as conn:
            # 获取 practices 表的列信息
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'practices'
                ORDER BY ordinal_position
            """))
            db_columns = {row[0]: (row[1], row[2]) for row in result}

        # 获取 Practice 模型的列
        model_columns = {
            prop.key: (
                prop.columns[0].type.python_type.__name__,
                prop.columns[0].nullable
            )
            for prop in class_mapper(Practice).iterate_properties
            if isinstance(prop, ColumnProperty)
        }

        # 检查关键字段是否存在
        required_columns = {
            'completed_questions', 'correct_rate', 'difficulty_level',
            'topic', 'time_spent', 'started_at', 'completed_at',
            'result_details', 'graph_update', 'graph_updated', 'extra_metadata'
        }

        missing_columns = required_columns - set(db_columns.keys())

        if missing_columns:
            pytest.fail(
                f"practices 表缺少以下列: {missing_columns}\n"
                f"当前数据库列: {list(db_columns.keys())}\n"
                f"请运行迁移添加缺失的列"
            )

    async def test_learning_reports_table_exists(self, db_engine: AsyncEngine):
        """
        测试 learning_reports 表存在且结构正确

        这是学习报告功能所需的表
        """
        async with db_engine.connect() as conn:
            # 检查表是否存在
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'learning_reports'
                )
            """))
            exists = result.scalar()

        assert exists, "learning_reports 表不存在，请运行迁移创建"

        # 检查关键列
        async with db_engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'learning_reports'
            """))
            columns = {row[0] for row in result}

        required_columns = {
            'id', 'student_id', 'report_type', 'period_start', 'period_end',
            'statistics', 'ability_analysis', 'weak_points', 'recommendations',
            'status', 'ai_insights', 'title', 'description'
        }

        missing = required_columns - columns
        assert not missing, f"learning_reports 表缺少列: {missing}"

    async def test_foreign_keys_valid(self, db_engine: AsyncEngine):
        """
        测试外键约束正确设置

        确保:
        - students.user_id 引用 users.id
        - practices.student_id 引用 students.id
        - practices.content_id 引用 contents.id
        - mistakes.student_id 引用 students.id
        - conversations.student_id 引用 students.id
        """
        async with db_engine.connect() as conn:
            # 获取所有外键约束
            result = await conn.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name, kcu.column_name
            """))
            foreign_keys = {(row[0], row[1]): (row[2], row[3]) for row in result}

        # 验证关键外键
        required_fks = {
            ('students', 'user_id'): ('users', 'id'),
            ('practices', 'student_id'): ('students', 'id'),
            ('practices', 'content_id'): ('contents', 'id'),
            ('mistakes', 'student_id'): ('students', 'id'),
            ('conversations', 'student_id'): ('students', 'id'),
            ('learning_reports', 'student_id'): ('students', 'id'),
        }

        for (table, column), (ref_table, ref_column) in required_fks.items():
            key = (table, column)
            if key not in foreign_keys:
                pytest.fail(f"缺少外键约束: {table}.{column} -> {ref_table}.{ref_column}")
            else:
                actual_ref = foreign_keys[key]
                assert actual_ref == (ref_table, ref_column), \
                    f"外键 {table}.{column} 引用错误: 期望 {ref_table}.{ref_column}, 实际 {actual_ref}"

    async def test_json_columns_exist(self, db_engine: AsyncEngine):
        """
        测试 JSON 类型列存在

        这些列存储复杂结构数据:
        - students.knowledge_graph
        - practices.answers, result_details
        - conversations.messages
        - learning_reports.statistics, recommendations
        """
        async with db_engine.connect() as conn:
            # 检查 JSON 列
            result = await conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE data_type IN ('json', 'jsonb')
                ORDER BY table_name, column_name
            """))
            json_columns = {(row[0], row[1]): row[2] for row in result}

        # 关键 JSON 列
        required_json_columns = {
            ('students', 'knowledge_graph'): 'jsonb',
            ('practices', 'answers'): 'jsonb',
            ('practices', 'result_details'): 'json',
            ('practices', 'graph_update'): 'json',
            ('practices', 'extra_metadata'): 'json',
            ('conversations', 'messages'): 'jsonb',
            ('learning_reports', 'statistics'): 'json',
            ('learning_reports', 'ability_analysis'): 'json',
            ('learning_reports', 'weak_points'): 'json',
            ('learning_reports', 'recommendations'): 'json',
            ('learning_reports', 'ai_insights'): 'json',
        }

        for (table, column), expected_type in required_json_columns.items():
            key = (table, column)
            if key not in json_columns:
                pytest.fail(f"缺少 JSON 列: {table}.{column}")


# ============================================================================
# 迁移状态测试
# ============================================================================

@pytest.mark.asyncio
class TestMigrationStatus:
    """
    迁移状态测试

    确保 Alembic 迁移已正确应用到数据库
    """

    async def test_alembic_version_table_exists(self, db_engine: AsyncEngine):
        """测试 alembic_version 表存在"""
        async with db_engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            exists = result.scalar()

        assert exists, "alembic_version 表不存在，数据库可能未通过 Alembic 初始化"

    async def test_no_orphan_tables(self, db_engine: AsyncEngine):
        """
        测试没有孤立表

        孤立表是指: 在数据库中存在但模型中没有定义的表
        可能是因为:
        1. 删除了模型但忘记删除对应的表
        2. 重命名了表但旧表还在
        """
        async with db_engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            db_tables = {row[0] for row in result}

        # 排除系统表和已知的外部表
        excluded = {'alembic_version', 'spatial_ref_sys'}
        db_tables -= excluded

        # 获取模型定义的表
        model_tables = {mapper.tables[0].name for mapper in Base.registry.mappers}

        # 孤立表
        orphan_tables = db_tables - model_tables

        if orphan_tables:
            # 某些情况下可能有合理的孤立表（如审计表）
            # 这里只是警告，不失败
            print(f"\n警告: 发现可能的孤立表: {orphan_tables}")
            print("如果这些表是有意保留的，请将它们添加到 excluded 列表中")


# ============================================================================
# 数据完整性测试
# ============================================================================

@pytest.mark.asyncio
class TestDataIntegrity:
    """
    数据完整性测试

    确保关键业务流程的数据完整性
    """

    async def test_student_creation_flow(self, db: AsyncSession):
        """
        测试学生创建流程的数据完整性

        确保:
        1. 可以创建用户
        2. 可以关联学生档案
        3. 外键关系正确
        """
        from app.models import User, Student
        from app.core.security import get_password_hash

        # 创建用户
        user_id = uuid4()
        user = User(
            id=user_id,
            username="test_student_flow",
            email="flow@test.com",
            hashed_password=get_password_hash("Test1234"),
            role="student",
            is_active=True
        )
        db.add(user)
        await db.commit()

        # 创建学生档案
        student = Student(
            id=uuid4(),
            user_id=user_id,
            grade_level="B1",
            learning_goals=["提高口语"]
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

        # 验证关联
        assert student.user_id == user_id
        assert student.user.username == "test_student_flow"

    async def test_learning_report_creation(self, db: AsyncSession):
        """
        测试学习报告创建的数据完整性

        确保 JSON 字段可以正确存储和检索
        """
        from app.models import LearningReport
        from datetime import datetime
        import uuid

        # 创建测试数据
        report = LearningReport(
            id=uuid.uuid4(),
            student_id=uuid.uuid4(),  # 使用虚拟ID，实际应有外键约束
            report_type="weekly",
            period_start=datetime.now(),
            period_end=datetime.now(),
            status="completed",
            statistics={
                "total_practices": 10,
                "completed_practices": 8,
                "completion_rate": 0.8
            },
            ability_analysis={
                "current_abilities": {"reading": 0.7, "listening": 0.6},
                "ability_radar": [{"name": "阅读", "value": 0.7}]
            },
            recommendations={
                "recommendations": [
                    {"category": "学习习惯", "priority": "high", "title": "提高练习频率"}
                ]
            }
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        # 验证 JSON 数据正确存储
        assert report.statistics["total_practices"] == 10
        assert report.ability_analysis["ability_radar"][0]["value"] == 0.7
        assert len(report.recommendations["recommendations"]) == 1
