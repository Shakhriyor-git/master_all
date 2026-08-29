"""Yozuv modeli — bajarilgan ishlar va ishlatilgan materiallar."""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.price import ProjectPrice
    from app.models.project import Project
    from app.models.user import User


class Entry(TimestampMixin, SoftDeleteMixin, Base):
    """Loyihadagi bitta ish yoki material yozuvi."""

    __tablename__ = "entries"
    __table_args__ = (
        Index("ix_entries_project_id_entry_date", "project_id", "entry_date"),
        Index("ix_entries_project_id_kind", "project_id", "kind"),
        CheckConstraint("quantity > 0", name="ck_entries_quantity_positive"),
        CheckConstraint(
            "unit_price >= 0", name="ck_entries_unit_price_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_price_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("project_prices.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # hozircha har doim usta
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # work / material
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # yozuv paytidagi nom (snapshot)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        Computed("quantity * unit_price", persisted=True),
    )
    # master / client — faqat material uchun ma'noli
    paid_by: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="master"
    )
    # ish qilingan sana
    entry_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Telegram file_id yoki R2 key
    receipt_file_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # manual / voice / ocr
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="manual"
    )

    project: Mapped[Project] = relationship(
        "Project", back_populates="entries", lazy="raise"
    )
    project_price: Mapped[ProjectPrice | None] = relationship(
        "ProjectPrice", back_populates="entries", lazy="raise"
    )
    created_by: Mapped[User | None] = relationship("User", lazy="raise")
