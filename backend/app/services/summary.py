"""Loyiha balansi — ikkita mustaqil hisob (ish haqi / mijoz budjeti).

Ikkalasi hech qachon qo'shilmaydi. Bitta agregat SQL so'rovda hisoblanadi,
hamma joyda `deleted_at IS NULL`.
"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entry, Payment
from app.models.enums import EntryKind, PaidBy, PaymentPurpose
from app.schemas.common import (
    BudgetSummary,
    LaborSummary,
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
        _sum_if(is_work & Entry.is_rework.is_(True)).label("rework_total"),
        _sum_if(is_material & by_master & billable).label(
            "materials_by_master"
        ),
        _sum_if(is_expense & by_master).label("expenses_by_master"),
        _sum_if(is_material & by_client).label("spent_materials"),
        _sum_if(is_expense & by_client).label("spent_expenses"),
        _payments_sum(PaymentPurpose.LABOR).label("paid_labor"),
        _payments_sum(PaymentPurpose.BUDGET).label("given"),
        func.count(Entry.id).label("entries_count"),
        func.max(Entry.entry_date).label("last_entry_date"),
    ).where(
        Entry.project_id == project_id,
        Entry.deleted_at.is_(None),
    )

    row = (await db.execute(stmt)).one()

    works_total = _money(row.works_total)
    materials_by_master = _money(row.materials_by_master)
    paid_labor = _money(row.paid_labor)

    given = _money(row.given)
    spent_materials = _money(row.spent_materials)
    spent_expenses = _money(row.spent_expenses)

    labor = LaborSummary(
        works_total=works_total,
        materials_by_master=materials_by_master,
        paid_labor=paid_labor,
        # manfiy bo'lishi mumkin (avans) — xizmat raqamni o'zgartirmaydi
        client_owes=(works_total + materials_by_master - paid_labor).quantize(
            _CENTS
        ),
        rework_total=_money(row.rework_total),
        expenses_by_master=_money(row.expenses_by_master),
    )
    budget = BudgetSummary(
        given=given,
        spent_materials=spent_materials,
        spent_expenses=spent_expenses,
        spent_total=(spent_materials + spent_expenses).quantize(_CENTS),
        balance=(given - spent_materials - spent_expenses).quantize(_CENTS),
    )
    meta = SummaryMeta(
        entries_count=row.entries_count or 0,
        last_entry_date=row.last_entry_date,
    )
    return ProjectSummary(labor=labor, budget=budget, meta=meta)
