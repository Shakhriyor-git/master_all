"""Kategoriya endpointlari."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models import Category, PriceItem, User
from app.models.enums import EntryKind
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


async def _owned_category(cat_id: int, user: User, db: DbSession) -> Category:
    cat = (
        await db.execute(
            select(Category).where(
                Category.id == cat_id, Category.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoriya topilmadi",
        )
    return cat


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    user: CurrentUser, db: DbSession, kind: EntryKind | None = None
):
    items_count = (
        select(func.count(PriceItem.id))
        .where(
            PriceItem.category_id == Category.id,
            PriceItem.is_active.is_(True),
        )
        .correlate(Category)
        .scalar_subquery()
    )
    stmt = (
        select(Category, items_count.label("items_count"))
        .where(Category.user_id == user.id, Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.name)
    )
    if kind is not None:
        stmt = stmt.where(Category.kind == kind)

    result = []
    for cat, count in (await db.execute(stmt)).all():
        row = CategoryRead.model_validate(cat)
        row.items_count = count
        result.append(row)
    return result


@router.post(
    "", response_model=CategoryRead, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CategoryCreate, user: CurrentUser, db: DbSession
):
    cat = Category(user_id=user.id, **payload.model_dump())
    db.add(cat)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu nom va tur bo'yicha kategoriya allaqachon bor",
        ) from exc
    await db.refresh(cat)
    return cat


@router.patch("/{cat_id}", response_model=CategoryRead)
async def update_category(
    cat_id: int, payload: CategoryUpdate, user: CurrentUser, db: DbSession
):
    cat = await _owned_category(cat_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(cat_id: int, user: CurrentUser, db: DbSession):
    cat = await _owned_category(cat_id, user, db)
    cat.is_active = False
    # Ichidagi pozitsiyalar o'chmaydi — "Kategoriyasiz" ga tushadi
    await db.execute(
        update(PriceItem)
        .where(PriceItem.category_id == cat.id)
        .values(category_id=None)
    )
    await db.commit()
