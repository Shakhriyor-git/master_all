"""Bot middleware'lari — DB sessiyasi va foydalanuvchi."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.models import User


class DbSessionMiddleware(BaseMiddleware):
    """Har bir update uchun bitta DB sessiyasi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with SessionLocal() as session:
            data["session"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    """from_user bo'yicha User topadi yoki yaratadi.

    initData tekshiruvi shart emas — bot API'dan kelgan from_user ishonchli.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        session: AsyncSession | None = data.get("session")
        if tg_user is not None and session is not None and not tg_user.is_bot:
            data["user"] = await _get_or_create_user(session, tg_user)
        return await handler(event, data)


async def _get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    user = (
        await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
    ).scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            full_name=(tg_user.full_name or f"user_{tg_user.id}")[:200],
            username=tg_user.username or None,
            language=(tg_user.language_code or "uz")[:8],
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


def setup_middlewares(dp: Dispatcher) -> None:
    """DbSession avval, keyin User (User sessiyaga muhtoj)."""
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())
