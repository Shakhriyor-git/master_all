"""Hisob-kitob PDF sinovi.

Seed ma'lumot bilan PDF yasaydi, /tmp/report_test.pdf ga saqlaydi va
sahifa sonini chiqaradi. Perf va bo'sh obyekt holatini ham tekshiradi.

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

    # 3) 500 yozuvli hisobot — 3 soniyadan tez bo'lsin
    for part, builder in _DOCS:
        t0 = time.perf_counter()
        bpdf, bpages = builder(_big_data())
        dt = time.perf_counter() - t0
        (OUT_DIR / f"report_test_big_{part}.pdf").write_bytes(bpdf)
        print(f"500 yozuv ({part}): {bpages} sahifa, {dt:.2f}s "
              f"({'OK' if dt < 3 else 'SEKIN!'})")


if __name__ == "__main__":
    asyncio.run(main())
