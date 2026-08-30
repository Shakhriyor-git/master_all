"""Bot uchun DB yordamchilari — barcha o'qishda deleted_at IS NULL."""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entry, PriceItem, Project, ProjectPrice
from app.models.enums import ProjectStatus


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
