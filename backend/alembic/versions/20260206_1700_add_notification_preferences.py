"""
Add notification preferences table

Revision ID: 20260206_1700
Revises: 20260206_1600
Create Date: 2026-02-06 17:00:00

This migration adds:
1. notification_preferences table for storing user notification settings
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260206_1700'
down_revision = '20260206_1600'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column(
            'user_id',
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            'enable_share_notifications',
            sa.Boolean(),
            server_default='true',
            nullable=False
        ),
        sa.Column(
            'enable_comment_notifications',
            sa.Boolean(),
            server_default='true',
            nullable=False
        ),
        sa.Column(
            'enable_system_notifications',
            sa.Boolean(),
            server_default='true',
            nullable=False
        ),
        sa.Column(
            'notify_via_websocket',
            sa.Boolean(),
            server_default='true',
            nullable=False
        ),
        sa.Column(
            'notify_via_email',
            sa.Boolean(),
            server_default='false',
            nullable=False
        ),
        sa.Column(
            'email_frequency',
            sa.String(length=20),
            server_default='immediate',
            nullable=False
        ),
        sa.Column(
            'quiet_hours_start',
            sa.String(length=5),
            nullable=True
        ),
        sa.Column(
            'quiet_hours_end',
            sa.String(length=5),
            nullable=True
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_notification_preferences_user',
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'user_id',
            name='uq_notification_preferences_user'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_notification_preferences')
    )

    # Create index for user_id
    op.create_index(
        'ix_notification_preferences_user_id',
        'notification_preferences',
        ['user_id']
    )


def downgrade() -> None:
    # Drop index for notification_preferences
    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')

    # Drop notification_preferences table
    op.drop_table('notification_preferences')
