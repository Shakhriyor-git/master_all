"""Barcha modellar shu yerda import qilinadi — Alembic autogenerate ko'rishi uchun."""

from app.models.entry import Entry
from app.models.payment import Payment
from app.models.price import PriceItem, ProjectPrice
from app.models.project import Project
from app.models.user import User

__all__ = [
    "Entry",
    "Payment",
    "PriceItem",
    "Project",
    "ProjectPrice",
    "User",
]
