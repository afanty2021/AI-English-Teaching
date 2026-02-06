"""
Add lesson plan sharing functionality

Revision ID: 20260206_1600
Revises: 20260206_add_query_indexes
Create Date: 2026-02-06 16:00:00

This migration adds:
1. lesson_plan_shares table for managing教案分享
2. Additional fields to lesson_plans table for sharing metadata
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260206_1600'
down_revision = '20260206_add_query_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lesson_plan_shares table
    op.create_table(
        'lesson_plan_shares',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column(
            'lesson_plan_id',
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            'shared_by',
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            'shared_to',
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            'permission',
            sa.String(length=20),
            nullable=False,
            server_default='view'
        ),
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='pending'
        ),
        sa.Column(
            'message',
            sa.Text(),
            nullable=True
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=True
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['lesson_plan_id'],
            ['lesson_plans.id'],
            name='fk_shares_lesson_plan',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['shared_by'],
            ['users.id'],
            name='fk_shares_shared_by',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['shared_to'],
            ['users.id'],
            name='fk_shares_shared_to',
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'lesson_plan_id',
            'shared_to',
            name='uq_share_lesson_user'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_lesson_plan_shares')
    )

    # Create indexes for lesson_plan_shares
    op.create_index(
        'ix_shares_shared_to',
        'lesson_plan_shares',
        ['shared_to']
    )
    op.create_index(
        'ix_shares_status',
        'lesson_plan_shares',
        ['status']
    )
    op.create_index(
        'ix_shares_lesson_plan_id',
        'lesson_plan_shares',
        ['lesson_plan_id']
    )

    # Add columns to lesson_plans table
    op.add_column(
        'lesson_plans',
        sa.Column(
            'is_shared',
            sa.Boolean(),
            server_default='false',
            nullable=False
        )
    )
    op.add_column(
        'lesson_plans',
        sa.Column(
            'is_public',
            sa.Boolean(),
            server_default='false',
            nullable=False
        )
    )
    op.add_column(
        'lesson_plans',
        sa.Column(
            'share_count',
            sa.Integer(),
            server_default='0',
            nullable=False
        )
    )
    op.add_column(
        'lesson_plans',
        sa.Column(
            'forked_from',
            sa.UUID(),
            nullable=True
        )
    )
    op.add_column(
        'lesson_plans',
        sa.Column(
            'fork_count',
            sa.Integer(),
            server_default='0',
            nullable=False
        )
    )

    # Create index for is_shared column
    op.create_index(
        'ix_lesson_plans_is_shared',
        'lesson_plans',
        ['is_shared']
    )


def downgrade() -> None:
    # Drop indexes for lesson_plans
    op.drop_index('ix_lesson_plans_is_shared', table_name='lesson_plans')

    # Remove columns from lesson_plans table
    op.drop_column('lesson_plans', 'fork_count')
    op.drop_column('lesson_plans', 'forked_from')
    op.drop_column('lesson_plans', 'share_count')
    op.drop_column('lesson_plans', 'is_public')
    op.drop_column('lesson_plans', 'is_shared')

    # Drop indexes for lesson_plan_shares
    op.drop_index('ix_shares_lesson_plan_id', table_name='lesson_plan_shares')
    op.drop_index('ix_shares_status', table_name='lesson_plan_shares')
    op.drop_index('ix_shares_shared_to', table_name='lesson_plan_shares')

    # Drop lesson_plan_shares table
    op.drop_table('lesson_plan_shares')
