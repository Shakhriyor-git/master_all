"""Kategoriya sxemalari."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EntryKind


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: EntryKind
    icon: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        """"Mebel " -> "Mebel" — bosh/oxirgi bo'shliqlar tozalanadi."""
        v = v.strip()
        if not v:
            raise ValueError("nom bo'sh bo'lishi mumkin emas")
        return v


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("nom bo'sh bo'lishi mumkin emas")
        return v


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
