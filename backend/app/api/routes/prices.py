"""Narx endpointlari — ustaning katalogi va loyiha narxlari."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import Category, MeasureUnit, PriceItem, ProjectPrice, User
from app.models.enums import EntryKind
from app.schemas.price import (
    PriceItemBulkUpdate,
    PriceItemCreate,
    PriceItemRead,
    PriceItemUpdate,
    PriceSyncResult,
    ProjectPriceCreate,
    ProjectPriceImport,
    ProjectPriceRead,
    ProjectPriceUpdate,
)

router = APIRouter(prefix="/api", tags=["prices"])


def _price_item_read(item: PriceItem, cat_name: str | None, unit_label: str | None) -> PriceItemRead:
    row = PriceItemRead.model_validate(item)
    row.category_name = cat_name
    row.unit_label = unit_label
    return row


async def _check_owned_category(
    category_id: int | None, user: User, db: DbSession
) -> None:
    if category_id is None:
        return
    owned = (
        await db.execute(
            select(Category.id).where(
                Category.id == category_id, Category.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if owned is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoriya topilmadi",
        )


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
    user: CurrentUser,
    db: DbSession,
    only_active: bool = True,
    category_id: int | None = None,
    kind: EntryKind | None = None,
    q: str | None = None,
):
    stmt = (
        select(PriceItem, Category.name, MeasureUnit.label)
        .outerjoin(Category, Category.id == PriceItem.category_id)
        .outerjoin(
            MeasureUnit,
            (MeasureUnit.user_id == user.id)
            & (MeasureUnit.code == PriceItem.unit),
        )
        .where(PriceItem.user_id == user.id)
    )
    if only_active:
        stmt = stmt.where(PriceItem.is_active.is_(True))
    if category_id is not None:
        stmt = stmt.where(PriceItem.category_id == category_id)
    if kind is not None:
        stmt = stmt.where(PriceItem.kind == kind)
    if q:
        stmt = stmt.where(PriceItem.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(PriceItem.name)

    return [
        _price_item_read(item, cat_name, unit_label)
        for item, cat_name, unit_label in (await db.execute(stmt)).all()
    ]


@router.post(
    "/price-items",
    response_model=PriceItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_price_item(
    payload: PriceItemCreate, user: CurrentUser, db: DbSession
):
    await _check_owned_category(payload.category_id, user, db)
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


@router.patch("/price-items/bulk", response_model=list[PriceItemRead])
async def bulk_update_price_items(
    payload: PriceItemBulkUpdate, user: CurrentUser, db: DbSession
):
    """Bir so'rovda 50 tagacha pozitsiya narxini yangilaydi. Egalik tekshiriladi."""
    by_id = {row.id: row.default_price for row in payload.items}
    items = (
        await db.execute(
            select(PriceItem).where(
                PriceItem.id.in_(by_id),
                PriceItem.user_id == user.id,
            )
        )
    ).scalars().all()
    if len(items) != len(by_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ba'zi pozitsiyalar topilmadi yoki sizniki emas",
        )
    for item in items:
        item.default_price = by_id[item.id]
    await db.commit()
    for item in items:
        await db.refresh(item)
    return [PriceItemRead.model_validate(i) for i in items]


@router.patch("/price-items/{item_id}", response_model=PriceItemRead)
async def update_price_item(
    item_id: int, payload: PriceItemUpdate, user: CurrentUser, db: DbSession
):
    item = await _owned_price_item(item_id, user, db)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        await _check_owned_category(data["category_id"], user, db)
    for field, value in data.items():
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


@router.post(
    "/projects/{project_id}/prices/{price_id}/sync",
    response_model=PriceSyncResult,
)
async def sync_project_price(
    project: OwnedProject, price_id: int, db: DbSession
):
    """project_prices.price ni katalogdagi joriy default_price ga tenglashtiradi.

    Mavjud entries o'zgarmaydi — ular yozilgan paytdagi narxni saqlaydi.
    """
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
    if pp.price_item_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu narx katalogga bog'lanmagan (bir martalik pozitsiya)",
        )

    item = (
        await db.execute(
            select(PriceItem).where(PriceItem.id == pp.price_item_id)
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Katalog pozitsiyasi topilmadi",
        )

    old_price = pp.price
    new_price = item.default_price
    changed = old_price != new_price
    if changed:
        pp.price = new_price
        await db.commit()

    return PriceSyncResult(
        price_id=pp.id,
        name=pp.name,
        old_price=old_price,
        new_price=new_price,
        changed=changed,
    )
