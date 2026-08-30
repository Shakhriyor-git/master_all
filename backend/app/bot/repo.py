"""Bot uchun DB yordamchilari — barcha o'qishda deleted_at IS NULL."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Entry, MeasureUnit, PriceItem, Project, ProjectPrice
from app.models.enums import ProjectStatus

UNDO_WINDOW = timedelta(minutes=5)


@dataclass
class CategoryBucket:
    """Loyiha narxlaridagi kategoriya (id=0 => kategoriyasiz)."""

    id: int
    label: str
    count: int


async def get_owned_project(
    session: AsyncSession, user_id: int, project_id: int
) -> Project | None:
    return (
        await session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()


async def list_active_projects(
    session: AsyncSession, user_id: int
) -> Sequence[Project]:
    return (
        await session.execute(
            select(Project)
            .where(
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
                Project.status != ProjectStatus.ARCHIVED,
            )
            .order_by(Project.created_at.desc())
        )
    ).scalars().all()


async def project_prices_by_kind(
    session: AsyncSession, project_id: int, kind: str
) -> Sequence[ProjectPrice]:
    return (
        await session.execute(
            select(ProjectPrice)
            .where(
                ProjectPrice.project_id == project_id,
                ProjectPrice.kind == kind,
                ProjectPrice.is_active.is_(True),
            )
            .order_by(ProjectPrice.name)
        )
    ).scalars().all()


async def project_price_categories(
    session: AsyncSession, project_id: int, kind: str
) -> list[CategoryBucket]:
    """Loyiha narxlarini manba-katalog kategoriyasi bo'yicha guruhlaydi."""
    rows = (
        await session.execute(
            select(
                func.coalesce(Category.id, 0),
                Category.icon,
                Category.name,
                func.count(ProjectPrice.id),
            )
            .select_from(ProjectPrice)
            .outerjoin(PriceItem, PriceItem.id == ProjectPrice.price_item_id)
            .outerjoin(Category, Category.id == PriceItem.category_id)
            .where(
                ProjectPrice.project_id == project_id,
                ProjectPrice.kind == kind,
                ProjectPrice.is_active.is_(True),
            )
            .group_by(Category.id, Category.icon, Category.name)
            .order_by(func.count(ProjectPrice.id).desc())
        )
    ).all()
    buckets: list[CategoryBucket] = []
    for cat_id, icon, name, count in rows:
        if cat_id:
            label = f"{icon or ''} {name}".strip()
        else:
            label = "Kategoriyasiz"
        buckets.append(CategoryBucket(id=cat_id, label=label, count=count))
    return buckets


async def project_prices_in_category(
    session: AsyncSession, project_id: int, kind: str, category_id: int
) -> Sequence[ProjectPrice]:
    stmt = (
        select(ProjectPrice)
        .outerjoin(PriceItem, PriceItem.id == ProjectPrice.price_item_id)
        .where(
            ProjectPrice.project_id == project_id,
            ProjectPrice.kind == kind,
            ProjectPrice.is_active.is_(True),
        )
        .order_by(ProjectPrice.name)
    )
    if category_id:
        stmt = stmt.where(PriceItem.category_id == category_id)
    else:
        stmt = stmt.where(PriceItem.category_id.is_(None))
    return (await session.execute(stmt)).scalars().all()


async def unit_label(session: AsyncSession, user_id: int, code: str) -> str:
    label = (
        await session.execute(
            select(MeasureUnit.label).where(
                MeasureUnit.user_id == user_id, MeasureUnit.code == code
            )
        )
    ).scalar_one_or_none()
    return label or code


async def last_entry(session: AsyncSession, project_id: int) -> Entry | None:
    return (
        await session.execute(
            select(Entry)
            .where(
                Entry.project_id == project_id, Entry.deleted_at.is_(None)
            )
            .order_by(Entry.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def undo_last_entry(
    session: AsyncSession, project_id: int
) -> tuple[str, Entry | None]:
    """('none'|'old'|'ok', entry). 'ok' bo'lsa entry soft-delete qilingan."""
    entry = await last_entry(session, project_id)
    if entry is None:
        return "none", None
    if datetime.now(UTC) - entry.created_at > UNDO_WINDOW:
        return "old", entry
    entry.deleted_at = datetime.now(UTC)
    await session.commit()
    return "ok", entry


async def recent_entries(
    session: AsyncSession, project_id: int, limit: int = 10
) -> Sequence[Entry]:
    return (
        await session.execute(
            select(Entry)
            .where(
                Entry.project_id == project_id,
                Entry.deleted_at.is_(None),
            )
            .order_by(Entry.entry_date.desc(), Entry.id.desc())
            .limit(limit)
        )
    ).scalars().all()


async def catalog_items(
    session: AsyncSession, user_id: int
) -> Sequence[PriceItem]:
    return (
        await session.execute(
            select(PriceItem)
            .where(
                PriceItem.user_id == user_id,
                PriceItem.is_active.is_(True),
            )
            .order_by(PriceItem.name)
        )
    ).scalars().all()


async def copy_catalog_to_project(
    session: AsyncSession, user_id: int, project_id: int
) -> int:
    """Faol katalog pozitsiyalarini obyektga nusxalaydi. Nusxalar sonini qaytaradi."""
    items = await catalog_items(session, user_id)
    existing = set(
        (
            await session.execute(
                select(ProjectPrice.price_item_id).where(
                    ProjectPrice.project_id == project_id,
                    ProjectPrice.price_item_id.is_not(None),
                )
            )
        ).scalars().all()
    )
    count = 0
    for it in items:
        if it.id in existing:
            continue
        session.add(
            ProjectPrice(
                project_id=project_id,
                price_item_id=it.id,
                name=it.name,
                kind=it.kind,
                unit=it.unit,
                price=it.default_price,
            )
        )
        count += 1
    await session.commit()
    return count


def line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return (Decimal(quantity) * Decimal(unit_price)).quantize(Decimal("0.01"))
