"""O'lchov birligi endpointlari."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models import MeasureUnit
from app.schemas.unit import UnitCreate, UnitRead

router = APIRouter(prefix="/api/units", tags=["units"])


@router.get("", response_model=list[UnitRead])
async def list_units(user: CurrentUser, db: DbSession):
    stmt = (
        select(MeasureUnit)
        .where(
            MeasureUnit.user_id == user.id,
            MeasureUnit.is_active.is_(True),
        )
        .order_by(MeasureUnit.sort_order, MeasureUnit.code)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "", response_model=UnitRead, status_code=status.HTTP_201_CREATED
)
async def create_unit(payload: UnitCreate, user: CurrentUser, db: DbSession):
    unit = MeasureUnit(
        user_id=user.id, code=payload.code, label=payload.label
    )
    db.add(unit)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu kod bo'yicha birlik allaqachon bor",
        ) from exc
    await db.refresh(unit)
    return unit


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(unit_id: int, user: CurrentUser, db: DbSession):
    unit = (
        await db.execute(
            select(MeasureUnit).where(
                MeasureUnit.id == unit_id,
                MeasureUnit.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Birlik topilmadi"
        )
    if unit.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Standart birlikni o'chirib bo'lmaydi",
        )
    unit.is_active = False
    await db.commit()
