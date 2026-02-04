"""add learning report model

Revision ID: 20260203_2100
Revises: 20260203_1200
Create Date: 2026-02-03 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '20260203_2100'
down_revision = '20260203_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 learning_reports 表
    op.create_table(
        'learning_reports',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'student_id',
            UUID(as_uuid=True),
            sa.ForeignKey('students.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('statistics', JSON, nullable=True),
        sa.Column('ability_analysis', JSON, nullable=True),
        sa.Column('weak_points', JSON, nullable=True),
        sa.Column('recommendations', JSON, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('ai_insights', JSON, nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
    )

    # 创建索引
    op.create_index('ix_learning_reports_id', 'learning_reports', ['id'])
    op.create_index('ix_learning_reports_student_id', 'learning_reports', ['student_id'])
    op.create_index('ix_learning_reports_report_type', 'learning_reports', ['report_type'])
    op.create_index('ix_learning_reports_period_start', 'learning_reports', ['period_start'])
    op.create_index('ix_learning_reports_period_end', 'learning_reports', ['period_end'])
    op.create_index('ix_learning_reports_status', 'learning_reports', ['status'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_learning_reports_status', table_name='learning_reports')
    op.drop_index('ix_learning_reports_period_end', table_name='learning_reports')
    op.drop_index('ix_learning_reports_period_start', table_name='learning_reports')
    op.drop_index('ix_learning_reports_report_type', table_name='learning_reports')
    op.drop_index('ix_learning_reports_student_id', table_name='learning_reports')
    op.drop_index('ix_learning_reports_id', table_name='learning_reports')

    # 删除表
    op.drop_table('learning_reports')
