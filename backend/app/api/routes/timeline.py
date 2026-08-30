"""Tarix lentasi — entries + payments, bitta UNION ALL so'rovda."""

from datetime import date

from fastapi import APIRouter, Query
from sqlalchemy import (
    Boolean,
    Numeric,
    String,
    and_,
    cast,
    func,
    literal,
    null,
    select,
    union_all,
)

from app.api.deps import DbSession, OwnedProject
from app.models import Entry, MeasureUnit, Payment
from app.schemas.timeline import TimelineEntry, TimelinePage, TimelinePayment

router = APIRouter(prefix="/api", tags=["timeline"])

_PAGE_SIZE = 20
_ENTRY_KINDS = {"work", "material", "expense"}


@router.get(
    "/projects/{project_id}/timeline", response_model=TimelinePage
)
async def project_timeline(
    project: OwnedProject,
    db: DbSession,
    kind: str | None = Query(default=None),  # work|material|expense|payment
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
):
    want_entries = kind is None or kind in _ENTRY_KINDS
    want_payments = kind is None or kind == "payment"

    parts = []

    if want_entries:
        e = (
            select(
                literal("entry").label("row_type"),
                Entry.id.label("id"),
                Entry.kind.label("kind"),
                Entry.name.label("name"),
                Entry.quantity.label("quantity"),
                Entry.unit.label("unit"),
                MeasureUnit.label.label("unit_label"),
                Entry.unit_price.label("unit_price"),
                Entry.amount.label("amount"),
                Entry.paid_by.label("paid_by"),
                Entry.payment_method.label("payment_method"),
                Entry.is_rework.label("is_rework"),
                Entry.receipt_file_id.label("receipt_file_id"),
                Entry.note.label("note"),
                cast(null(), String).label("purpose"),
                cast(null(), String).label("method"),
                Entry.entry_date.label("event_date"),
                Entry.created_at.label("created_at"),
            )
            .outerjoin(
                MeasureUnit,
                and_(
                    MeasureUnit.user_id == project.user_id,
                    MeasureUnit.code == Entry.unit,
                ),
            )
            .where(
                Entry.project_id == project.id,
                Entry.deleted_at.is_(None),
            )
        )
        if kind in _ENTRY_KINDS:
            e = e.where(Entry.kind == kind)
        if date_from is not None:
            e = e.where(Entry.entry_date >= date_from)
        if date_to is not None:
            e = e.where(Entry.entry_date <= date_to)
        parts.append(e)

    if want_payments:
        p = select(
            literal("payment").label("row_type"),
            Payment.id.label("id"),
            literal("payment").label("kind"),
            cast(null(), String).label("name"),
            cast(null(), Numeric(12, 3)).label("quantity"),
            cast(null(), String).label("unit"),
            cast(null(), String).label("unit_label"),
            cast(null(), Numeric(14, 2)).label("unit_price"),
            Payment.amount.label("amount"),
            cast(null(), String).label("paid_by"),
            cast(null(), String).label("payment_method"),
            cast(null(), Boolean).label("is_rework"),
            cast(null(), String).label("receipt_file_id"),
            Payment.note.label("note"),
            Payment.purpose.label("purpose"),
            Payment.method.label("method"),
            Payment.paid_at.label("event_date"),
            Payment.created_at.label("created_at"),
        ).where(
            Payment.project_id == project.id,
            Payment.deleted_at.is_(None),
        )
        if date_from is not None:
            p = p.where(Payment.paid_at >= date_from)
        if date_to is not None:
            p = p.where(Payment.paid_at <= date_to)
        parts.append(p)

    if not parts:
        return TimelinePage(items=[], page=1, pages=1, total=0)

    combined = parts[0] if len(parts) == 1 else union_all(*parts)
    subq = combined.subquery()

    total = (
        await db.execute(select(func.count()).select_from(subq))
    ).scalar_one()
    pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = min(page, pages)

    rows = (
        await db.execute(
            select(subq)
            .order_by(subq.c.created_at.desc(), subq.c.id.desc())
            .offset((page - 1) * _PAGE_SIZE)
            .limit(_PAGE_SIZE)
        )
    ).all()

    items: list[TimelineEntry | TimelinePayment] = []
    for r in rows:
        if r.row_type == "entry":
            items.append(
                TimelineEntry(
                    id=r.id,
                    kind=r.kind,
                    name=r.name,
                    quantity=r.quantity,
                    unit=r.unit,
                    unit_label=r.unit_label,
                    unit_price=r.unit_price,
                    amount=r.amount,
                    paid_by=r.paid_by,
                    payment_method=r.payment_method,
                    is_rework=r.is_rework,
                    has_receipt=r.receipt_file_id is not None,
                    note=r.note,
                    entry_date=r.event_date,
                    created_at=r.created_at,
                )
            )
        else:
            items.append(
                TimelinePayment(
                    id=r.id,
                    purpose=r.purpose,
                    amount=r.amount,
                    method=r.method,
                    note=r.note,
                    paid_at=r.event_date,
                    created_at=r.created_at,
                )
            )

    return TimelinePage(items=items, page=page, pages=pages, total=total)
