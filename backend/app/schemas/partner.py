"""Brigada sxemalari — sheriklar va ularga berilgan pullar."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod


class PartnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=300)


class PartnerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=300)


class PartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None
    note: str | None
    created_at: datetime


class PartnerListItem(PartnerRead):
    """Ro'yxat qatori — agregatlar bitta so'rovda hisoblanadi."""

    total_paid: Decimal
    payments_count: int
    last_payment_at: date | None


class PartnerListRead(BaseModel):
    partners: list[PartnerListItem]
    grand_total: Decimal


class PartnerPaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: PaymentMethod = PaymentMethod.CASH
    paid_at: date | None = None
    note: str | None = Field(default=None, max_length=300)


class PartnerPaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    method: PaymentMethod | None = None
    paid_at: date | None = None
    note: str | None = Field(default=None, max_length=300)


class PartnerPaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partner_id: int
    amount: Decimal
    method: str
    paid_at: date
    note: str | None
    created_at: datetime
