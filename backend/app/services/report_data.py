"""Hisobot PDF uchun ma'lumot yig'ish — API va bot uchun bir xil.

Faqat bazadan: entries + `build_project_summary` (ish haqi qarzi uchun).
Ish haqi hisob-kitobi butun loyiha bo'yicha — Mini App'dagi raqamlar bilan
bir xil bo'lishi uchun sana filtri unga ta'sir qilmaydi.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Category,
    Entry,
    MeasureUnit,
    PriceItem,
    Project,
    ProjectPrice,
    User,
)
from app.services.report_pdf import (
    ExpenseRow,
    MaterialRow,
    ReportData,
    WorkRow,
)
from app.services.summary import build_project_summary


# apostrof variantlari (o' g' va h.k.) — butunlay olib tashlanadi
_STRIP_CHARS = "'`‘’ʻʼ"


def report_filename(title: str, on: date, part: str = "") -> str:
    """'Tarovat 145-uy' + 'ish-haqi' -> 'Tarovat-145-uy_ish-haqi_2026-08-30.pdf'.

    Translit, ASCII-xavfsiz. `part` bo'sh bo'lsa tushirib qoldiriladi.
    """
    text = "".join("" if ch in _STRIP_CHARS else ch for ch in title)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    out = [ch if ch.isalnum() else "-" if ch in " -_" else "" for ch in text]
    slug = "-".join(filter(None, "".join(out).split("-"))) or "hisobot"
    mid = f"_{part}" if part else ""
    return f"{slug}{mid}_{on.isoformat()}.pdf"


async def gather_report_data(
    db: AsyncSession,
    project: Project,
    master: User,
    date_from: date | None,
    date_to: date | None,
) -> ReportData:
    stmt = (
        select(Entry, Category.name, MeasureUnit.label)
        .outerjoin(ProjectPrice, ProjectPrice.id == Entry.project_price_id)
        .outerjoin(PriceItem, PriceItem.id == ProjectPrice.price_item_id)
        .outerjoin(Category, Category.id == PriceItem.category_id)
        .outerjoin(
            MeasureUnit,
            (MeasureUnit.user_id == project.user_id)
            & (MeasureUnit.code == Entry.unit),
        )
        .where(Entry.project_id == project.id, Entry.deleted_at.is_(None))
    )
    if date_from is not None:
        stmt = stmt.where(Entry.entry_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Entry.entry_date <= date_to)
    stmt = stmt.order_by(Entry.entry_date, Entry.id)

    works: list[WorkRow] = []
    materials: list[MaterialRow] = []
    expenses: list[ExpenseRow] = []

    for entry, cat_name, unit_label in (await db.execute(stmt)).all():
        unit = unit_label or entry.unit
        if entry.kind == "work":
            works.append(WorkRow(
                day=entry.entry_date,
                name=entry.name,
                category=cat_name or "Kategoriyasiz",
                qty=entry.quantity,
                unit_label=unit,
                unit_price=entry.unit_price,
                amount=entry.amount,
                is_rework=entry.is_rework,
                note=entry.note,
            ))
        elif entry.kind == "material":
            materials.append(MaterialRow(
                day=entry.entry_date,
                name=entry.name,
                qty=entry.quantity,
                unit_label=unit,
                unit_price=entry.unit_price,
                amount=entry.amount,
                method=entry.payment_method,
                vendor=entry.vendor,
                note=entry.note,
            ))
        elif entry.kind == "expense":
            expenses.append(ExpenseRow(
                day=entry.entry_date,
                name=entry.name,
                amount=entry.amount,
                method=entry.payment_method,
                note=entry.note,
            ))

    summary = await build_project_summary(db, project.id)

    return ReportData(
        project_title=project.title,
        client_name=project.client_name,
        master_name=master.full_name,
        master_phone=master.phone,
        generated_at=datetime.now(UTC).date(),
        period_from=date_from,
        period_to=date_to,
        works=works,
        materials=materials,
        expenses=expenses,
        works_total=summary.labor.works_total,
        paid_labor=summary.labor.paid,
    )
