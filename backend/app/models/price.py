"""Narx modellari — ustaning katalogi va loyihaga kelishilgan narxlar."""

from __future__ import annotations

from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.entry import Entry
    from app.models.project import Project
    from app.models.user import User


class PriceItem(TimestampMixin, Base):
    """Ustaning shaxsiy narx katalogi."""

    __tablename__ = "price_items"
    __table_args__ = (
        Index("ix_price_items_user_id_is_active", "user_id", "is_active"),
        UniqueConstraint(
            "user_id", "name", "kind", name="uq_price_items_user_name_kind"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # work / material
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # m2, m3, dona, qop, metr, kg, soat, komplekt
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    default_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[User] = relationship(
        "User", back_populates="price_items", lazy="raise"
    )
    project_prices: Mapped[list[ProjectPrice]] = relationship(
        "ProjectPrice", back_populates="price_item", lazy="raise"
    )


class ProjectPrice(TimestampMixin, Base):
    """Loyihaga kelishilgan narx — katalogdan NUSXA.

    Katalogda narx keyin o'zgarsa ham, eski loyiha hisoboti o'zgarmaydi.
    """

    __tablename__ = "project_prices"
    __table_args__ = (
        Index("ix_project_prices_project_id_kind", "project_id", "kind"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    # manba; bir martalik pozitsiya uchun NULL
    price_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("price_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    # nusxa olingan nom
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    # shu loyihada kelishilgan narx
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    project: Mapped[Project] = relationship(
        "Project", back_populates="prices", lazy="raise"
    )
    price_item: Mapped[PriceItem | None] = relationship(
        "PriceItem", back_populates="project_prices", lazy="raise"
    )
    entries: Mapped[list[Entry]] = relationship(
        "Entry", back_populates="project_price", lazy="raise"
    )
