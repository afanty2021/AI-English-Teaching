# revision identifiers, used by Alembic.
revision = '20260204_2200'
down_revision = '20260203_2100'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """添加练习系统模型（questions、question_banks、practice_sessions表）"""

    # 创建 question_banks 表（题库）
    op.create_table(
        'question_banks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('practice_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty_level', sa.String(length=10), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_question_banks_created_by_users'), ondelete='CASCADE')
    )
    op.create_index('ix_question_banks_id', 'question_banks', ['id'])
    op.create_index('ix_question_banks_practice_type', 'question_banks', ['practice_type'])
    op.create_index('ix_question_banks_difficulty_level', 'question_banks', ['difficulty_level'])
    op.create_index('ix_question_banks_is_public', 'question_banks', ['is_public'])
    op.create_index('ix_question_banks_created_by', 'question_banks', ['created_by'])

    # 创建 questions 表（题目）
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('difficulty_level', sa.String(length=10), nullable=True),
        sa.Column('topic', sa.String(length=100), nullable=True),
        sa.Column('knowledge_points', postgresql.JSON(), nullable=True),
        sa.Column('options', postgresql.JSON(), nullable=True),
        sa.Column('correct_answer', postgresql.JSON(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('question_bank_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('passage_content', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.String(length=500), nullable=True),
        sa.Column('sample_answer', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['question_bank_id'], ['question_banks.id'], name=op.f('fk_questions_question_bank_id_question_banks'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_questions_created_by_users'), ondelete='SET NULL')
    )
    op.create_index('ix_questions_id', 'questions', ['id'])
    op.create_index('ix_questions_question_type', 'questions', ['question_type'])
    op.create_index('ix_questions_difficulty_level', 'questions', ['difficulty_level'])
    op.create_index('ix_questions_topic', 'questions', ['topic'])
    op.create_index('ix_questions_question_bank_id', 'questions', ['question_bank_id'])
    op.create_index('ix_questions_created_by', 'questions', ['created_by'])
    op.create_index('ix_questions_is_active', 'questions', ['is_active'])

    # 创建 practice_sessions 表（练习会话）
    op.create_table(
        'practice_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_bank_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('practice_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_question_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('answered_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answers', postgresql.JSON(), nullable=True),
        sa.Column('question_ids', postgresql.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('paused_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('practice_record_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('practice_record_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_practice_sessions_student_id_students'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_bank_id'], ['question_banks.id'], name=op.f('fk_practice_sessions_question_bank_id_question_banks'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['current_question_id'], ['questions.id'], name=op.f('fk_practice_sessions_current_question_id_questions'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['practice_record_id'], ['practices.id'], name=op.f('fk_practice_sessions_practice_record_id_practices'), ondelete='SET NULL')
    )
    op.create_index('ix_practice_sessions_id', 'practice_sessions', ['id'])
    op.create_index('ix_practice_sessions_student_id', 'practice_sessions', ['student_id'])
    op.create_index('ix_practice_sessions_question_bank_id', 'practice_sessions', ['question_bank_id'])
    op.create_index('ix_practice_sessions_practice_type', 'practice_sessions', ['practice_type'])
    op.create_index('ix_practice_sessions_status', 'practice_sessions', ['status'])
    op.create_index('ix_practice_sessions_current_question_id', 'practice_sessions', ['current_question_id'])
    op.create_index('ix_practice_sessions_practice_record_id', 'practice_sessions', ['practice_record_id'])


def downgrade() -> None:
    """删除练习系统模型（questions、question_banks、practice_sessions表）"""

    # 删除 practice_sessions 表
    op.drop_index('ix_practice_sessions_practice_record_id', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_current_question_id', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_status', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_practice_type', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_question_bank_id', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_student_id', table_name='practice_sessions')
    op.drop_index('ix_practice_sessions_id', table_name='practice_sessions')
    op.drop_table('practice_sessions')

    # 删除 questions 表
    op.drop_index('ix_questions_is_active', table_name='questions')
    op.drop_index('ix_questions_created_by', table_name='questions')
    op.drop_index('ix_questions_question_bank_id', table_name='questions')
    op.drop_index('ix_questions_topic', table_name='questions')
    op.drop_index('ix_questions_difficulty_level', table_name='questions')
    op.drop_index('ix_questions_question_type', table_name='questions')
    op.drop_index('ix_questions_id', table_name='questions')
    op.drop_table('questions')

    # 删除 question_banks 表
    op.drop_index('ix_question_banks_created_by', table_name='question_banks')
    op.drop_index('ix_question_banks_is_public', table_name='question_banks')
    op.drop_index('ix_question_banks_difficulty_level', table_name='question_banks')
    op.drop_index('ix_question_banks_practice_type', table_name='question_banks')
    op.drop_index('ix_question_banks_id', table_name='question_banks')
    op.drop_table('question_banks')
