"""Umumiy sxemalar."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LaborSummary(BaseModel):
    """Ish haqi qarzi — bajarilgan ishlar minus mijoz ish haqi uchun to'lagani."""

    works_total: Decimal
    paid: Decimal
    remaining: Decimal  # manfiy bo'lsa — mijoz avansi


class MaterialsSummary(BaseModel):
    """Material qarzi — usta olgan material/xarajat minus mijoz material uchun
    to'lagani."""

    materials_total: Decimal  # paid_by=master materiallar
    expenses_total: Decimal  # paid_by=master xarajatlar
    paid: Decimal
    remaining: Decimal  # manfiy bo'lsa — mijoz avansi


class SummaryMeta(BaseModel):
    entries_count: int
    last_entry_date: date | None


class ProjectSummary(BaseModel):
    """GET /api/projects/{id}/summary — ikkita mustaqil qarz + meta."""

    labor: LaborSummary
    materials: MaterialsSummary
    # paid_by=client yozuvlar — mijoz o'zi sotib olgan, faqat ma'lumot uchun
    client_bought: Decimal
    meta: SummaryMeta
