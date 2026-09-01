"""Musiqa: users.music_enabled + user_tracks jadvali

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-01 18:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: str | None = 'e5f6a7b8c9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'music_enabled', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
    )
    op.create_table(
        'user_tracks',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('original_name', sa.String(length=200), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column(
            'sort_order', sa.Integer(), server_default='0', nullable=False,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_user_tracks_user_id_sort_order',
        'user_tracks',
        ['user_id', 'sort_order'],
    )


def downgrade() -> None:
    op.drop_index('ix_user_tracks_user_id_sort_order', table_name='user_tracks')
    op.drop_table('user_tracks')
    op.drop_column('users', 'music_enabled')
