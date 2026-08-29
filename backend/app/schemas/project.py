"""Loyiha sxemalari."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    client_name: str | None = Field(default=None, max_length=200)
    client_phone: str | None = Field(default=None, max_length=32)
    client_telegram_id: int | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    note: str | None = None
    started_at: date | None = None
    closed_at: date | None = None


class ProjectUpdate(BaseModel):
    """Hamma maydon optional — faqat yuborilganlari o'zgaradi."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    client_name: str | None = Field(default=None, max_length=200)
    client_phone: str | None = Field(default=None, max_length=32)
    client_telegram_id: int | None = None
    status: ProjectStatus | None = None
    note: str | None = None
    started_at: date | None = None
    closed_at: date | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    address: str | None
    client_name: str | None
    client_phone: str | None
    client_telegram_id: int | None
    status: str
    note: str | None
    started_at: date | None
    closed_at: date | None
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None
