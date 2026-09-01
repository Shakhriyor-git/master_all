"""Loyiha balansi — yagona qarz (ish haqi) + material ro'yxati.

  Ish haqi qarzi = bajarilgan ishlar − mijoz ish haqi uchun to'lagani
  Material       = faqat jami sarflangan summa (qarz yo'q — mijoz to'laydi)

Bitta agregat SQL so'rovda hisoblanadi, hamma joyda `deleted_at IS NULL`.
"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entry, Payment
from app.models.enums import EntryKind, PaymentPurpose
from app.schemas.common import (
    LaborSummary,
    MaterialsSummary,
    ProjectSummary,
    SummaryMeta,
)

_CENTS = Decimal("0.01")


def _money(value: object) -> Decimal:
    return (Decimal(value) if value is not None else Decimal(0)).quantize(_CENTS)


def _sum_if(condition) -> object:
    return func.coalesce(func.sum(case((condition, Entry.amount), else_=0)), 0)


async def build_project_summary(
    db: AsyncSession, project_id: int
) -> ProjectSummary:
    is_work = Entry.kind == EntryKind.WORK
    is_material = Entry.kind == EntryKind.MATERIAL
    is_expense = Entry.kind == EntryKind.EXPENSE
    billable = Entry.is_billable.is_(True)

    # Faqat ish haqi to'lovlari hisobga kiradi. Eski purpose='material'
    # to'lovlar bazada qoladi, lekin hech qanday hisobga qo'shilmaydi.
    paid_labor_subq = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.project_id == project_id,
            Payment.purpose == PaymentPurpose.LABOR,
            Payment.deleted_at.is_(None),
        )
        .scalar_subquery()
    )

    stmt = select(
        _sum_if(is_work & billable).label("works_total"),
        _sum_if(is_material).label("materials_total"),
        _sum_if(is_expense).label("expenses_total"),
        paid_labor_subq.label("paid_labor"),
        func.count(Entry.id).label("entries_count"),
        func.max(Entry.entry_date).label("last_entry_date"),
    ).where(
        Entry.project_id == project_id,
        Entry.deleted_at.is_(None),
    )

    row = (await db.execute(stmt)).one()
    paid_labor = _money(row.paid_labor)

    works_total = _money(row.works_total)
    materials_total = _money(row.materials_total)
    expenses_total = _money(row.expenses_total)

    labor = LaborSummary(
        works_total=works_total,
        paid=paid_labor,
        # manfiy bo'lishi mumkin (avans) — xizmat raqamni o'zgartirmaydi
        remaining=(works_total - paid_labor).quantize(_CENTS),
    )
    materials = MaterialsSummary(
        materials_total=materials_total,
        expenses_total=expenses_total,
        total_spent=(materials_total + expenses_total).quantize(_CENTS),
    )
    meta = SummaryMeta(
        entries_count=row.entries_count or 0,
        last_entry_date=row.last_entry_date,
    )
    return ProjectSummary(labor=labor, materials=materials, meta=meta)
