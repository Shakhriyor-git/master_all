"""Bot middleware'lari — DB sessiyasi va foydalanuvchi."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.services.user_service import get_or_create_user


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
            data["user"] = await get_or_create_user(
                session,
                telegram_id=tg_user.id,
                full_name=tg_user.full_name or "",
                username=tg_user.username,
                language=tg_user.language_code or "uz",
            )
        return await handler(event, data)


def setup_middlewares(dp: Dispatcher) -> None:
    """DbSession avval, keyin User (User sessiyaga muhtoj)."""
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())
