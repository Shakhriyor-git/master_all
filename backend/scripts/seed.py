"""Test uchun boshlang'ich ma'lumot.

Idempotent — qayta ishga tushirilsa dublikat yaratmaydi.
Ishga tushirish:  docker compose exec api python scripts/seed.py
"""

import asyncio
import datetime
import pathlib
import sys
from decimal import Decimal

# "python scripts/seed.py" da /code sys.path da bo'lmaydi — qo'shib qo'yamiz.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Entry,
    Payment,
    PriceItem,
    Project,
    ProjectPrice,
    User,
)
from app.models.enums import (  # noqa: E402
    EntryKind,
    PaidBy,
    PaymentMethod,
    ProjectStatus,
    Unit,
)

# Test usta — Telegram ID int32 dan katta, konfliktdan xoli
TEST_TELEGRAM_ID = 999_000_001
TEST_PROJECT_TITLE = "Chilonzor 12-uy, 45-xonadon"

# (nom, tur, birlik, narx)
CATALOG: list[tuple[str, EntryKind, Unit, Decimal]] = [
    ("Shpatlyovka", EntryKind.WORK, Unit.M2, Decimal("25000")),
    ("Plitka yotqizish", EntryKind.WORK, Unit.M2, Decimal("60000")),
    ("Bo'yash", EntryKind.WORK, Unit.M2, Decimal("18000")),
    ("Sement", EntryKind.MATERIAL, Unit.QOP, Decimal("45000")),
    ("Gips", EntryKind.MATERIAL, Unit.QOP, Decimal("38000")),
    ("Quyma pol", EntryKind.WORK, Unit.M2, Decimal("55000")),
]

# Loyihaga nusxalanadigan pozitsiyalar
PROJECT_PRICE_NAMES = ["Shpatlyovka", "Plitka yotqizish", "Sement"]

# (narx nomi, miqdor, sana, kim to'ladi)
ENTRIES_SPEC: list[tuple[str, Decimal, datetime.date, PaidBy]] = [
    ("Shpatlyovka", Decimal("40"), datetime.date(2026, 8, 10), PaidBy.MASTER),
    ("Plitka yotqizish", Decimal("18"), datetime.date(2026, 8, 15), PaidBy.MASTER),
    ("Sement", Decimal("12"), datetime.date(2026, 8, 16), PaidBy.CLIENT),
]


async def get_or_create[T](
    session: AsyncSession,
    model: type[T],
    defaults: dict | None = None,
    **keys: object,
) -> tuple[T, bool]:
    """Kalitlar bo'yicha qidiradi, topilmasa yaratadi."""
    result = await session.execute(select(model).filter_by(**keys))
    obj = result.scalar_one_or_none()
    if obj is not None:
        return obj, False
    obj = model(**{**keys, **(defaults or {})})
    session.add(obj)
    await session.flush()
    return obj, True


async def main() -> None:
    async with SessionLocal() as session:
        user, _ = await get_or_create(
            session,
            User,
            telegram_id=TEST_TELEGRAM_ID,
            defaults={
                "full_name": "Test Usta",
                "username": "test_usta",
                "phone": "+998900000000",
            },
        )

        project, _ = await get_or_create(
            session,
            Project,
            user_id=user.id,
            title=TEST_PROJECT_TITLE,
            defaults={
                "address": "Toshkent, Chilonzor 12",
                "client_name": "Aziz aka",
                "client_phone": "+998901234567",
                "status": ProjectStatus.ACTIVE,
                "started_at": datetime.date(2026, 8, 1),
            },
        )

        price_items: dict[str, PriceItem] = {}
        for name, kind, unit, price in CATALOG:
            item, _ = await get_or_create(
                session,
                PriceItem,
                user_id=user.id,
                name=name,
                kind=kind,
                defaults={"unit": unit, "default_price": price},
            )
            price_items[name] = item

        project_prices: dict[str, ProjectPrice] = {}
        for name in PROJECT_PRICE_NAMES:
            item = price_items[name]
            pp, _ = await get_or_create(
                session,
                ProjectPrice,
                project_id=project.id,
                name=item.name,
                kind=item.kind,
                defaults={
                    "price_item_id": item.id,
                    "unit": item.unit,
                    "price": item.default_price,
                },
            )
            project_prices[name] = pp

        for name, quantity, entry_date, paid_by in ENTRIES_SPEC:
            pp = project_prices[name]
            await get_or_create(
                session,
                Entry,
                project_id=project.id,
                project_price_id=pp.id,
                entry_date=entry_date,
                defaults={
                    "created_by_user_id": user.id,
                    "kind": pp.kind,
                    "name": pp.name,
                    "unit": pp.unit,
                    "quantity": quantity,
                    "unit_price": pp.price,
                    "paid_by": paid_by,
                },
            )

        await get_or_create(
            session,
            Payment,
            project_id=project.id,
            amount=Decimal("2000000"),
            paid_at=datetime.date(2026, 8, 20),
            defaults={
                "created_by_user_id": user.id,
                "method": PaymentMethod.CASH,
            },
        )

        await session.commit()

    print("Seed tayyor: 1 usta, 1 loyiha, "
          f"{len(CATALOG)} narx, {len(ENTRIES_SPEC)} yozuv, 1 to'lov.")


if __name__ == "__main__":
    asyncio.run(main())
