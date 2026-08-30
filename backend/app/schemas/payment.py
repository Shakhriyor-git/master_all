"""To'lov sxemalari."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, PaymentPurpose


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: PaymentMethod = PaymentMethod.CASH
    # labor — ish haqi (qarzni kamaytiradi); budget — mijoz xarajat naqdi
    purpose: PaymentPurpose = PaymentPurpose.LABOR
    paid_at: date | None = None
    note: str | None = None


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    method: PaymentMethod | None = None
    purpose: PaymentPurpose | None = None
    paid_at: date | None = None
    note: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_by_user_id: int | None
    amount: Decimal
    method: str
    purpose: str
    paid_at: date
    note: str | None
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None
