"""AI kiritish sxemalari — matn va chek uchun yagona javob shakli."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class AiParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class AiDraft(BaseModel):
    """Tasdiqlash formasi shu javobdan oldindan to'ldiriladi."""

    kind: Literal["work", "material", "expense"] = "material"
    name: str = ""
    quantity: Decimal | None = None
    unit: str | None = None
    # amount — JAMI summa; unit_price = amount / quantity
    amount: Decimal | None = None
    unit_price: Decimal | None = None
    paid_by: Literal["master", "client"] | None = None
    payment_method: Literal["cash", "card", "transfer"] | None = None
    matched_price_item_id: int | None = None
    vendor: str | None = None
    entry_date: date | None = None
    note: str | None = None
    confidence: Literal["high", "low"] = "low"
