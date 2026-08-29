"""Narx endpointlari — ustaning katalogi va loyiha narxlari."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import PriceItem, ProjectPrice, User
from app.models.enums import EntryKind
from app.schemas.price import (
    PriceItemCreate,
    PriceItemRead,
    PriceItemUpdate,
    ProjectPriceCreate,
    ProjectPriceImport,
    ProjectPriceRead,
    ProjectPriceUpdate,
)

router = APIRouter(prefix="/api", tags=["prices"])


# --------------------------------------------------------------------------
# Katalog — price_items
# --------------------------------------------------------------------------


async def _owned_price_item(
    item_id: int, user: User, db: DbSession
) -> PriceItem:
    item = (
        await db.execute(
            select(PriceItem).where(
                PriceItem.id == item_id, PriceItem.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Katalog pozitsiyasi topilmadi",
        )
    return item


@router.get("/price-items", response_model=list[PriceItemRead])
async def list_price_items(
    user: CurrentUser, db: DbSession, only_active: bool = True
):
    stmt = select(PriceItem).where(PriceItem.user_id == user.id)
    if only_active:
        stmt = stmt.where(PriceItem.is_active.is_(True))
    stmt = stmt.order_by(PriceItem.name)
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/price-items",
    response_model=PriceItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_price_item(
    payload: PriceItemCreate, user: CurrentUser, db: DbSession
):
    item = PriceItem(user_id=user.id, **payload.model_dump())
    db.add(item)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu nom va tur bo'yicha pozitsiya allaqachon bor",
        ) from exc
    await db.refresh(item)
    return item


@router.patch("/price-items/{item_id}", response_model=PriceItemRead)
async def update_price_item(
    item_id: int, payload: PriceItemUpdate, user: CurrentUser, db: DbSession
):
    item = await _owned_price_item(item_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete(
    "/price-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_price_item(item_id: int, user: CurrentUser, db: DbSession):
    item = await _owned_price_item(item_id, user, db)
    item.is_active = False
    await db.commit()


# --------------------------------------------------------------------------
# Loyiha narxlari — project_prices
# --------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/prices", response_model=list[ProjectPriceRead]
)
async def list_project_prices(
    project: OwnedProject, db: DbSession, kind: EntryKind | None = None
):
    stmt = select(ProjectPrice).where(ProjectPrice.project_id == project.id)
    if kind is not None:
        stmt = stmt.where(ProjectPrice.kind == kind)
    stmt = stmt.order_by(ProjectPrice.name)
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/projects/{project_id}/prices",
    response_model=ProjectPriceRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_price(
    project: OwnedProject,
    payload: ProjectPriceCreate,
    user: CurrentUser,
    db: DbSession,
):
    if payload.price_item_id is not None:
        item = await _owned_price_item(payload.price_item_id, user, db)
        price = payload.price if payload.price is not None else item.default_price
        pp = ProjectPrice(
            project_id=project.id,
            price_item_id=item.id,
            name=item.name,
            kind=item.kind,
            unit=item.unit,
            price=price,
        )
    else:
        missing = [
            name
            for name in ("name", "kind", "unit", "price")
            if getattr(payload, name) is None
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Qo'lda narx uchun majburiy maydonlar: {', '.join(missing)}",
            )
        pp = ProjectPrice(
            project_id=project.id,
            price_item_id=None,
            name=payload.name,
            kind=payload.kind,
            unit=payload.unit,
            price=payload.price,
        )
    db.add(pp)
    await db.commit()
    await db.refresh(pp)
    return pp


@router.post(
    "/projects/{project_id}/prices/import",
    response_model=list[ProjectPriceRead],
    status_code=status.HTTP_201_CREATED,
)
async def import_project_prices(
    project: OwnedProject,
    payload: ProjectPriceImport,
    user: CurrentUser,
    db: DbSession,
):
    items = (
        await db.execute(
            select(PriceItem).where(
                PriceItem.id.in_(payload.price_item_ids),
                PriceItem.user_id == user.id,
            )
        )
    ).scalars().all()

    already = set(
        (
            await db.execute(
                select(ProjectPrice.price_item_id).where(
                    ProjectPrice.project_id == project.id,
                    ProjectPrice.price_item_id.is_not(None),
                )
            )
        ).scalars().all()
    )

    created: list[ProjectPrice] = []
    for item in items:
        if item.id in already:
            continue
        pp = ProjectPrice(
            project_id=project.id,
            price_item_id=item.id,
            name=item.name,
            kind=item.kind,
            unit=item.unit,
            price=item.default_price,
        )
        db.add(pp)
        created.append(pp)

    await db.commit()
    for pp in created:
        await db.refresh(pp)
    return created


@router.patch(
    "/projects/{project_id}/prices/{price_id}",
    response_model=ProjectPriceRead,
)
async def update_project_price(
    project: OwnedProject,
    price_id: int,
    payload: ProjectPriceUpdate,
    db: DbSession,
):
    pp = (
        await db.execute(
            select(ProjectPrice).where(
                ProjectPrice.id == price_id,
                ProjectPrice.project_id == project.id,
            )
        )
    ).scalar_one_or_none()
    if pp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyiha narxi topilmadi",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pp, field, value)
    await db.commit()
    await db.refresh(pp)
    return pp
