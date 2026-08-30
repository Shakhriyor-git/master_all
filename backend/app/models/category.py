"""Kategoriya modeli — ustaning xizmat/material guruhlari."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.price import PriceItem
    from app.models.user import User


class Category(TimestampMixin, Base):
    """Xizmat yoki material guruhi — masalan "Elektrika" (work)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "name", "kind", name="uq_categories_user_name_kind"
        ),
        Index(
            "ix_categories_user_id_kind_is_active",
            "user_id",
            "kind",
            "is_active",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # work | material
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # emoji, karta ko'rinishi uchun
    icon: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[User] = relationship("User", lazy="raise")
    price_items: Mapped[list[PriceItem]] = relationship(
        "PriceItem", back_populates="category", lazy="raise"
    )
