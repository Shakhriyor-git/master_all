"""Loyiha balansi — ikkita mustaqil qarz.

  1. Ish haqi qarzi  = bajarilgan ishlar − mijoz ish haqi uchun to'lagani
  2. Material qarzi   = usta olgan material/xarajat − mijoz material uchun to'lagani

Ikkalasi hech qachon qo'shilmaydi. Bitta agregat SQL so'rovda hisoblanadi,
hamma joyda `deleted_at IS NULL`.
"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entry, Payment
from app.models.enums import EntryKind, PaidBy, PaymentPurpose
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
    by_master = Entry.paid_by == PaidBy.MASTER
    by_client = Entry.paid_by == PaidBy.CLIENT
    billable = Entry.is_billable.is_(True)

    def _payments_sum(purpose: str):
        return (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                Payment.project_id == project_id,
                Payment.purpose == purpose,
                Payment.deleted_at.is_(None),
            )
            .scalar_subquery()
        )

    stmt = select(
        _sum_if(is_work & billable).label("works_total"),
        _sum_if(is_material & by_master & billable).label("materials_master"),
        _sum_if(is_expense & by_master).label("expenses_master"),
        _sum_if((is_material | is_expense) & by_client).label("client_bought"),
        _payments_sum(PaymentPurpose.LABOR).label("paid_labor"),
        _payments_sum(PaymentPurpose.MATERIAL).label("paid_material"),
        func.count(Entry.id).label("entries_count"),
        func.max(Entry.entry_date).label("last_entry_date"),
    ).where(
        Entry.project_id == project_id,
        Entry.deleted_at.is_(None),
    )

    row = (await db.execute(stmt)).one()

    works_total = _money(row.works_total)
    paid_labor = _money(row.paid_labor)
    materials_total = _money(row.materials_master)
    expenses_total = _money(row.expenses_master)
    paid_material = _money(row.paid_material)

    labor = LaborSummary(
        works_total=works_total,
        paid=paid_labor,
        # manfiy bo'lishi mumkin (avans) — xizmat raqamni o'zgartirmaydi
        remaining=(works_total - paid_labor).quantize(_CENTS),
    )
    materials = MaterialsSummary(
        materials_total=materials_total,
        expenses_total=expenses_total,
        paid=paid_material,
        remaining=(
            materials_total + expenses_total - paid_material
        ).quantize(_CENTS),
    )
    meta = SummaryMeta(
        entries_count=row.entries_count or 0,
        last_entry_date=row.last_entry_date,
    )
    return ProjectSummary(
        labor=labor,
        materials=materials,
        client_bought=_money(row.client_bought),
        meta=meta,
    )
