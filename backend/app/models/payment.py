"""To'lov modeli — mijozdan olingan pullar."""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    Text,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Payment(TimestampMixin, SoftDeleteMixin, Base):
    """Mijoz to'lagan summa."""

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_project_id_paid_at", "project_id", "paid_at"),
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # cash / card / transfer
    method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="cash"
    )
    paid_at: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(
        "Project", back_populates="payments", lazy="raise"
    )
    created_by: Mapped[User | None] = relationship("User", lazy="raise")
