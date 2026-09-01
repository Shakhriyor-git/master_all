"""Joriy foydalanuvchi — profil, statistika, avatar."""

import io
import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models import Note, PriceItem, Project, User
from app.models.enums import ProjectStatus
from app.schemas.me import MeRead, MeUpdate

router = APIRouter(prefix="/api/me", tags=["me"])

_MAX_BYTES = 5 * 1024 * 1024
_ALLOWED = {"image/jpeg", "image/png", "image/webp"}
_SIZE = 512


def _avatar_url(user: User) -> str | None:
    return f"/media/avatars/{user.avatar_path}" if user.avatar_path else None


async def _project_counts(db: DbSession, user_id: int) -> tuple[int, int]:
    rows = (
        await db.execute(
            select(Project.status, func.count(Project.id))
            .where(
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
            )
            .group_by(Project.status)
        )
    ).all()
    by_status = dict(rows)
    return (
        by_status.get(ProjectStatus.ACTIVE.value, 0),
        by_status.get(ProjectStatus.COMPLETED.value, 0),
    )


async def _catalog_counts(db: DbSession, user_id: int) -> tuple[int, int]:
    """(jami pozitsiya, narxsiz) — faqat faol katalog."""
    row = (
        await db.execute(
            select(
                func.count(PriceItem.id),
                func.count(PriceItem.id).filter(
                    PriceItem.default_price <= 0
                ),
            ).where(
                PriceItem.user_id == user_id,
                PriceItem.is_active.is_(True),
            )
        )
    ).one()
    return int(row[0] or 0), int(row[1] or 0)


async def _notes_count(db: DbSession, user_id: int) -> int:
    return int(
        (
            await db.execute(
                select(func.count(Note.id)).where(
                    Note.user_id == user_id,
                    Note.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        or 0
    )


async def _me_read(db: DbSession, user: User) -> MeRead:
    active, completed = await _project_counts(db, user.id)
    catalog_items, catalog_unpriced = await _catalog_counts(db, user.id)
    notes_count = await _notes_count(db, user.id)
    return MeRead(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        phone=user.phone,
        language=user.language,
        theme=user.theme,
        onboarded=user.onboarded,
        avatar_url=_avatar_url(user),
        social_links=user.social_links or [],
        active_projects=active,
        completed_projects=completed,
        catalog_items=catalog_items,
        catalog_unpriced=catalog_unpriced,
        notes_count=notes_count,
    )


@router.get("", response_model=MeRead)
async def get_me(user: CurrentUser, db: DbSession):
    return await _me_read(db, user)


@router.patch("", response_model=MeRead)
async def update_me(payload: MeUpdate, user: CurrentUser, db: DbSession):
    data = payload.model_dump(exclude_unset=True)
    if "social_links" in data:
        # JSONB — oddiy dict ro'yxati sifatida saqlanadi
        data["social_links"] = [
            link.model_dump() for link in (payload.social_links or [])
        ]
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return await _me_read(db, user)


def _process_image(raw: bytes) -> bytes:
    """RGB ga o'tkazadi, markazdan 512×512 kesadi, JPEG qaytaradi."""
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rasmni o'qib bo'lmadi",
        ) from exc

    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize(
        (_SIZE, _SIZE), Image.LANCZOS
    )
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


@router.post("/avatar", response_model=MeRead)
async def upload_avatar(file: UploadFile, user: CurrentUser, db: DbSession):
    if file.content_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faqat jpg, png yoki webp",
        )
    raw = await file.read()
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rasm 5 MB dan katta",
        )

    data = _process_image(raw)

    avatar_dir = Path(settings.avatar_dir)
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{secrets.token_hex(4)}.jpg"
    (avatar_dir / filename).write_bytes(data)

    old = user.avatar_path
    user.avatar_path = filename
    await db.commit()
    await db.refresh(user)

    if old and old != filename:
        (avatar_dir / old).unlink(missing_ok=True)

    return await _me_read(db, user)


@router.delete("/avatar", response_model=MeRead)
async def delete_avatar(user: CurrentUser, db: DbSession):
    old = user.avatar_path
    user.avatar_path = None
    await db.commit()
    await db.refresh(user)
    if old:
        (Path(settings.avatar_dir) / old).unlink(missing_ok=True)
    return await _me_read(db, user)
