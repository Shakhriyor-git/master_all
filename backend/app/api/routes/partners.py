"""Brigada endpointlari — sheriklar va ularga berilgan pullar.

Ustaning shaxsiy daftari. Obyekt, summary, timeline, PDF — hech biriga
bog'lanmaydi. Har bir so'rov `user_id` bilan filtrlanadi.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession
from app.models import Partner, PartnerPayment, User
from app.schemas.partner import (
    PartnerCreate,
    PartnerListItem,
    PartnerListRead,
    PartnerPaymentCreate,
    PartnerPaymentRead,
    PartnerPaymentUpdate,
    PartnerRead,
    PartnerUpdate,
)

router = APIRouter(prefix="/api", tags=["partners"])


async def _owned_partner(
    partner_id: int, user: User, db: AsyncSession
) -> Partner:
    """Begona yoki o'chirilgan sherik uchun 404."""
    partner = (
        await db.execute(
            select(Partner).where(
                Partner.id == partner_id,
                Partner.user_id == user.id,
                Partner.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sherik topilmadi"
        )
    return partner


async def _owned_partner_payment(
    payment_id: int, user: User, db: AsyncSession
) -> PartnerPayment:
    payment = (
        await db.execute(
            select(PartnerPayment)
            .join(Partner, Partner.id == PartnerPayment.partner_id)
            .where(
                PartnerPayment.id == payment_id,
                PartnerPayment.user_id == user.id,
                PartnerPayment.deleted_at.is_(None),
                Partner.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="To'lov topilmadi"
        )
    return payment


# ---------------------------------------------------------------------------
# Sheriklar
# ---------------------------------------------------------------------------


@router.get("/partners", response_model=PartnerListRead)
async def list_partners(user: CurrentUser, db: DbSession):
    """Bitta agregat so'rov: LEFT JOIN + GROUP BY — N+1 yo'q."""
    active_payment = PartnerPayment.deleted_at.is_(None)
    total_paid = func.coalesce(
        func.sum(PartnerPayment.amount).filter(active_payment), 0
    )
    payments_count = func.count(PartnerPayment.id).filter(active_payment)
    last_payment_at = func.max(PartnerPayment.paid_at).filter(active_payment)

    stmt = (
        select(
            Partner,
            total_paid.label("total_paid"),
            payments_count.label("payments_count"),
            last_payment_at.label("last_payment_at"),
        )
        .outerjoin(PartnerPayment, PartnerPayment.partner_id == Partner.id)
        .where(Partner.user_id == user.id, Partner.deleted_at.is_(None))
        .group_by(Partner.id)
        .order_by(Partner.name.asc(), Partner.id.asc())
    )

    partners: list[PartnerListItem] = []
    grand_total = Decimal(0)
    for partner, total, count, last_at in (await db.execute(stmt)).all():
        row = PartnerListItem(
            **PartnerRead.model_validate(partner).model_dump(),
            total_paid=total,
            payments_count=count,
            last_payment_at=last_at,
        )
        grand_total += row.total_paid
        partners.append(row)
    return PartnerListRead(partners=partners, grand_total=grand_total)


@router.post(
    "/partners",
    response_model=PartnerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_partner(
    payload: PartnerCreate, user: CurrentUser, db: DbSession
):
    partner = Partner(
        user_id=user.id,
        name=payload.name.strip(),
        phone=payload.phone,
        note=payload.note,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.patch("/partners/{partner_id}", response_model=PartnerRead)
async def update_partner(
    partner_id: int, payload: PartnerUpdate, user: CurrentUser, db: DbSession
):
    partner = await _owned_partner(partner_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(partner, field, value.strip() if field == "name" else value)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.delete(
    "/partners/{partner_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_partner(partner_id: int, user: CurrentUser, db: DbSession):
    """Soft delete. To'lovlari ham bir vaqtda o'chiriladi."""
    partner = await _owned_partner(partner_id, user, db)
    now = datetime.now(UTC)
    partner.deleted_at = now
    for payment in (
        await db.execute(
            select(PartnerPayment).where(
                PartnerPayment.partner_id == partner.id,
                PartnerPayment.deleted_at.is_(None),
            )
        )
    ).scalars():
        payment.deleted_at = now
    await db.commit()


# ---------------------------------------------------------------------------
# To'lovlar
# ---------------------------------------------------------------------------


@router.get(
    "/partners/{partner_id}/payments",
    response_model=list[PartnerPaymentRead],
)
async def list_partner_payments(
    partner_id: int, user: CurrentUser, db: DbSession
):
    partner = await _owned_partner(partner_id, user, db)
    stmt = (
        select(PartnerPayment)
        .where(
            PartnerPayment.user_id == user.id,
            PartnerPayment.partner_id == partner.id,
            PartnerPayment.deleted_at.is_(None),
        )
        .order_by(PartnerPayment.paid_at.desc(), PartnerPayment.id.desc())
    )
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/partners/{partner_id}/payments",
    response_model=PartnerPaymentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_partner_payment(
    partner_id: int,
    payload: PartnerPaymentCreate,
    user: CurrentUser,
    db: DbSession,
):
    partner = await _owned_partner(partner_id, user, db)
    payment = PartnerPayment(
        user_id=user.id,
        partner_id=partner.id,
        amount=payload.amount,
        method=payload.method,
        note=payload.note,
    )
    if payload.paid_at is not None:
        payment.paid_at = payload.paid_at
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.patch(
    "/partner-payments/{payment_id}", response_model=PartnerPaymentRead
)
async def update_partner_payment(
    payment_id: int,
    payload: PartnerPaymentUpdate,
    user: CurrentUser,
    db: DbSession,
):
    payment = await _owned_partner_payment(payment_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete(
    "/partner-payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_partner_payment(
    payment_id: int, user: CurrentUser, db: DbSession
):
    payment = await _owned_partner_payment(payment_id, user, db)
    payment.deleted_at = datetime.now(UTC)
    await db.commit()
