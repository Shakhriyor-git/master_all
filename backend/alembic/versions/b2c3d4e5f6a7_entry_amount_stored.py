"""entries.amount — generated column emas, oddiy saqlanadigan ustun

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-01 10:00:00.000000

Sabab: `amount` GENERATED (quantity * unit_price) bo'lganida usta "3 qop
100 000" deb aniq jami summa kiritsa ham, unit_price = 33 333.33 ga
yaxlanib, amount = 99 999.99 chiqardi. Endi amount oddiy ustun — jami
summa aniq kiritilsa o'shandayligicha saqlanadi, aks holda listener
quantity * unit_price ni yozadi.

`DROP EXPRESSION` mavjud qiymatlarni saqlab qoladi (PostgreSQL 13+).
"""
from collections.abc import Sequence

from alembic import op


# revision identifikatorlari
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE entries ALTER COLUMN amount DROP EXPRESSION"
    )
    op.create_check_constraint(
        "ck_entries_amount_non_negative", "entries", "amount >= 0"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_entries_amount_non_negative", "entries", type_="check"
    )
    # Generated column'ga qaytarish — ustunni qayta yaratamiz.
    op.drop_column("entries", "amount")
    op.execute(
        "ALTER TABLE entries ADD COLUMN amount NUMERIC(14, 2) "
        "GENERATED ALWAYS AS (quantity * unit_price) STORED NOT NULL"
    )
