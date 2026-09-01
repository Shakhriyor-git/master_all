"""Material qarzi tushunchasi butunlay olib tashlandi

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-01 14:00:00.000000

Yangi model:
  Ish haqi:  bajarilgan ishlar − mijoz to'lagan = MIJOZ QARZI
  Material:  faqat ro'yxat va jami sarflangan. Qarz yo'q — mijoz to'laydi.

O'zgarishlar:
1. entries: kind IN ('material','expense') bo'lganlarning hammasi
   paid_by = 'client'. Usta faqat yozib boradi.
2. ck_entries_master_expense_not_billable olib tashlandi (ma'nosiz —
   usta xarajati degan tushuncha yo'q).
   O'rniga: material/xarajat doim paid_by='client' bo'lishini majburlash.
3. payments.purpose = 'material' qatorlarga TEGILMAYDI — ular Tarixda
   qoladi, lekin summary.labor.paid ga kirmaydi (purpose='labor' filtri).

Downgrade: paid_by qiymatlari QAYTARILMAYDI (ma'no o'zgargan). Faqat
constraint'lar orqaga qaytariladi.
"""
from collections.abc import Sequence

from alembic import op


# revision identifikatorlari
revision: str = 'd4e5f6a7b8c9'
down_revision: str | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE entries SET paid_by = 'client' "
        "WHERE kind IN ('material', 'expense')"
    )
    op.drop_constraint(
        "ck_entries_master_expense_not_billable", "entries", type_="check"
    )
    op.create_check_constraint(
        "ck_entries_material_expense_client",
        "entries",
        "kind NOT IN ('material', 'expense') OR paid_by = 'client'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_entries_material_expense_client", "entries", type_="check"
    )
    op.create_check_constraint(
        "ck_entries_master_expense_not_billable",
        "entries",
        "NOT (kind = 'expense' AND paid_by = 'master' AND is_billable)",
    )
    # paid_by 'client' -> 'master' QAYTARILMAYDI: yangi modelda material/
    # xarajatni har doim mijoz to'laydi, orqaga qaytarish ma'lumotni buzadi.
