import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    categories,
    entries,
    health,
    me,
    notes,
    payments,
    prices,
    projects,
    units,
)
from app.bot.webhook import (
    attach_bot_webhook,
    start_bot_webhook,
    stop_bot_webhook,
)
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Ishga tushmoqda: env=%s", settings.env)
    Path(settings.avatar_dir).mkdir(parents=True, exist_ok=True)
    if settings.bot_use_webhook:
        await start_bot_webhook()
    yield
    if settings.bot_use_webhook:
        await stop_bot_webhook()
    log.info("To'xtatilmoqda")


app = FastAPI(
    title="Brigada API",
    description="Qurilish brigadalari uchun ish va xarajat hisobi",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.media_root).mkdir(parents=True, exist_ok=True)
app.mount(
    "/media",
    StaticFiles(directory=settings.media_root, check_dir=False),
    name="media",
)

app.include_router(health.router, tags=["health"])
app.include_router(me.router)
app.include_router(projects.router)
app.include_router(categories.router)
app.include_router(units.router)
app.include_router(prices.router)
app.include_router(entries.router)
app.include_router(payments.router)
app.include_router(notes.router)

# BOT_USE_WEBHOOK=true bo'lsa POST /tg/{secret} route'ini qo'shadi
attach_bot_webhook(app)
