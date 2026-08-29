"""Umumiy sxemalar."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    """Loyiha balansi — GET /api/projects/{id}/summary."""

    works_total: Decimal
    materials_by_master: Decimal
    materials_by_client: Decimal
    paid_total: Decimal
    client_owes: Decimal
    entries_count: int
    last_entry_date: date | None
