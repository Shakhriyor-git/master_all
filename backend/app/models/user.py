"""Foydalanuvchi (usta) modeli."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.price import PriceItem
    from app.models.project import Project


class User(TimestampMixin, Base):
    """Bot va Mini App foydalanuvchisi."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # BIGINT majburiy — Telegram ID int32 dan oshadi
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Telegram username, @ siz
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default="uz"
    )
    # light / dark / auto — Mini App mavzusi
    theme: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="auto"
    )
    # yuklangan avatar yo'li; bo'sh bo'lsa Telegram rasmi ishlatiladi
    avatar_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    # birinchi kirishda ism/telefon so'raladi — to'ldirilgach true
    onboarded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # Asosiy ekranda musiqa tugmasi ko'rsatilsinmi
    music_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # [{"label": "Instagram", "url": "https://..."}], maksimum 5 ta
    social_links: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    projects: Mapped[list[Project]] = relationship(
        "Project", back_populates="user", lazy="raise"
    )
    price_items: Mapped[list[PriceItem]] = relationship(
        "PriceItem", back_populates="user", lazy="raise"
    )
