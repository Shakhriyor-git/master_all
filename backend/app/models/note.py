"""Qayd modellari — usta uchun erkin matn va belgilanadigan ro'yxat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import text as sa_text  # NoteItem.text ustuni bilan chalkashmasin
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Note(TimestampMixin, SoftDeleteMixin, Base):
    """Qayd — matn (`body`), ro'yxat (`items`) yoki ikkalasi birga."""

    __tablename__ = "notes"
    __table_args__ = (
        Index(
            "ix_notes_user_id_project_id_is_pinned",
            "user_id",
            "project_id",
            "is_pinned",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # umumiy qayd bo'lsa NULL
    project_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # erkin matn
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_text("false")
    )

    user: Mapped[User] = relationship("User", lazy="raise")
    project: Mapped[Project | None] = relationship("Project", lazy="raise")
    items: Mapped[list[NoteItem]] = relationship(
        "NoteItem",
        back_populates="note",
        lazy="raise",
        cascade="all, delete-orphan",
        order_by="NoteItem.sort_order, NoteItem.id",
    )


class NoteItem(Base):
    """Qayd ichidagi belgilanadigan qator (xarid ro'yxati uchun)."""

    __tablename__ = "note_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_text("false")
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=sa_text("0")
    )

    note: Mapped[Note] = relationship(
        "Note", back_populates="items", lazy="raise"
    )
