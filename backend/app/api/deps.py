"""FastAPI dependency'lari — autentifikatsiya va egalik tekshiruvi."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import InvalidInitDataError, validate_init_data
from app.models import Project, User
from app.services.user_service import get_or_create_user

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _full_name(tg_user: dict) -> str:
    """Telegram user maydonidan to'liq ism yig'adi."""
    parts = [tg_user.get("first_name"), tg_user.get("last_name")]
    name = " ".join(p for p in parts if p)
    return name or tg_user.get("username") or f"user_{tg_user.get('id')}"


async def _user_from_init_data(init_data: str, db: AsyncSession) -> User:
    try:
        parsed = validate_init_data(init_data, settings.bot_token)
    except InvalidInitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"initData yaroqsiz: {exc}",
        ) from exc

    tg_user = parsed.get("user") or {}
    telegram_id = tg_user.get("id")
    if not isinstance(telegram_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData ichida foydalanuvchi ID topilmadi",
        )

    return await get_or_create_user(
        db,
        telegram_id=telegram_id,
        full_name=_full_name(tg_user),
        username=tg_user.get("username"),
        language=tg_user.get("language_code") or "uz",
    )


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """`Authorization: tma <initData>` sarlavhasini tekshiradi.

    Imzo to'g'ri bo'lsa telegram_id bo'yicha User topadi yoki yaratadi
    (birinchi kirishda avtomatik ro'yxatdan o'tish). Yaroqsiz bo'lsa 401.
    """
    if not authorization or not authorization.lower().startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization sarlavhasi 'tma <initData>' ko'rinishida bo'lsin",
        )
    return await _user_from_init_data(authorization[4:].strip(), db)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_download_user(
    tma: Annotated[str | None, Query()] = None,
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fayl yuklab olish uchun: sarlavha YOKI `?tma=<initData>` so'rov parametri.

    Brauzer `Telegram.WebApp.openLink` orqali ochilganda sarlavha yubora
    olmaydi — shuning uchun initData URL'da uzatiladi.
    """
    if authorization and authorization.lower().startswith("tma "):
        return await _user_from_init_data(authorization[4:].strip(), db)
    if tma:
        return await _user_from_init_data(tma.strip(), db)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="initData kerak (Authorization sarlavhasi yoki ?tma=)",
    )


DownloadUser = Annotated[User, Depends(get_download_user)]


async def get_owned_project(
    project_id: int,
    user: CurrentUser,
    db: DbSession,
) -> Project:
    """Loyiha shu foydalanuvchiniki ekanini tekshiradi.

    Begona yoki o'chirilgan loyiha uchun 404 (403 emas — mavjudligini
    ham oshkor qilmaymiz).
    """
    project = (
        await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user.id,
                Project.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loyiha topilmadi"
        )
    return project


OwnedProject = Annotated[Project, Depends(get_owned_project)]
