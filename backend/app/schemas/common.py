"""Umumiy sxemalar."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LaborSummary(BaseModel):
    """Ish haqi — yagona qarz manbai.

    remaining = works_total − paid. Manfiy bo'lsa — mijoz avansi.
    """

    works_total: Decimal
    paid: Decimal
    remaining: Decimal


class MaterialsSummary(BaseModel):
    """Material va xarajat — faqat ro'yxat va jami. Qarz yo'q:
    materialni har doim mijoz to'laydi."""

    materials_total: Decimal
    expenses_total: Decimal
    total_spent: Decimal  # materials_total + expenses_total


class SummaryMeta(BaseModel):
    entries_count: int
    last_entry_date: date | None


class ProjectSummary(BaseModel):
    """GET /api/projects/{id}/summary — bitta qarz + material ro'yxati + meta."""

    labor: LaborSummary
    materials: MaterialsSummary
    meta: SummaryMeta
