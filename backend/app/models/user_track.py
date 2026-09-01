"""Foydalanuvchi musiqa treklari — ish paytida chalinadigan fayllar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserTrack(TimestampMixin, Base):
    """Bitta yuklangan audio fayl. Jami hajm foydalanuvchi bo'yicha cheklangan."""

    __tablename__ = "user_tracks"
    __table_args__ = (
        Index("ix_user_tracks_user_id_sort_order", "user_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # diskdagi tasodifiy nom (secrets.token_hex + kengaytma)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    # foydalanuvchi ko'radigan nom
    original_name: Mapped[str] = mapped_column(String(200), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    user: Mapped[User] = relationship("User", lazy="raise")
