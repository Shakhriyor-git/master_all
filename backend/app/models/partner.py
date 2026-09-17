"""Brigada — ustaning sheriklari va ularga berilgan pullar.

Bu ustaning SHAXSIY daftari: obyektga bog'lanmaydi, hisobot/summary/PDF ga
kirmaydi. Faqat "kimga qancha berdim" tarixi.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User


class Partner(SoftDeleteMixin, Base):
    """Sherik (yordamchi). Ilovaga kirmaydi — faqat ism va telefon."""

    __tablename__ = "partners"
    __table_args__ = (
        Index("ix_partners_user_id_deleted_at", "user_id", "deleted_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship("User", lazy="raise")
    payments: Mapped[list[PartnerPayment]] = relationship(
        "PartnerPayment", back_populates="partner", lazy="raise"
    )


class PartnerPayment(SoftDeleteMixin, Base):
    """Sherikka berilgan bitta to'lov."""

    __tablename__ = "partner_payments"
    __table_args__ = (
        CheckConstraint(
            "amount > 0", name="ck_partner_payments_amount_positive"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # user_id ataylab takrorlangan — har so'rov shu ustun bilan filtrlanadi
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # cash / card / transfer
    method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="cash"
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    paid_at: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    partner: Mapped[Partner] = relationship(
        "Partner", back_populates="payments", lazy="raise"
    )


# (user_id, partner_id, paid_at DESC) — sherik tarixi sanaga qarab
Index(
    "ix_partner_payments_user_id_partner_id_paid_at",
    PartnerPayment.user_id,
    PartnerPayment.partner_id,
    PartnerPayment.paid_at.desc(),
)
