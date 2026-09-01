"""Joriy foydalanuvchi — profil, statistika, avatar."""

import io
import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models import Note, PriceItem, Project, User, UserTrack
from app.models.enums import ProjectStatus
from app.schemas.me import MeRead, MeUpdate
from app.schemas.track import TrackRead, TracksResponse

router = APIRouter(prefix="/api/me", tags=["me"])

_MAX_BYTES = 5 * 1024 * 1024
_ALLOWED = {"image/jpeg", "image/png", "image/webp"}
_SIZE = 512

# Musiqa — foydalanuvchiga jami 15 MB
_MUSIC_LIMIT = 15 * 1024 * 1024
_AUDIO_EXT = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".m4a",
    "audio/ogg": ".ogg",
    "audio/opus": ".ogg",
}


def _mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


def _track_url(user_id: int, filename: str) -> str:
    return f"/media/music/{user_id}/{filename}"


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
        music_enabled=user.music_enabled,
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


# --------------------------------------------------------------------------
# Musiqa treklari — ish paytida chalinadi
# --------------------------------------------------------------------------
async def _user_tracks(db: DbSession, user_id: int) -> list[UserTrack]:
    return list(
        (
            await db.execute(
                select(UserTrack)
                .where(UserTrack.user_id == user_id)
                .order_by(UserTrack.sort_order, UserTrack.id)
            )
        ).scalars()
    )


def _tracks_response(user_id: int, tracks: list[UserTrack]) -> TracksResponse:
    total = sum(t.size_bytes for t in tracks)
    return TracksResponse(
        tracks=[
            TrackRead(
                id=t.id,
                original_name=t.original_name,
                size_bytes=t.size_bytes,
                sort_order=t.sort_order,
                url=_track_url(user_id, t.filename),
            )
            for t in tracks
        ],
        total_bytes=total,
        limit_bytes=_MUSIC_LIMIT,
        remaining_bytes=max(0, _MUSIC_LIMIT - total),
    )


@router.get("/tracks", response_model=TracksResponse)
async def list_tracks(user: CurrentUser, db: DbSession):
    return _tracks_response(user.id, await _user_tracks(db, user.id))


@router.post("/tracks", response_model=TracksResponse)
async def upload_track(file: UploadFile, user: CurrentUser, db: DbSession):
    ext = _AUDIO_EXT.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faqat mp3, m4a yoki ogg",
        )
    raw = await file.read()
    if len(raw) > _MUSIC_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bitta fayl {_mb(_MUSIC_LIMIT)} dan katta",
        )

    tracks = await _user_tracks(db, user.id)
    used = sum(t.size_bytes for t in tracks)
    remaining = _MUSIC_LIMIT - used
    if len(raw) > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Joy yetarli emas. Bo'sh: {_mb(max(0, remaining))}, "
                f"fayl: {_mb(len(raw))}"
            ),
        )

    user_dir = Path(settings.music_dir) / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{secrets.token_hex(8)}{ext}"
    (user_dir / fname).write_bytes(raw)

    original = (file.filename or "Trek").rsplit("/", 1)[-1][:200]
    next_order = (max((t.sort_order for t in tracks), default=-1)) + 1
    db.add(
        UserTrack(
            user_id=user.id,
            filename=fname,
            original_name=original,
            size_bytes=len(raw),
            sort_order=next_order,
        )
    )
    await db.commit()
    return _tracks_response(user.id, await _user_tracks(db, user.id))


@router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track(track_id: int, user: CurrentUser, db: DbSession):
    track = (
        await db.execute(
            select(UserTrack).where(
                UserTrack.id == track_id,
                UserTrack.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trek topilmadi"
        )
    (Path(settings.music_dir) / str(user.id) / track.filename).unlink(
        missing_ok=True
    )
    await db.delete(track)
    await db.commit()
