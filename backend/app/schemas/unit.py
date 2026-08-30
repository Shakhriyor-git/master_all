"""O'lchov birligi sxemalari."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UnitCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    label: str = Field(min_length=1, max_length=30)


class UnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    code: str
    label: str
    is_system: bool
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
