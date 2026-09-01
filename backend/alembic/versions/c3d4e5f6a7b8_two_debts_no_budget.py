"""Budjet tushunchasi olib tashlandi — ikkita oddiy qarz

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-01 12:00:00.000000

Uchta ma'lumot tuzatishi:

1. payments.purpose: 'budget' -> 'material'
   "Mijoz budjeti" amalda ishlatilmadi. Endi mijoz material qarziga
   alohida to'laydi — o'sha to'lovlar purpose='material'.

2. entries.paid_by: 'client' -> 'master' (HAMMASI)
   Ilgari 'client' "mijoz puli bilan to'landi" degani edi, endi "mijoz
   o'zi borib sotib oldi". Eski yozuvlarni usta olgan — 'master' bo'lishi
   kerak. Downgrade'da QAYTARILMAYDI: ma'no o'zgargan, orqaga qaytarish
   ma'lumotni buzadi.

3. categories.name: bosh/oxirgi bo'shliqlar tozalanadi ("Mebel " -> "Mebel").
   Trim natijasi mavjud nom bilan to'qnashsa — o'sha qator tegilmaydi
   (usta o'zi birlashtiradi).
"""
from collections.abc import Sequence

from alembic import op


# revision identifikatorlari
revision: str = 'c3d4e5f6a7b8'
down_revision: str | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE payments SET purpose = 'material' WHERE purpose = 'budget'"
    )
    # paid_by 'client' -> 'master'. Xarajatlar uchun is_billable=false ham
    # kerak, aks holda ck_entries_master_expense_not_billable buziladi
    # (usta xarajati mijozga qayta hisoblanmaydi).
    op.execute(
        """
        UPDATE entries
        SET paid_by = 'master',
            is_billable = CASE
                WHEN kind = 'expense' THEN false
                ELSE is_billable
            END
        WHERE paid_by = 'client'
        """
    )
    op.execute(
        """
        UPDATE categories c
        SET name = btrim(c.name)
        WHERE c.name <> btrim(c.name)
          AND NOT EXISTS (
              SELECT 1 FROM categories d
              WHERE d.user_id = c.user_id
                AND d.kind = c.kind
                AND d.name = btrim(c.name)
                AND d.id <> c.id
          )
        """
    )


def downgrade() -> None:
    # purpose nomini orqaga qaytaramiz; paid_by va name tozalash esa
    # QAYTARILMAYDI (ma'no o'zgargan / ma'lumot buziladi).
    op.execute(
        "UPDATE payments SET purpose = 'budget' WHERE purpose = 'material'"
    )
