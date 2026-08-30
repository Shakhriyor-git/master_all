"""Narx sxemalari — katalog va loyiha narxlari."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EntryKind

# unit — units jadvalidagi code (enum emas; usta o'z birligini qo'sha oladi)


class PriceItemCreate(BaseModel):
    category_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    kind: EntryKind
    unit: str = Field(min_length=1, max_length=20)
    default_price: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True


class PriceItemUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: EntryKind | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    default_price: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class PriceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    kind: str
    unit: str
    default_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class ProjectPriceCreate(BaseModel):
    """price_item_id berilsa katalogdan nusxa, aks holda qo'lda kiritish."""

    price_item_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: EntryKind | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    price: Decimal | None = Field(default=None, ge=0)


class ProjectPriceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: EntryKind | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    price: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProjectPriceImport(BaseModel):
    price_item_ids: list[int] = Field(min_length=1)


class ProjectPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    price_item_id: int | None
    name: str
    kind: str
    unit: str
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
