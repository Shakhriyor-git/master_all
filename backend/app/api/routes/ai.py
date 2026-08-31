"""AI kiritish — erkin matn va chek surati. Natija tasdiqlash formasiga boradi."""

import io
import logging
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import MeasureUnit, PriceItem
from app.schemas.ai import AiDraft, AiParseRequest
from app.services.ai_parse import (
    AiBadResponse,
    AiLimitReached,
    AiRefused,
    AiUnavailable,
    bump_daily_usage,
    build_note_text,
    check_daily_limit,
    parse_receipt_date,
    parse_text,
    scan_receipt,
)

router = APIRouter(prefix="/api", tags=["ai"])
log = logging.getLogger("ai")

_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
_MAX_SIDE = 1400


def _dec(value: object) -> Decimal | None:
    if value in (None, "", "null"):
        return None
    try:
        d = Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return d


def _to_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AiLimitReached):
        return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc))
    if isinstance(exc, AiUnavailable):
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI hozir ishlamayapti. Qo'lda kiritishingiz mumkin.",
        )
    if isinstance(exc, AiBadResponse):
        return HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "AI javobini o'qib bo'lmadi"
        )
    log.exception("AI kutilmagan xatosi")
    return HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Xatolik yuz berdi"
    )


async def _catalog_context(
    db: DbSession, user_id: int
) -> tuple[list[tuple[int, str]], list[str], set[int]]:
    rows = (
        await db.execute(
            select(PriceItem.id, PriceItem.name)
            .where(
                PriceItem.user_id == user_id,
                PriceItem.is_active.is_(True),
            )
            .order_by(PriceItem.name)
        )
    ).all()
    items = [(r.id, r.name) for r in rows]
    owned_ids = {r.id for r in rows}
    units = (
        await db.execute(
            select(MeasureUnit.code).where(
                MeasureUnit.user_id == user_id,
                MeasureUnit.is_active.is_(True),
            )
        )
    ).scalars().all()
    return items, list(units), owned_ids


def _finalize(raw: dict, owned_ids: set[int]) -> AiDraft:
    """Model javobini xavfsiz shaklga keltiradi (4.4-bo'lim)."""
    amount = _dec(raw.get("amount"))
    quantity = _dec(raw.get("quantity"))
    confidence = "high" if raw.get("confidence") == "high" else "low"

    if amount is None or amount <= 0:
        confidence = "low"

    unit_price: Decimal | None = None
    if amount is not None and amount > 0:
        if quantity is not None and quantity > 0:
            unit_price = (amount / quantity).quantize(Decimal("0.01"))
        else:
            quantity = Decimal("1")
            unit_price = amount

    matched = raw.get("matched_price_item_id")
    matched_id = (
        int(matched)
        if isinstance(matched, int | str)
        and str(matched).isdigit()
        and int(matched) in owned_ids
        else None
    )

    kind = raw.get("kind")
    if kind not in ("work", "material", "expense"):
        kind = "material"

    paid_by = raw.get("paid_by")
    if paid_by not in ("master", "client"):
        paid_by = None
    method = raw.get("payment_method")
    if method not in ("cash", "card", "transfer"):
        method = None

    return AiDraft(
        kind=kind,
        name=str(raw.get("name") or "").strip()[:200],
        quantity=quantity,
        unit=(str(raw["unit"]).strip()[:20] if raw.get("unit") else None),
        amount=amount,
        unit_price=unit_price,
        paid_by=paid_by,
        payment_method=method,
        matched_price_item_id=matched_id,
        vendor=(str(raw["vendor"]).strip()[:200] if raw.get("vendor") else None),
        entry_date=parse_receipt_date(raw.get("receipt_date")),
        note=(str(raw["note"]).strip() if raw.get("note") else None),
        confidence=confidence,
    )


@router.post("/projects/{project_id}/ai-parse", response_model=AiDraft)
async def ai_parse(
    project: OwnedProject,
    payload: AiParseRequest,
    user: CurrentUser,
    db: DbSession,
):
    items, units, owned_ids = await _catalog_context(db, user.id)
    try:
        await check_daily_limit(db, user.id)
        raw = await parse_text(payload.text, items, units)
    except AiRefused:
        # model tushunmadi — bo'sh forma, matn "Nomi" ga (4.5-bo'lim)
        await bump_daily_usage(db, user.id)
        return AiDraft(name=payload.text.strip()[:200], confidence="low")
    except Exception as exc:  # noqa: BLE001
        raise _to_error(exc) from exc
    await bump_daily_usage(db, user.id)
    return _finalize(raw, owned_ids)


@router.post("/projects/{project_id}/receipt-scan", response_model=AiDraft)
async def receipt_scan(
    project: OwnedProject,
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
):
    if file.content_type not in _ALLOWED_IMAGE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Faqat jpg, png yoki webp"
        )
    raw_bytes = await file.read()
    if len(raw_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Rasm 8 MB dan katta"
        )

    try:
        await check_daily_limit(db, user.id)
    except AiLimitReached as exc:
        raise _to_error(exc) from exc

    try:
        jpeg = await run_in_threadpool(_recompress, raw_bytes)
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Rasmni o'qib bo'lmadi"
        ) from exc

    try:
        raw = await scan_receipt(jpeg, "image/jpeg")
    except AiRefused as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Chekni o'qib bo'lmadi. Yorug'roq joyda qayta suratga oling.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise _to_error(exc) from exc
    await bump_daily_usage(db, user.id)

    items = raw.get("items") or []
    if not raw.get("note") and items:
        raw["note"] = build_note_text(items)
    if not raw.get("name"):
        raw["name"] = (
            str(items[0].get("name")).strip()
            if len(items) == 1 and items[0].get("name")
            else "Qurilish mollari"
        )
    raw.setdefault("kind", "material")
    _, _, owned_ids = await _catalog_context(db, user.id)
    return _finalize(raw, owned_ids)


def _recompress(data: bytes) -> bytes:
    """Serverda ham siqiladi (himoya): max 1400 px, JPEG 0.85, xotirada."""
    img = Image.open(io.BytesIO(data))
    img.load()
    img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, _MAX_SIDE / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()
