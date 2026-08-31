"""AI kunlik limitini hisoblash — matn va rasm birga."""

from __future__ import annotations

import datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class AiUsage(TimestampMixin, Base):
    """Bir foydalanuvchi bir kunda nechta AI so'rovi qilgani."""

    __tablename__ = "ai_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_ai_usage_user_day"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    day: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
