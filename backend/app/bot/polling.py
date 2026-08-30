"""Lokal ishga tushirish nuqtasi — polling. `python -m app.bot.polling`."""

import asyncio
import logging
import sys

from aiogram.types import ErrorEvent

from app.bot import texts
from app.bot.handlers import router
from app.bot.loader import bot, dp
from app.bot.middlewares import setup_middlewares
from app.core.config import settings

log = logging.getLogger("bot")


@dp.error()
async def on_error(event: ErrorEvent) -> bool:
    """Kutilmagan xato — foydalanuvchiga umumiy xabar, log'ga to'liq traceback."""
    log.exception("Bot handler xatosi", exc_info=event.exception)

    update = event.update
    target = update.message
    if target is None and update.callback_query is not None:
        target = update.callback_query.message
    if target is not None:
        try:
            await target.answer(texts.ERROR)
        except Exception:  # noqa: BLE001
            log.exception("Xato xabarini yuborib bo'lmadi")
    return True


async def main() -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN sozlanmagan. .env faylga haqiqiy token qo'shing.")
        sys.exit(1)

    setup_middlewares(dp)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    log.info("Start polling — @%s", me.username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    asyncio.run(main())
