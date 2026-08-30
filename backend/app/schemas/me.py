"""Joriy foydalanuvchi sxemalari."""

from typing import Literal

from pydantic import BaseModel, Field


class MeRead(BaseModel):
    id: int
    full_name: str
    username: str | None
    phone: str | None
    language: str
    theme: str
    # bo'sh bo'lsa frontend Telegram rasmini ishlatadi
    avatar_url: str | None
    active_projects: int
    completed_projects: int


class MeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    theme: Literal["light", "dark", "auto"] | None = None
    language: str | None = Field(default=None, min_length=2, max_length=8)
