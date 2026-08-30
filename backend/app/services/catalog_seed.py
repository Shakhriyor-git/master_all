"""Yangi foydalanuvchi uchun standart katalog — endi faqat BIRLIKLAR.

09-vazifa: tayyor kategoriya/pozitsiya katalogi chalkashlik keltirdi
(45 ta narxsiz pozitsiya, ustaning nomlari bilan mos kelmaydi). Usta o'zi
kiritsin. Standart birliklar qoladi — ular umumiy va chalkashlik bermaydi.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MeasureUnit

# (code, label) — hammasi is_system=true.
SYSTEM_UNITS: list[tuple[str, str]] = [
    ("m2", "m²"),
    ("m3", "m³"),
    ("dona", "dona"),
    ("qop", "qop"),
    ("metr", "metr"),
    ("kg", "kg"),
    ("litr", "litr"),
    ("soat", "soat"),
    ("kunlik", "kunlik"),
    ("tochka", "tochka"),
    ("komplekt", "komplekt"),
    ("rulon", "rulon"),
    ("summa", "summa"),
]

# expense yozuvlari uchun majburiy birlik
EXPENSE_UNIT = "summa"

# Birlik tanlash ro'yxatida ko'rsatilmaydigan kodlar
HIDDEN_PICKER_UNITS = frozenset({"summa"})


async def seed_catalog_for_user(session: AsyncSession, user_id: int) -> None:
    """Standart birliklarni qo'shadi. Idempotent — dublikat yaratmaydi."""
    await _seed_units(session, user_id)
    await session.commit()


async def _seed_units(session: AsyncSession, user_id: int) -> None:
    have = set(
        (
            await session.execute(
                select(MeasureUnit.code).where(
                    MeasureUnit.user_id == user_id
                )
            )
        ).scalars().all()
    )
    for order, (code, label) in enumerate(SYSTEM_UNITS):
        if code in have:
            continue
        session.add(
            MeasureUnit(
                user_id=user_id,
                code=code,
                label=label,
                is_system=True,
                sort_order=order,
            )
        )
