"""Formatlash va kichik yordamchilar."""

import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal, InvalidOperation

# Birlik kodini chiroyli ko'rinishga
_UNIT_DISPLAY = {"m2": "m²", "m3": "m³"}

# Oxiridagi harf/belgilar ("25000 so'm" -> "25000")
_TRAILING_JUNK = re.compile(r"[^\d.,]+$")
# Faqat raqam va ajratuvchilardan iborat, raqam bilan boshlanadi
_NUMERIC = re.compile(r"\d[\d.,]*")
# Kasr dumi: [.,] + 1-2 raqam + satr oxiri
_FRACTION_TAIL = re.compile(r"[.,]\d{1,2}$")


def fmt_money(value: Decimal | int | float | None) -> str:
    """2080000 -> '2 080 000 so'm'. Ajratuvchi — oddiy bo'shliq."""
    number = int(round(Decimal(value or 0)))
    grouped = f"{abs(number):,}".replace(",", " ")
    sign = "-" if number < 0 else ""
    return f"{sign}{grouped} so'm"


def fmt_qty(value: Decimal) -> str:
    """Ortiqcha nollarni olib tashlaydi: 11.500 -> '11.5', 4.000 -> '4'."""
    text = format(Decimal(value).normalize(), "f")
    return text


def fmt_unit(unit: str) -> str:
    return _UNIT_DISPLAY.get(unit, unit)


def fmt_date(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "—"


def _clean(text: str) -> str | None:
    """Bo'shliqlar va oxiridagi harflarni tashlaydi. Yaroqsiz bo'lsa None."""
    if not text:
        return None
    s = text.replace(" ", " ").strip()
    if "-" in s:
        return None
    s = _TRAILING_JUNK.sub("", s).replace(" ", "")
    if not s or not _NUMERIC.fullmatch(s):
        return None
    return s


def parse_money(text: str) -> Decimal | None:
    """Pul summasi — so'mda tiyin yo'q, butun songa yaxlitlanadi.

    "20000" "20,000" "20 000" "20.000" -> 20000
    "1,250,000.00" -> 1250000 (kasr dumi tashlanadi)
    "25000 so'm" -> 25000.  "-", "abc", "", "0" -> None
    """
    s = _clean(text)
    if s is None:
        return None

    seps = [c for c in s if c in ".,"]
    # Kasr dumi FAQAT undan oldin yana ajratuvchi bo'lsa (aks holda minglik)
    if len(seps) >= 2 and _FRACTION_TAIL.search(s):
        s = _FRACTION_TAIL.sub("", s)

    digits = s.replace(".", "").replace(",", "")
    if not digits.isdigit():
        return None
    value = Decimal(digits)
    return value if value > 0 else None


def parse_quantity(text: str) -> Decimal | None:
    """Miqdor — kasr ma'noli (11.5 m²).

    "11" -> 11.  "11,5" / "11.5" -> 11.5.  "1,25" -> 1.25.
    "1.250,75" -> 1250.75 (oxirgi ajratuvchi kasr).
    "1,500" -> 1500 (bitta ajratuvchi + aniq 3 raqam = minglik).
    "-", "abc", "", "0" -> None
    """
    s = _clean(text)
    if s is None:
        return None

    seps = [c for c in s if c in ".,"]
    if not seps:
        norm = s
    elif len(seps) >= 2:
        # oxirgi ajratuvchi — kasr nuqtasi, qolganlari minglik
        cut = max(s.rfind("."), s.rfind(","))
        norm = s[:cut].replace(".", "").replace(",", "") + "." + s[cut + 1 :]
    else:
        cut = s.rfind(".") if "." in s else s.rfind(",")
        after = s[cut + 1 :]
        norm = s[:cut] + after if len(after) == 3 else s[:cut] + "." + after

    try:
        value = Decimal(norm)
    except InvalidOperation:
        return None
    return value if value > 0 else None


def paginate[T](
    items: Sequence[T], page: int, per_page: int = 10
) -> tuple[list[T], int, int]:
    """(sahifadagi elementlar, joriy sahifa, jami sahifalar) — 1 dan boshlab."""
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return list(items[start : start + per_page]), page, total_pages
