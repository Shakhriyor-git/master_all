"""Yozuv modeli — bajarilgan ishlar va ishlatilgan materiallar."""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    event,
    func,
    text,
)
from sqlalchemy.orm import Mapped, Mapper, mapped_column, relationship

from app.core.db import Base
from app.models.enums import EntryKind, PaidBy
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
        # Pul bilan bog'liq qoidalar — bazada ham turadi (listener yetarli emas:
        # bulk update da ishlamaydi, refaktorda yo'qolishi mumkin).
        CheckConstraint(
            "NOT (is_rework AND is_billable)",
            name="ck_entries_rework_not_billable",
        ),
        CheckConstraint(
            "NOT (kind = 'expense' AND paid_by = 'master' AND is_billable)",
            name="ck_entries_master_expense_not_billable",
        ),
        CheckConstraint(
            "kind <> 'work' OR (payment_method IS NULL AND vendor IS NULL)",
            name="ck_entries_work_no_payment_fields",
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
    # master / client — material va expense uchun ma'noli
    paid_by: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="master"
    )
    # mijozga hisoblanadimi (server qoidasi bilan majburlanadi)
    is_billable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    # brak / qayta qilingan ish
    is_rework: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    # cash / card / transfer — faqat material va expense uchun
    payment_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    # qayerdan olindi — "Qurilish bozori"
    vendor: Mapped[str | None] = mapped_column(String(200), nullable=True)
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


@event.listens_for(Entry, "before_insert")
@event.listens_for(Entry, "before_update")
def _enforce_entry_rules(
    mapper: Mapper, connection: object, target: Entry
) -> None:
    """A5 qoidalari — ORM yozuvlarida qiymatlarni to'g'rilaydi.

    Baza CHECK constraint'lari backstop; bu listener foydalanuvchiga 500
    o'rniga to'g'ri natija beradi.
    """
    if target.is_rework:
        target.is_billable = False
    effective_paid_by = target.paid_by or PaidBy.MASTER.value
    if (
        target.kind == EntryKind.EXPENSE
        and effective_paid_by == PaidBy.MASTER.value
    ):
        target.is_billable = False
    if target.kind == EntryKind.WORK:
        target.payment_method = None
        target.vendor = None
