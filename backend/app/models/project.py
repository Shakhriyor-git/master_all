"""Loyiha (obyekt) modeli."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ProjectStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.entry import Entry
    from app.models.payment import Payment
    from app.models.price import ProjectPrice
    from app.models.user import User


class Project(TimestampMixin, SoftDeleteMixin, Base):
    """Ustaning obyekti — masalan "Chilonzor 12-uy, 45-xonadon"."""

    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_user_id_status", "user_id", "status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # egasi (usta)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # keyinchalik mijozga read-only ko'rinish uchun
    client_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    # active / paused / completed / archived
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=ProjectStatus.ACTIVE.value,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(
        "User", back_populates="projects", lazy="raise"
    )
    prices: Mapped[list[ProjectPrice]] = relationship(
        "ProjectPrice", back_populates="project", lazy="raise"
    )
    entries: Mapped[list[Entry]] = relationship(
        "Entry", back_populates="project", lazy="raise"
    )
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="project", lazy="raise"
    )
