"""Tarix lentasi — yozuvlar va to'lovlar bitta oqimda."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class TimelineEntry(BaseModel):
    type: Literal["entry"] = "entry"
    id: int
    kind: str  # work | material | expense
    name: str
    quantity: Decimal
    unit: str
    unit_label: str | None
    unit_price: Decimal
    amount: Decimal
    paid_by: str
    payment_method: str | None
    is_rework: bool
    has_receipt: bool
    note: str | None
    entry_date: date
    created_at: datetime


class TimelinePayment(BaseModel):
    type: Literal["payment"] = "payment"
    id: int
    kind: Literal["payment"] = "payment"  # filtr birxilligi uchun
    purpose: str  # labor | material
    amount: Decimal
    method: str
    note: str | None
    paid_at: date
    created_at: datetime


TimelineItem = TimelineEntry | TimelinePayment


class TimelinePage(BaseModel):
    items: list[TimelineItem]
    page: int
    pages: int
    total: int
