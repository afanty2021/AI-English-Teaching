# revision identifiers, used by Alembic.
revision = '20260203_1200'
down_revision = '6180530e656a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """添加错题本模型（mistakes表）"""

    # 创建mistakes表
    op.create_table(
        'mistakes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mistake_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('wrong_answer', sa.Text(), nullable=False),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('knowledge_points', postgresql.JSON(), nullable=True),
        sa.Column('difficulty_level', sa.String(length=50), nullable=True),
        sa.Column('topic', sa.String(length=100), nullable=True),
        sa.Column('mistake_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('ai_suggestion', sa.Text(), nullable=True),
        sa.Column('needs_ai_analysis', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ai_analysis', postgresql.JSON(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(), nullable=True),
        sa.Column('first_mistaken_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_mistaken_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], name=op.f('fk_mistakes_content_id_contents'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['practice_id'], ['practices.id'], name=op.f('fk_mistakes_practice_id_practices'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_mistakes_student_id_students'), ondelete='CASCADE')
    )

    # 创建索引
    op.create_index('ix_mistakes_id', 'mistakes', ['id'])
    op.create_index('ix_mistakes_student_id', 'mistakes', ['student_id'])
    op.create_index('ix_mistakes_practice_id', 'mistakes', ['practice_id'])
    op.create_index('ix_mistakes_content_id', 'mistakes', ['content_id'])
    op.create_index('ix_mistakes_mistake_type', 'mistakes', ['mistake_type'])
    op.create_index('ix_mistakes_status', 'mistakes', ['status'])
    op.create_index('ix_mistakes_topic', 'mistakes', ['topic'])


def downgrade() -> None:
    """删除错题本模型（mistakes表）"""

    # 删除索引
    op.drop_index('ix_mistakes_topic', table_name='mistakes')
    op.drop_index('ix_mistakes_status', table_name='mistakes')
    op.drop_index('ix_mistakes_mistake_type', table_name='mistakes')
    op.drop_index('ix_mistakes_content_id', table_name='mistakes')
    op.drop_index('ix_mistakes_practice_id', table_name='mistakes')
    op.drop_index('ix_mistakes_student_id', table_name='mistakes')
    op.drop_index('ix_mistakes_id', table_name='mistakes')

    # 删除表
    op.drop_table('mistakes')
