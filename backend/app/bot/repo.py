"""Bot uchun DB yordamchilari — barcha o'qishda deleted_at IS NULL.

Mini App bor — bot faqat obyektlarni o'qiydi va yangisini yaratadi.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
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
