"""To'lov endpointlari — mijozdan olingan pullar."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import Payment, Project, User
from app.models.enums import PaymentPurpose
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate

router = APIRouter(prefix="/api", tags=["payments"])


async def _owned_payment(
    payment_id: int, user: User, db: AsyncSession
) -> Payment:
    payment = (
        await db.execute(
            select(Payment)
            .join(Project, Project.id == Payment.project_id)
            .where(
                Payment.id == payment_id,
                Payment.deleted_at.is_(None),
                Project.user_id == user.id,
                Project.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="To'lov topilmadi"
        )
    return payment


@router.get(
    "/projects/{project_id}/payments", response_model=list[PaymentRead]
)
async def list_payments(
    project: OwnedProject,
    db: DbSession,
    purpose: PaymentPurpose | None = None,
):
    stmt = select(Payment).where(
        Payment.project_id == project.id,
        Payment.deleted_at.is_(None),
    )
    if purpose is not None:
        stmt = stmt.where(Payment.purpose == purpose)
    stmt = stmt.order_by(Payment.paid_at.desc(), Payment.id.desc())
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/projects/{project_id}/payments",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    project: OwnedProject,
    payload: PaymentCreate,
    user: CurrentUser,
    db: DbSession,
):
    payment = Payment(
        project_id=project.id,
        created_by_user_id=user.id,
        amount=payload.amount,
        method=payload.method,
        purpose=payload.purpose,
        note=payload.note,
    )
    if payload.paid_at is not None:
        payment.paid_at = payload.paid_at

    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.patch("/payments/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: int, payload: PaymentUpdate, user: CurrentUser, db: DbSession
):
    payment = await _owned_payment(payment_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete(
    "/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_payment(payment_id: int, user: CurrentUser, db: DbSession):
    payment = await _owned_payment(payment_id, user, db)
    payment.deleted_at = datetime.now(UTC)
    await db.commit()
