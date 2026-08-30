"""Foydalanuvchi topish/yaratish — bot va Mini App uchun yagona nuqta.

Yangi foydalanuvchi yaratilganda standart katalog ham to'ldiriladi, aks holda
Web App'dan birinchi kirgan ustada katalog bo'sh qolardi.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.catalog_seed import seed_catalog_for_user


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
    language: str = "uz",
) -> User:
    """telegram_id bo'yicha User qaytaradi; yo'q bo'lsa yaratadi + katalog seed."""
    user = (
        await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
    ).scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        telegram_id=telegram_id,
        full_name=(full_name or f"user_{telegram_id}")[:200],
        username=(username or None),
        language=(language or "uz")[:8],
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await seed_catalog_for_user(session, user.id)
    return user
