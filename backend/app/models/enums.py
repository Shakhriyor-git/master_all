"""Enum qiymatlar. Python tomonda StrEnum, bazada VARCHAR sifatida saqlanadi.

Diqqat: o'lchov birligi (unit) uchun enum YO'Q — usta o'z birligini qo'sha
oladi, shuning uchun unit hamma joyda oddiy `str`. Standart birliklar ro'yxati
`app/services/catalog_seed.py` da konstanta, tekshirish kerak bo'lsa `units`
jadvalidagi `code` lar bilan solishtiriladi.
"""

import enum


class ProjectStatus(enum.StrEnum):
    """Loyiha holati."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EntryKind(enum.StrEnum):
    """Yozuv turi."""

    WORK = "work"
    MATERIAL = "material"
    # ovqat, transport, asbob ijarasi — quantity=1, unit='summa'
    EXPENSE = "expense"


class PaidBy(enum.StrEnum):
    """Kim to'lagan (material va expense uchun ma'noli)."""

    MASTER = "master"
    CLIENT = "client"


class PaymentMethod(enum.StrEnum):
    """To'lov usuli — material va expense yozuvlari uchun."""

    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class PaymentPurpose(enum.StrEnum):
    """To'lov maqsadi — ikkita mustaqil qarz.

    labor     — mijoz ish haqi uchun to'ladi (ish haqi qarzini kamaytiradi)
    material  — mijoz material uchun to'ladi (material qarzini kamaytiradi)
    """

    LABOR = "labor"
    MATERIAL = "material"


class EntrySource(enum.StrEnum):
    """Yozuv qayerdan kelgan."""

    MANUAL = "manual"
    VOICE = "voice"
    OCR = "ocr"
