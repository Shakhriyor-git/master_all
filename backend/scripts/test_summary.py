"""summary xizmatining ssenariy testi (05-vazifa, A bosqich).

Alohida test usta + loyiha yaratadi, 8 ta yozuv/to'lov qo'yadi, natijani
tekshiradi va o'zidan keyin tozalaydi.

Ishga tushirish:  docker compose exec api python scripts/test_summary.py
"""

import asyncio
import pathlib
import sys
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import Entry, Payment, Project, User  # noqa: E402
from app.services.summary import build_project_summary  # noqa: E402

TG_ID = 999_111_222


def _entry(project_id: int, user_id: int, **kw) -> Entry:
    base = {
        "project_id": project_id,
        "created_by_user_id": user_id,
        "quantity": Decimal("1"),
        "name": kw.pop("name", "test"),
        "unit": kw.pop("unit", "dona"),
    }
    return Entry(**base, **kw)


async def _cleanup(session: AsyncSession) -> None:
    user = (
        await session.execute(select(User).where(User.telegram_id == TG_ID))
    ).scalar_one_or_none()
    if user is not None:
        # projects CASCADE -> entries/payments ham o'chadi
        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()


async def main() -> int:
    async with SessionLocal() as session:
        await _cleanup(session)

        user = User(telegram_id=TG_ID, full_name="Summary Test")
        session.add(user)
        await session.flush()

        project = Project(user_id=user.id, title="Summary test obyekti")
        session.add(project)
        await session.flush()

        pid, uid = project.id, user.id
        rows = [
            # 1. Ish (oddiy) — 2 400 000
            _entry(pid, uid, kind="work", name="Ish A", unit="m2",
                   unit_price=Decimal("2400000")),
            # 2. Ish (brak) — 180 000, qarzga kirmasligi kerak
            _entry(pid, uid, kind="work", name="Ish brak", unit="m2",
                   unit_price=Decimal("180000"), is_rework=True),
            # 3. Material, usta puliga, karta — 350 000
            _entry(pid, uid, kind="material", name="Mat usta", unit="qop",
                   unit_price=Decimal("350000"), paid_by="master",
                   payment_method="card"),
            # 4. Material, mijoz puliga, naqd — 520 000
            _entry(pid, uid, kind="material", name="Mat mijoz", unit="qop",
                   unit_price=Decimal("520000"), paid_by="client",
                   payment_method="cash"),
            # 5. Xarajat (ovqat), usta puliga — 120 000, qarzga kirmasligi kerak
            _entry(pid, uid, kind="expense", name="Ovqat", unit="summa",
                   unit_price=Decimal("120000"), paid_by="master",
                   payment_method="cash"),
            # 6. Xarajat (transport), mijoz puliga — 120 000
            _entry(pid, uid, kind="expense", name="Transport", unit="summa",
                   unit_price=Decimal("120000"), paid_by="client",
                   payment_method="cash"),
        ]
        session.add_all(rows)
        session.add_all([
            Payment(project_id=pid, created_by_user_id=uid,
                    amount=Decimal("2000000"), purpose="labor"),
            Payment(project_id=pid, created_by_user_id=uid,
                    amount=Decimal("1000000"), purpose="budget"),
        ])
        await session.commit()

        s = await build_project_summary(session, pid)

        checks: list[tuple[str, Decimal | int, Decimal | int]] = [
            ("labor.works_total", s.labor.works_total, Decimal("2400000.00")),
            ("labor.rework_total", s.labor.rework_total, Decimal("180000.00")),
            ("labor.materials_by_master", s.labor.materials_by_master,
             Decimal("350000.00")),
            ("labor.expenses_by_master", s.labor.expenses_by_master,
             Decimal("120000.00")),
            ("labor.paid_labor", s.labor.paid_labor, Decimal("2000000.00")),
            ("labor.client_owes", s.labor.client_owes, Decimal("750000.00")),
            ("budget.given", s.budget.given, Decimal("1000000.00")),
            ("budget.spent_materials", s.budget.spent_materials,
             Decimal("520000.00")),
            ("budget.spent_expenses", s.budget.spent_expenses,
             Decimal("120000.00")),
            ("budget.spent_total", s.budget.spent_total, Decimal("640000.00")),
            ("budget.balance", s.budget.balance, Decimal("360000.00")),
            ("meta.entries_count", s.meta.entries_count, 6),
        ]

        failures = [
            f"{name}: kutilgan {want}, olindi {got}"
            for name, got, want in checks
            if got != want
        ]

        # Brak va ustaning ovqati qarzga kirmasligi — alohida
        owes_without_specials = (
            s.labor.works_total + s.labor.materials_by_master
            - s.labor.paid_labor
        )
        if owes_without_specials != Decimal("750000.00"):
            failures.append(
                "brak/ovqat qarzga kirib ketdi: "
                f"{owes_without_specials}"
            )

        await _cleanup(session)

    for name, got, want in checks:
        mark = "OK  " if got == want else "FAIL"
        print(f"{mark} {name} = {got}")

    if failures:
        print("\nFAIL:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("\nHammasi joyida: client_owes=750 000, budget.balance=360 000.")
    print("Brak (180 000) va ustaning ovqati (120 000) qarzga KIRMADI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
