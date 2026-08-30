"""Qayd sxemalari."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteItemCreate(BaseModel):
    text: str = Field(min_length=1, max_length=300)


class NoteItemUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=300)
    is_done: bool | None = None
    sort_order: int | None = None


class NoteItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    text: str
    is_done: bool
    sort_order: int


class NoteCreate(BaseModel):
    project_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    body: str | None = None
    # ixtiyoriy — bir zumda ro'yxat bilan yaratish
    items: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    is_pinned: bool | None = None


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    project_id: int | None
    title: str
    body: str | None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime | None


class NoteListRead(NoteRead):
    """Ro'yxat kartasi uchun — ro'yxat elementlari sanog'i badge sifatida."""

    items_done: int = 0
    items_total: int = 0


class NoteDetailRead(NoteRead):
    items: list[NoteItemRead] = Field(default_factory=list)
