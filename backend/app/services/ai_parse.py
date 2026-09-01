"""AI yordamida matn va chekdan yozuv qurish — Gemini.

Chaqiruv faqat backendda. API kalit frontendga hech qachon tushmaydi.
`run_in_threadpool`, 25 soniya timeout. Javob JSON bo'lmasa xato ko'tariladi.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Sequence
from datetime import UTC, date, datetime

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.models import AiUsage

log = logging.getLogger("ai")

_TIMEOUT_S = 25
_UNIT_HINT = (
    "m2, m3, dona, qop, metr, kg, litr, soat, kunlik, tochka, komplekt, "
    "rulon, summa"
)

_TEXT_PROMPT = """Sen qurilish ustasining yordamchisisan. Usta o'zbek tilida
(rus so'zlari aralash bo'lishi mumkin) nima qilgani yoki nima olganini yozadi.
Uni tuzilgan yozuvga aylantir.

Faqat JSON qaytar, markdown va izohsiz:

{{
  "kind": "work | material | expense",
  "name": "...",
  "quantity": "raqam yoki null",
  "unit": "birlik kodi yoki null",
  "amount": "JAMI summa, faqat raqam",
  "paid_by": "master | client | null",
  "payment_method": "cash | card | transfer | null",
  "matched_price_item_id": null,
  "confidence": "high | low"
}}

Qoidalar:
- amount har doim JAMI summa. Usta bir birlik narxini aytsa, miqdorga ko'paytir.
- kind: bajarilgan ish bo'lsa "work", sotib olingan mol bo'lsa "material",
  ovqat/transport/ijara bo'lsa "expense".
- unit: quyidagi kodlardan birini tanla. Mos kelmasa aytilgan so'zni o'zini yoz.
- Katalogda mos pozitsiya bo'lsa matched_price_item_id ga uning id sini yoz,
  bo'lmasa null.
- "mijoz" / "mijoz to'ladi" -> paid_by "client". "o'zim" / "men" -> "master".
- "naqd" -> cash, "karta" / "kartadan" -> card, "o'tkazma" / "perevod" -> transfer.
- Aytilmagan narsani o'ylab topma — null qoldir.
- Tushunmasang: {{"error": "sabab"}}

BIRLIKLAR: {units}
KATALOG:
{catalog}

MATN: {text}
"""

_RECEIPT_PROMPT = """Rasmda O'zbekistondagi qurilish do'koni cheki bor. Matn
o'zbek, rus yoki aralash.

Faqat JSON qaytar:
{
  "vendor": "do'kon nomi yoki null",
  "receipt_date": "YYYY-MM-DD yoki null",
  "amount": "JAMI summa, faqat raqam",
  "confidence": "high | low",
  "items": [{"name": "...", "quantity": "...", "unit": "...",
             "unit_price": "...", "amount": "..."}]
}

- Chekda jami summa yozilgan bo'lsa o'shani ol. Yo'q bo'lsa mollarni qo'sh.
- Rasm chek emas yoki o'qib bo'lmasa: {"error": "sabab"}
- Taxmin qilma, ishonching past bo'lsa confidence: "low"
"""


class AiError(Exception):
    """AI umumiy xatosi."""


class AiUnavailable(AiError):
    """Kalit yo'q yoki xizmat javob bermadi — 503."""


class AiLimitReached(AiError):
    """Kunlik limit tugadi — 429."""


class AiRefused(AiError):
    """Model {"error": ...} qaytardi — bo'sh forma ochiladi."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AiBadResponse(AiError):
    """Javob JSON emas yoki parse bo'lmadi — 422."""


# --------------------------------------------------------------------------
# Kunlik limit
# --------------------------------------------------------------------------
async def check_daily_limit(db: AsyncSession, user_id: int) -> None:
    """Limitga yetgan bo'lsa AiLimitReached ko'taradi. Bump alohida — muvaffaqiyatda."""
    today = datetime.now(UTC).date()
    used = (
        await db.execute(
            select(AiUsage.count).where(
                AiUsage.user_id == user_id, AiUsage.day == today
            )
        )
    ).scalar_one_or_none()
    if used is not None and used >= settings.ai_daily_limit:
        raise AiLimitReached(
            f"Bugungi AI limiti tugadi ({settings.ai_daily_limit}). "
            "Qo'lda kiritishingiz mumkin."
        )


async def bump_daily_usage(db: AsyncSession, user_id: int) -> None:
    """Bugungi hisobni +1. Matn va rasm birga hisoblanadi."""
    today = datetime.now(UTC).date()
    stmt = (
        pg_insert(AiUsage)
        .values(user_id=user_id, day=today, count=1)
        .on_conflict_do_update(
            index_elements=["user_id", "day"],
            set_={"count": AiUsage.count + 1},
        )
    )
    await db.execute(stmt)
    await db.commit()


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------
_client = None


def _get_client():
    global _client
    if not settings.gemini_api_key:
        raise AiUnavailable("GEMINI_API_KEY sozlanmagan")
    if _client is None:
        from google import genai  # importni kechiktiramiz

        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _parse_json(raw: str) -> dict:
    text = _FENCE.sub("", (raw or "").strip()).strip()
    if not text:
        raise AiBadResponse("bo'sh javob")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # ba'zan model matn ichiga JSON joylaydi — birinchi {...} ni ol
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise AiBadResponse("javob JSON emas") from exc
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError as exc2:
            raise AiBadResponse("javob JSON emas") from exc2
    if not isinstance(data, dict):
        raise AiBadResponse("javob obyekt emas")
    if data.get("error"):
        raise AiRefused(str(data["error"]))
    return data


def _generate(contents: list, label: str = "call") -> dict:
    client = _get_client()
    from google.genai import types

    started = time.perf_counter()
    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                http_options=types.HttpOptions(timeout=_TIMEOUT_S * 1000),
            ),
        )
    except (AiUnavailable, AiRefused, AiBadResponse):
        raise
    except Exception as exc:  # noqa: BLE001 — SDK turli xato turlarini beradi
        log.exception("Gemini chaqiruv xatosi")
        raise AiUnavailable("AI xizmati javob bermadi") from exc

    # Chaqiruv vaqti va tokenlar — sekinlashsa sababini bilish uchun
    usage = getattr(resp, "usage_metadata", None)
    log.info(
        "AI %s: %.1fs | in=%s tok | out=%s tok | model=%s",
        label,
        time.perf_counter() - started,
        getattr(usage, "prompt_token_count", "?"),
        getattr(usage, "candidates_token_count", "?"),
        settings.gemini_model,
    )
    return _parse_json(getattr(resp, "text", "") or "")


# --------------------------------------------------------------------------
# Ommaviy funksiyalar
# --------------------------------------------------------------------------
async def parse_text(
    text: str,
    price_items: Sequence[tuple[int, str]],
    unit_codes: Sequence[str],
) -> dict:
    """Erkin matndan yozuv maydonlarini qaytaradi (xom, tekshirilmagan)."""
    catalog = "\n".join(f"{pid} — {name}" for pid, name in price_items[:60])
    units = ", ".join(unit_codes) or _UNIT_HINT
    prompt = _TEXT_PROMPT.format(
        units=units, catalog=catalog or "(bo'sh)", text=text.strip()
    )
    return await run_in_threadpool(_generate, [prompt], "parse")


async def scan_receipt(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Chek suratidan yozuv maydonlarini qaytaradi (xom, tekshirilmagan)."""
    from google.genai import types

    part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    return await run_in_threadpool(_generate, [_RECEIPT_PROMPT, part], "receipt")


def build_note_text(items: list[dict]) -> str:
    """'Sement 5 qop × 130 000' qatorlari, \\n bilan."""
    lines = []
    for it in items or []:
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        qty = str(it.get("quantity") or "").strip()
        unit = str(it.get("unit") or "").strip()
        price = str(it.get("unit_price") or it.get("amount") or "").strip()
        parts = [name]
        if qty:
            parts.append(qty + (f" {unit}" if unit else ""))
        if price:
            parts.append(f"× {price}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def parse_receipt_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
