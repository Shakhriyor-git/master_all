"""Kategoriya sxemalari."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EntryKind


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: EntryKind
    icon: str | None = Field(default=None, max_length=20)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    kind: str
    icon: str | None
    sort_order: int
    is_active: bool
    # Web App'da "Elektrika · 6 ta xizmat" ko'rinishi uchun
    items_count: int = 0
    created_at: datetime
    updated_at: datetime | None
