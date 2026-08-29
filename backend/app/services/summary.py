"""Loyiha balansini hisoblash — bitta agregat SQL so'rovda."""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entry, Payment
from app.models.enums import EntryKind, PaidBy
from app.schemas.common import ProjectSummary

_CENTS = Decimal("0.01")


def _money(value: object) -> Decimal:
    """Har qanday son(yoki None) ni 2 xonali Decimal ga keltiradi."""
    return (Decimal(value) if value is not None else Decimal(0)).quantize(_CENTS)


async def build_project_summary(
    db: AsyncSession, project_id: int
) -> ProjectSummary:
    is_work = Entry.kind == EntryKind.WORK
    is_material = Entry.kind == EntryKind.MATERIAL

    works_total = func.coalesce(
        func.sum(case((is_work, Entry.amount), else_=0)), 0
    )
    materials_by_master = func.coalesce(
        func.sum(
            case(
                (is_material & (Entry.paid_by == PaidBy.MASTER), Entry.amount),
                else_=0,
            )
        ),
        0,
    )
    materials_by_client = func.coalesce(
        func.sum(
            case(
                (is_material & (Entry.paid_by == PaidBy.CLIENT), Entry.amount),
                else_=0,
            )
        ),
        0,
    )

    # To'lovlar boshqa jadvalda — skalyar kichik so'rov sifatida qo'shamiz,
    # shunda hammasi bitta so'rovda hisoblanadi.
    paid_total_sq = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.project_id == project_id,
            Payment.deleted_at.is_(None),
        )
        .scalar_subquery()
    )

    stmt = select(
        works_total.label("works_total"),
        materials_by_master.label("materials_by_master"),
        materials_by_client.label("materials_by_client"),
        paid_total_sq.label("paid_total"),
        func.count(Entry.id).label("entries_count"),
        func.max(Entry.entry_date).label("last_entry_date"),
    ).where(
        Entry.project_id == project_id,
        Entry.deleted_at.is_(None),
    )

    row = (await db.execute(stmt)).one()

    works = _money(row.works_total)
    mat_master = _money(row.materials_by_master)
    paid = _money(row.paid_total)

    return ProjectSummary(
        works_total=works,
        materials_by_master=mat_master,
        materials_by_client=_money(row.materials_by_client),
        paid_total=paid,
        # materials_by_client balansga kirmaydi — mijoz o'zi to'lagan
        client_owes=(works + mat_master - paid).quantize(_CENTS),
        entries_count=row.entries_count or 0,
        last_entry_date=row.last_entry_date,
    )
