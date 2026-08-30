"""Xato kiritilgan narxlarni topish (o'chirmaydi, faqat ro'yxatlaydi).

So'mda 1000 dan arzon ish/material amalda yo'q — 0 < qiymat < 1000 bo'lganlar
ehtimol "20,000" o'rniga "20" kabi xato kiritilgan.

Ishga tushirish:  docker compose exec api python scripts/find_suspicious_prices.py
"""

import asyncio
import pathlib
import sys
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import Entry, PriceItem, Project, ProjectPrice, User  # noqa: E402

LO = Decimal("0")
HI = Decimal("1000")


async def main() -> int:
    async with SessionLocal() as s:
        pi_rows = (
            await s.execute(
                select(
                    PriceItem.id,
                    PriceItem.name,
                    PriceItem.kind,
                    PriceItem.unit,
                    PriceItem.default_price,
                    User.telegram_id,
                )
                .join(User, User.id == PriceItem.user_id)
                .where(
                    PriceItem.default_price > LO,
                    PriceItem.default_price < HI,
                )
                .order_by(PriceItem.default_price)
            )
        ).all()

        pp_rows = (
            await s.execute(
                select(
                    ProjectPrice.id,
                    ProjectPrice.name,
                    ProjectPrice.kind,
                    ProjectPrice.unit,
                    ProjectPrice.price,
                    Project.title,
                )
                .join(Project, Project.id == ProjectPrice.project_id)
                .where(ProjectPrice.price > LO, ProjectPrice.price < HI)
                .order_by(ProjectPrice.price)
            )
        ).all()

        entry_rows = (
            await s.execute(
                select(
                    Entry.id,
                    Entry.name,
                    Entry.kind,
                    Entry.unit,
                    Entry.unit_price,
                    Entry.entry_date,
                    Project.title,
                )
                .join(Project, Project.id == Entry.project_id)
                .where(
                    Entry.deleted_at.is_(None),
                    Entry.unit_price > LO,
                    Entry.unit_price < HI,
                )
                .order_by(Entry.unit_price)
            )
        ).all()

    print(f"=== price_items (0 < default_price < {HI}) — {len(pi_rows)} ta ===")
    for pid, name, kind, unit, price, tg in pi_rows:
        print(f"  #{pid:<5} {price:>8} / {unit:<8} {kind:<8} {name}  (usta tg={tg})")

    print(f"\n=== project_prices (0 < price < {HI}) — {len(pp_rows)} ta ===")
    for ppid, name, kind, unit, price, title in pp_rows:
        print(f"  #{ppid:<5} {price:>8} / {unit:<8} {kind:<8} {name}  (obyekt: {title})")

    print(f"\n=== entries (0 < unit_price < {HI}) — {len(entry_rows)} ta ===")
    for eid, name, kind, unit, price, edate, title in entry_rows:
        print(
            f"  #{eid:<5} {price:>8} / {unit:<8} {kind:<8} {edate} "
            f"{name}  (obyekt: {title})"
        )

    total = len(pi_rows) + len(pp_rows) + len(entry_rows)
    print(f"\nJami shubhali: {total} ta. Hech narsa o'chirilmadi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
