# revision identifiers, used by Alembic.
revision = '20260206_add_query_indexes'
down_revision = '20260204_2200'
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    """添加查询优化索引

    为常用查询字段添加索引以提升查询性能：
    - practices.created_at: 按时间查询练习记录
    - mistakes.topic: 按知识点分类查询错题
    - students.target_exam: 按目标考试筛选学生
    """
    # 为练习记录添加时间索引
    op.create_index('ix_practices_created_at', 'practices', ['created_at'])

    # 为错题本添加主题索引
    op.create_index('ix_mistakes_topic', 'mistakes', ['topic'])

    # 为学生添加目标考试索引
    op.create_index('ix_students_target_exam', 'students', ['target_exam'])


def downgrade() -> None:
    """移除添加的索引"""
    op.drop_index('ix_students_target_exam', 'students')
    op.drop_index('ix_mistakes_topic', 'mistakes')
    op.drop_index('ix_practices_created_at', 'practices')
