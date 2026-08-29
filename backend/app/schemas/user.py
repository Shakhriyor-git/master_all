"""Foydalanuvchi sxemalari."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    full_name: str
    username: str | None
    phone: str | None
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
