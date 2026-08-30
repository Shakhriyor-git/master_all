"""Yozuv sxemalari."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EntryKind, EntrySource, PaidBy, PaymentMethod

# unit — units jadvalidagi code (enum emas; usta o'z birligini qo'sha oladi)


class EntryCreate(BaseModel):
    """project_price_id berilsa nom/birlik/narx shundan olinadi.

    Berilmasa — qo'lda yozuv, name/unit/unit_price/kind majburiy.
    kind='expense' bo'lsa quantity=1, unit='summa' avtomatik.
    """

    project_price_id: int | None = None
    # Mini App: katalog pozitsiyasi — project_price kerak bo'lsa yaratiladi
    price_item_id: int | None = None
    kind: EntryKind | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    unit_price: Decimal | None = Field(default=None, ge=0)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    paid_by: PaidBy = PaidBy.MASTER
    is_rework: bool = False
    payment_method: PaymentMethod | None = None
    vendor: str | None = Field(default=None, max_length=200)
    entry_date: date | None = None
    note: str | None = None
    receipt_file_id: str | None = Field(default=None, max_length=255)
    source: EntrySource = EntrySource.MANUAL


class EntryUpdate(BaseModel):
    kind: EntryKind | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    paid_by: PaidBy | None = None
    is_rework: bool | None = None
    is_billable: bool | None = None
    payment_method: PaymentMethod | None = None
    vendor: str | None = Field(default=None, max_length=200)
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
    is_billable: bool
    is_rework: bool
    payment_method: str | None
    vendor: str | None
    entry_date: date
    note: str | None
    receipt_file_id: str | None
    source: str
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None


class EntryDetailRead(EntryRead):
    """Web App'dagi batafsil oyna aynan shundan quriladi (JOIN bilan)."""

    category_name: str | None = None
    unit_label: str | None = None
    has_receipt: bool = False


class EntryPage(BaseModel):
    items: list[EntryDetailRead]
    page: int
    pages: int
    total: int
