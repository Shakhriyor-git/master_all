"""Hisobot PDF sinovi — ikkala hujjat (ish haqi + material).

Har biri uchun /tmp/report_test_*.pdf ga yozadi va sahifa sonini chiqaradi:
seed obyekt, bo'sh obyekt, kirill matnli yozuvlar (шлакаблок, газаблок) va
500 yozuvli perf holati.

Ishga tushirish:  docker compose exec api python scripts/test_report.py
"""

import asyncio
import datetime
import pathlib
import sys
import time
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import Project, User  # noqa: E402
from app.services.report_data import (  # noqa: E402
    gather_report_data,
    report_filename,
)
from app.services.report_pdf import (  # noqa: E402
    ExpenseRow,
    MaterialRow,
    ReportData,
    WorkRow,
    build_labor_pdf_with_pages,
    build_materials_pdf_with_pages,
)

import scripts.seed as seed_mod  # noqa: E402

OUT_DIR = pathlib.Path("/tmp")


async def _seed_project(session) -> tuple[Project, User]:
    user = (
        await session.execute(
            select(User).where(
                User.telegram_id == seed_mod.TEST_TELEGRAM_ID
            )
        )
    ).scalar_one()
    project = (
        await session.execute(
            select(Project).where(
                Project.user_id == user.id,
                Project.title == seed_mod.TEST_PROJECT_TITLE,
            )
        )
    ).scalar_one()
    return project, user


def _big_data() -> ReportData:
    day = datetime.date(2026, 8, 1)
    works = [
        WorkRow(
            day=day + datetime.timedelta(days=i % 25),
            name=f"Ish pozitsiyasi {i}",
            category=f"Kategoriya {i % 6}",
            qty=Decimal("11.5"),
            unit_label="m²",
            unit_price=Decimal("25000"),
            amount=Decimal("287500"),
            is_rework=(i % 20 == 0),
        )
        for i in range(320)
    ]
    materials = [
        MaterialRow(
            day=day + datetime.timedelta(days=i % 25),
            name=f"Material {i}",
            qty=Decimal("3"),
            unit_label="qop",
            unit_price=Decimal("45000"),
            amount=Decimal("135000"),
            method="card",
        )
        for i in range(180)
    ]
    return ReportData(
        project_title="Katta obyekt 500 yozuv",
        client_name="Sinov mijozi",
        master_name="Shahriyor",
        master_phone="+998916600106",
        generated_at=datetime.date(2026, 8, 30),
        works=works,
        materials_master=materials,
        works_total=Decimal("90000000"),
        materials_by_master=Decimal("24300000"),
        paid_labor=Decimal("50000000"),
        client_owes=Decimal("64300000"),
    )


def _cyrillic_data() -> ReportData:
    """Kirill matnli yozuvlar — DejaVu shrift xaritasi to'g'ri ishlashini
    tekshiradi (bazada шлакаблок, газаблок kabi nomlar bor)."""
    day = datetime.date(2026, 8, 15)
    return ReportData(
        project_title="Объект: Чиланзар, 12-й квартал",
        client_name="Мижоз Акмал ака",
        master_name="Уста Шакир",
        master_phone="+998901234567",
        generated_at=datetime.date(2026, 9, 1),
        works=[
            WorkRow(
                day=day, name="Стяжка пола", category="Черновые работы",
                qty=Decimal("48"), unit_label="м²",
                unit_price=Decimal("35000"), amount=Decimal("1680000"),
                note="Материал: шлакаблок ва газаблок ишлатилди",
            ),
            WorkRow(
                day=day, name="Шпаклёвка стен", category="Черновые работы",
                qty=Decimal("120"), unit_label="м²",
                unit_price=Decimal("18000"), amount=Decimal("2160000"),
                is_rework=True, note="Қайта қилинди — брак",
            ),
        ],
        materials_master=[
            MaterialRow(
                day=day, name="Шлакоблок", qty=Decimal("200"),
                unit_label="дона", unit_price=Decimal("4500"),
                amount=Decimal("900000"), method="cash",
                vendor="Қурилиш бозори",
                note="шлакаблок — 200 дона\nгазаблок — 40 дона\nцемент — 5 қоп",
            ),
        ],
        expenses_master=[
            ExpenseRow(
                day=day, name="Такси (материал ташиш)",
                amount=Decimal("120000"), method="cash",
            ),
        ],
        materials_client=[
            MaterialRow(
                day=day, name="Обойный клей", qty=Decimal("3"),
                unit_label="дона", unit_price=Decimal("45000"),
                amount=Decimal("135000"), method="card",
            ),
        ],
        works_total=Decimal("1680000"),
        materials_by_master=Decimal("900000"),
        paid_labor=Decimal("1000000"),
        client_owes=Decimal("1580000"),
        budget_given=Decimal("500000"),
        budget_spent_materials=Decimal("135000"),
    )


_DOCS = (
    ("ish-haqi", build_labor_pdf_with_pages),
    ("material", build_materials_pdf_with_pages),
)


async def main() -> None:
    # 1) seed (idempotent) + haqiqiy obyekt uchun ikkala hujjat
    await seed_mod.main()
    async with SessionLocal() as session:
        project, user = await _seed_project(session)
        data = await gather_report_data(session, project, user, None, None)

    for part, builder in _DOCS:
        pdf, pages = builder(data)
        out = OUT_DIR / f"report_test_{part}.pdf"
        out.write_bytes(pdf)
        fname = report_filename(project.title, data.generated_at, part)
        print(f"{part:9} {out}  ({fname}, {len(pdf) / 1024:.1f} KB, "
              f"{pages} sahifa)")

    # 2) bo'sh obyekt — yiqilmasligi kerak
    empty = ReportData(
        project_title="Bo'sh obyekt",
        client_name=None,
        master_name="Usta",
        master_phone=None,
        generated_at=datetime.date(2026, 8, 30),
    )
    for part, builder in _DOCS:
        epdf, epages = builder(empty)
        print(f"Bo'sh ({part}): {epages} sahifa, {len(epdf)} bayt — OK")

    # 3) kirill matnli yozuvlar — shrift xaritasi buzilmasligi kerak
    for part, builder in _DOCS:
        cpdf, cpages = builder(_cyrillic_data())
        out = OUT_DIR / f"report_test_cyr_{part}.pdf"
        out.write_bytes(cpdf)
        print(f"Kirill ({part}): {cpages} sahifa, {len(cpdf) / 1024:.1f} KB "
              f"— OK  ({out})")

    # 4) 500 yozuvli hisobot — 3 soniyadan tez bo'lsin
    for part, builder in _DOCS:
        t0 = time.perf_counter()
        bpdf, bpages = builder(_big_data())
        dt = time.perf_counter() - t0
        (OUT_DIR / f"report_test_big_{part}.pdf").write_bytes(bpdf)
        print(f"500 yozuv ({part}): {bpages} sahifa, {dt:.2f}s "
              f"({'OK' if dt < 3 else 'SEKIN!'})")


if __name__ == "__main__":
    asyncio.run(main())
