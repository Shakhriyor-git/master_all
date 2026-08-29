from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Konteyner tirikligini tekshirish (bazaga tegmaydi)."""
    return {"status": "ok", "env": settings.env, "version": "0.1.0"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    """Baza ulanishini tekshirish."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
