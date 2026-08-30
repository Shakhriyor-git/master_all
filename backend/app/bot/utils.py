"""Formatlash va kichik yordamchilar."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal, InvalidOperation

# Birlik kodini chiroyli ko'rinishga
_UNIT_DISPLAY = {"m2": "m²", "m3": "m³"}


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


def parse_quantity(text: str) -> Decimal | None:
    """'11,5' yoki '11.5' -> Decimal('11.5'). Yaroqsiz yoki <= 0 bo'lsa None."""
    if not text:
        return None
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    return value


def paginate[T](
    items: Sequence[T], page: int, per_page: int = 10
) -> tuple[list[T], int, int]:
    """(sahifadagi elementlar, joriy sahifa, jami sahifalar) — 1 dan boshlab."""
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return list(items[start : start + per_page]), page, total_pages
