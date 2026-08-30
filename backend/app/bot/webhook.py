"""Prod uchun bot — webhook rejimi (FastAPI ichida).

Lokalda `BOT_USE_WEBHOOK=false` — bot alohida konteynerda polling qiladi
(app/bot/polling.py). Prodda `BOT_USE_WEBHOOK=true` — bu modul `main.py`
lifespan'idan ulanadi: dispatcher + middleware'lar sozlanadi, `POST /tg/{secret}`
route qo'shiladi, Telegramga webhook o'rnatiladi.
"""

import logging

from aiogram.types import Update
from fastapi import APIRouter, FastAPI, Header, Request, Response, status

from app.bot.handlers import router as handlers_router
from app.bot.loader import bot, dp
from app.bot.middlewares import setup_middlewares
from app.core.config import settings

log = logging.getLogger("bot.webhook")

webhook_router = APIRouter()

_TG_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
_configured = False


def _webhook_path() -> str:
    return f"/tg/{settings.webhook_secret}"


def _configure_dispatcher() -> None:
    global _configured
    if _configured:
        return
    setup_middlewares(dp)
    dp.include_router(handlers_router)
    _configured = True


@webhook_router.post("/tg/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    # Ikki qatlamli himoya: URL'dagi tasodifiy secret + Telegram sarlavhasi
    if not settings.webhook_secret or secret != settings.webhook_secret:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    if x_telegram_bot_api_secret_token != settings.webhook_secret:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=status.HTTP_200_OK)


async def start_bot_webhook() -> None:
    """Lifespan startup: dispatcher'ni sozlaydi va webhook'ni o'rnatadi."""
    if not settings.bot_token:
        log.warning("BOT_USE_WEBHOOK=true, lekin BOT_TOKEN bo'sh — o'tkazib yuborildi")
        return
    _configure_dispatcher()
    url = f"{settings.public_url.rstrip('/')}{_webhook_path()}"
    await bot.set_webhook(
        url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    log.info("Webhook o'rnatildi: %s", url)


async def stop_bot_webhook() -> None:
    """Lifespan shutdown: webhook'ni olib tashlaydi."""
    if not settings.bot_token:
        return
    try:
        await bot.delete_webhook()
    finally:
        await bot.session.close()
    log.info("Webhook o'chirildi")


def attach_bot_webhook(app: FastAPI) -> None:
    """main.py: BOT_USE_WEBHOOK=true bo'lsa route'ni ulaydi."""
    if settings.bot_use_webhook:
        app.include_router(webhook_router)
