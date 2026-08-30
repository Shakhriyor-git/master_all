"""Umumiy sxemalar."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LaborSummary(BaseModel):
    """Ish haqi hisobi — usta topgan pul."""

    works_total: Decimal
    materials_by_master: Decimal
    paid_labor: Decimal
    client_owes: Decimal
    rework_total: Decimal  # ma'lumot uchun
    expenses_by_master: Decimal  # ma'lumot uchun


class BudgetSummary(BaseModel):
    """Mijoz budjeti — xarajat uchun berilgan naqd."""

    given: Decimal
    spent_materials: Decimal
    spent_expenses: Decimal
    spent_total: Decimal
    balance: Decimal


class SummaryMeta(BaseModel):
    entries_count: int
    last_entry_date: date | None


class ProjectSummary(BaseModel):
    """GET /api/projects/{id}/summary — ikkita mustaqil hisob + meta."""

    labor: LaborSummary
    budget: BudgetSummary
    meta: SummaryMeta
