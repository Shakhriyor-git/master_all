"""Yozuv sxemalari."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EntryKind, EntrySource, PaidBy, Unit


class EntryCreate(BaseModel):
    """project_price_id berilsa nom/birlik/narx shundan olinadi.

    Berilmasa — qo'lda bir martalik yozuv, name/unit/unit_price/kind majburiy.
    """

    project_price_id: int | None = None
    kind: EntryKind | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: Unit | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    quantity: Decimal = Field(gt=0)
    paid_by: PaidBy = PaidBy.MASTER
    entry_date: date | None = None
    note: str | None = None
    receipt_file_id: str | None = Field(default=None, max_length=255)
    source: EntrySource = EntrySource.MANUAL


class EntryUpdate(BaseModel):
    kind: EntryKind | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: Unit | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    paid_by: PaidBy | None = None
    entry_date: date | None = None
    note: str | None = None
    receipt_file_id: str | None = Field(default=None, max_length=255)
    source: EntrySource | None = None


class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_price_id: int | None
    created_by_user_id: int | None
    kind: str
    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    paid_by: str
    entry_date: date
    note: str | None
    receipt_file_id: str | None
    source: str
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None
