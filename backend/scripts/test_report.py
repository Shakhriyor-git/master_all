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
    build_report_pdf_with_pages,
)

import scripts.seed as seed_mod  # noqa: E402

OUT = pathlib.Path("/tmp/report_test.pdf")


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


async def main() -> None:
    # 1) seed (idempotent) + haqiqiy obyekt uchun PDF
    await seed_mod.main()
    async with SessionLocal() as session:
        project, user = await _seed_project(session)
        data = await gather_report_data(session, project, user, None, None)

    pdf, pages = build_report_pdf_with_pages(data)
    OUT.write_bytes(pdf)
    print(f"Fayl:        {OUT}")
    print(f"Fayl nomi:   {report_filename(project.title, data.generated_at)}")
    print(f"Hajm:        {len(pdf) / 1024:.1f} KB")
    print(f"Sahifalar:   {pages}")

    # 2) bo'sh obyekt — yiqilmasligi kerak
    empty = ReportData(
        project_title="Bo'sh obyekt",
        client_name=None,
        master_name="Usta",
        master_phone=None,
        generated_at=datetime.date(2026, 8, 30),
    )
    epdf, epages = build_report_pdf_with_pages(empty)
    print(f"Bo'sh obyekt: {epages} sahifa, {len(epdf)} bayt — OK")

    # 3) 500 yozuvli hisobot — 3 soniyadan tez bo'lsin
    t0 = time.perf_counter()
    bpdf, bpages = build_report_pdf_with_pages(_big_data())
    dt = time.perf_counter() - t0
    (OUT.parent / "report_test_big.pdf").write_bytes(bpdf)
    print(f"500 yozuv:    {bpages} sahifa, {dt:.2f}s "
          f"({'OK' if dt < 3 else 'SEKIN!'})")


if __name__ == "__main__":
    asyncio.run(main())
