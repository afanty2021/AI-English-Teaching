"""
Add export system tables

Revision ID: 20260207_1000
Revises: 20260206_1700
Create Date: 2026-02-07 10:00:00

This migration adds:
1. export_templates table for storing export templates
2. export_tasks table for managing export jobs
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260207_1000'
down_revision = '20260206_1700'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== export_templates table ====================
    op.create_table(
        'export_templates',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('template_path', sa.String(500), nullable=False),
        sa.Column('preview_path', sa.String(500), nullable=True),
        sa.Column(
            'variables',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for export_templates
    op.create_index('ix_export_templates_id', 'export_templates', ['id'])
    op.create_index('ix_export_templates_name', 'export_templates', ['name'])
    op.create_index('ix_export_templates_format', 'export_templates', ['format'])
    op.create_index('ix_export_templates_is_system', 'export_templates', ['is_system'])
    op.create_index('ix_export_templates_is_active', 'export_templates', ['is_active'])
    op.create_index('ix_export_templates_created_by', 'export_templates', ['created_by'])
    op.create_index('ix_export_templates_organization_id', 'export_templates', ['organization_id'])

    # ==================== export_tasks table ====================
    op.create_table(
        'export_tasks',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column('lesson_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column(
            'options',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('download_url', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['export_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for export_tasks
    op.create_index('ix_export_tasks_id', 'export_tasks', ['id'])
    op.create_index('ix_export_tasks_lesson_id', 'export_tasks', ['lesson_id'])
    op.create_index('ix_export_tasks_template_id', 'export_tasks', ['template_id'])
    op.create_index('ix_export_tasks_created_by', 'export_tasks', ['created_by'])
    op.create_index('ix_export_tasks_status', 'export_tasks', ['status'])


def downgrade() -> None:
    # Drop export_tasks table
    op.drop_index('ix_export_tasks_status', table_name='export_tasks')
    op.drop_index('ix_export_tasks_created_by', table_name='export_tasks')
    op.drop_index('ix_export_tasks_template_id', table_name='export_tasks')
    op.drop_index('ix_export_tasks_lesson_id', table_name='export_tasks')
    op.drop_index('ix_export_tasks_id', table_name='export_tasks')
    op.drop_table('export_tasks')

    # Drop export_templates table
    op.drop_index('ix_export_templates_organization_id', table_name='export_templates')
    op.drop_index('ix_export_templates_created_by', table_name='export_templates')
    op.drop_index('ix_export_templates_is_active', table_name='export_templates')
    op.drop_index('ix_export_templates_is_system', table_name='export_templates')
    op.drop_index('ix_export_templates_format', table_name='export_templates')
    op.drop_index('ix_export_templates_name', table_name='export_templates')
    op.drop_index('ix_export_templates_id', table_name='export_templates')
    op.drop_table('export_templates')
