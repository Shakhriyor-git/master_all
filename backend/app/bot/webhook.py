"""Prod uchun webhook — HOZIR YOQILMAGAN, main.py ga ulanmagan.

Lokalda polling ishlaydi (app/bot/polling.py). Webhook'ni yoqish uchun
(keyingi bosqichda):

  1. .env:  BOT_USE_WEBHOOK=true  va  WEBHOOK_SECRET=<tasodifiy_satr>
  2. app/main.py lifespan ichida:
        from app.bot.webhook import setup_bot_webhook, shutdown_bot, webhook_router
        # startup:  await setup_bot_webhook()
        # shutdown: await shutdown_bot()
        app.include_router(webhook_router)
  3. `bot` compose servisini o'chiring — polling va webhook bir vaqtda ishlamaydi.
"""

from aiogram.types import Update
from fastapi import APIRouter, Request, Response

from app.bot.handlers import router as handlers_router
from app.bot.loader import bot, dp
from app.bot.middlewares import setup_middlewares
from app.core.config import settings

webhook_router = APIRouter()

_configured = False


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        setup_middlewares(dp)
        dp.include_router(handlers_router)
        _configured = True


async def setup_bot_webhook() -> None:
    _ensure_configured()
    url = (
        f"{settings.public_url.rstrip('/')}"
        f"/bot/webhook/{settings.webhook_secret}"
    )
    await bot.set_webhook(
        url,
        drop_pending_updates=True,
        secret_token=settings.webhook_secret or None,
    )


async def shutdown_bot() -> None:
    await bot.delete_webhook()
    await bot.session.close()


@webhook_router.post("/bot/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> Response:
    if not settings.webhook_secret or secret != settings.webhook_secret:
        return Response(status_code=403)
    _ensure_configured()
    update = Update.model_validate(
        await request.json(), context={"bot": bot}
    )
    await dp.feed_update(bot, update)
    return Response(status_code=200)
