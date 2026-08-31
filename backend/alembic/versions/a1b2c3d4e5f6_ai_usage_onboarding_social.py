"""ai_usage, users.onboarded, users.social_links

Revision ID: a1b2c3d4e5f6
Revises: 31545fdacdbb
Create Date: 2026-08-31 09:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifikatorlari
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '31545fdacdbb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'onboarded', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'social_links', postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"), nullable=False,
        ),
    )
    # Mavjud foydalanuvchilar allaqachon ishlagan — ularni qayta
    # tanishtirmaymiz (telefon bo'lmasa ham).
    op.execute("UPDATE users SET onboarded = true")

    op.create_table(
        'ai_usage',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column(
            'count', sa.Integer(), server_default='0', nullable=False,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'day', name='uq_ai_usage_user_day'),
    )


def downgrade() -> None:
    op.drop_table('ai_usage')
    op.drop_column('users', 'social_links')
    op.drop_column('users', 'onboarded')
