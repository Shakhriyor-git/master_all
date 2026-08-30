"""O'lchov birligi modeli (jadval `units`).

Klass nomi `MeasureUnit` — `enums` da endi `Unit` yo'q, lekin chalkashmaslik
uchun ataylab boshqa nom.

`entries.unit` va `price_items.unit` shu jadvaldagi `code` ni saqlaydi, lekin
FK QO'YILMAYDI: birlik o'chirilsa ham eski yozuvlar buzilmasligi kerak.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class MeasureUnit(TimestampMixin, Base):
    """Ustaning o'lchov birligi — `m2` (code) / `m²` (label)."""

    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_units_user_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # bazada saqlanadigan qiymat
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    # ko'rsatiladigan matn
    label: Mapped[str] = mapped_column(String(30), nullable=False)
    # standart birlik — o'chirib bo'lmaydi
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[User] = relationship("User", lazy="raise")
