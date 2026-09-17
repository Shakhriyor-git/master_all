"""Brigada: partners + partner_payments jadvallari

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-17 12:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: str | None = 'f6a7b8c9d0e1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'partners',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('note', sa.String(length=300), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_partners_user_id_deleted_at',
        'partners',
        ['user_id', 'deleted_at'],
    )

    op.create_table(
        'partner_payments',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('partner_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'amount', sa.Numeric(precision=14, scale=2), nullable=False,
        ),
        sa.Column(
            'method', sa.String(length=20),
            server_default='cash', nullable=False,
        ),
        sa.Column('note', sa.String(length=300), nullable=True),
        sa.Column(
            'paid_at', sa.Date(),
            server_default=sa.text('CURRENT_DATE'), nullable=False,
        ),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.CheckConstraint(
            'amount > 0', name='ck_partner_payments_amount_positive'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['partner_id'], ['partners.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_partner_payments_user_id_partner_id_paid_at',
        'partner_payments',
        ['user_id', 'partner_id', sa.text('paid_at DESC')],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_partner_payments_user_id_partner_id_paid_at',
        table_name='partner_payments',
    )
    op.drop_table('partner_payments')
    op.drop_index('ix_partners_user_id_deleted_at', table_name='partners')
    op.drop_table('partners')
