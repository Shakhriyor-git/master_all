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
            # 2. Ish (brak) — 180 000, ish haqi qarziga kirmasligi kerak
            _entry(pid, uid, kind="work", name="Ish brak", unit="m2",
                   unit_price=Decimal("180000"), is_rework=True),
            # 3-4. Materiallar — 350 000 + 520 000 (paid_by listener'da 'client')
            _entry(pid, uid, kind="material", name="Mat 1", unit="qop",
                   unit_price=Decimal("350000"), payment_method="card"),
            _entry(pid, uid, kind="material", name="Mat 2", unit="qop",
                   unit_price=Decimal("520000"), payment_method="cash"),
            # 5-6. Xarajatlar — 120 000 + 120 000
            _entry(pid, uid, kind="expense", name="Ovqat", unit="summa",
                   unit_price=Decimal("120000"), payment_method="cash"),
            _entry(pid, uid, kind="expense", name="Transport", unit="summa",
                   unit_price=Decimal("120000"), payment_method="cash"),
        ]
        session.add_all(rows)
        session.add_all([
            Payment(project_id=pid, created_by_user_id=uid,
                    amount=Decimal("2000000"), purpose="labor"),
            # Eski 'material' to'lov — hech qanday hisobga KIRMASLIGI kerak
            Payment(project_id=pid, created_by_user_id=uid,
                    amount=Decimal("1000000"), purpose="material"),
        ])
        await session.commit()

        s = await build_project_summary(session, pid)

        checks: list[tuple[str, Decimal | int, Decimal | int]] = [
            # Ish haqi qarzi = 2 400 000 − 2 000 000 = 400 000
            # (purpose='material' to'lov 1 000 000 HISOBGA KIRMAYDI)
            ("labor.works_total", s.labor.works_total, Decimal("2400000.00")),
            ("labor.paid", s.labor.paid, Decimal("2000000.00")),
            ("labor.remaining", s.labor.remaining, Decimal("400000.00")),
            # Material — faqat jami, qarz yo'q
            ("materials.materials_total", s.materials.materials_total,
             Decimal("870000.00")),  # 350 000 + 520 000
            ("materials.expenses_total", s.materials.expenses_total,
             Decimal("240000.00")),  # 120 000 + 120 000
            ("materials.total_spent", s.materials.total_spent,
             Decimal("1110000.00")),
            ("meta.entries_count", s.meta.entries_count, 6),
        ]

        failures = [
            f"{name}: kutilgan {want}, olindi {got}"
            for name, got, want in checks
            if got != want
        ]

        # Brak (180 000) ish haqi qarziga kirmasligi kerak
        if s.labor.remaining != Decimal("400000.00"):
            failures.append(
                f"brak ish haqi qarziga kirib ketdi: {s.labor.remaining}"
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
    print("\nHammasi joyida: ish haqi qarzi=400 000, jami sarflangan=1 110 000.")
    print("Brak (180 000) va eski 'material' to'lov (1 000 000) HISOBGA KIRMADI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
