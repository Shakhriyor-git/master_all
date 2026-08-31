"""Joriy foydalanuvchi sxemalari."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SocialLink(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    url: str = Field(min_length=1, max_length=300)

    @field_validator("url")
    @classmethod
    def _https_only(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("Havola https:// bilan boshlanishi kerak")
        return v


class MeRead(BaseModel):
    id: int
    full_name: str
    username: str | None
    phone: str | None
    language: str
    theme: str
    onboarded: bool
    # bo'sh bo'lsa frontend Telegram rasmini ishlatadi
    avatar_url: str | None
    social_links: list[SocialLink]
    active_projects: int
    completed_projects: int


class MeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    theme: Literal["light", "dark", "auto"] | None = None
    language: str | None = Field(default=None, min_length=2, max_length=8)
    onboarded: bool | None = None
    social_links: list[SocialLink] | None = Field(default=None, max_length=5)
