"""Enum qiymatlar. Python tomonda StrEnum, bazada VARCHAR sifatida saqlanadi."""

import enum


class ProjectStatus(enum.StrEnum):
    """Loyiha holati."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EntryKind(enum.StrEnum):
    """Yozuv turi: ish yoki material."""

    WORK = "work"
    MATERIAL = "material"


class Unit(enum.StrEnum):
    """O'lchov birligi."""

    M2 = "m2"
    M3 = "m3"
    DONA = "dona"
    QOP = "qop"
    METR = "metr"
    KG = "kg"
    SOAT = "soat"
    KOMPLEKT = "komplekt"


class PaidBy(enum.StrEnum):
    """Materialni kim to'lagan (faqat material uchun ma'noli)."""

    MASTER = "master"
    CLIENT = "client"


class PaymentMethod(enum.StrEnum):
    """To'lov usuli."""

    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class EntrySource(enum.StrEnum):
    """Yozuv qayerdan kelgan."""

    MANUAL = "manual"
    VOICE = "voice"
    OCR = "ocr"
