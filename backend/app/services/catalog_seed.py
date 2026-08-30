"""Yangi foydalanuvchi uchun standart katalog.

Birliklar + kategoriyalar + xizmat/material pozitsiyalari. **Narxlar 0** —
usta o'zi belgilaydi (taxminiy narx eskirsa mijoz bilan janjalga sabab bo'ladi).

Idempotent: `seed_catalog_for_user` bir necha marta chaqirilsa ham dublikat
yaratmaydi va ustaning o'zgartirgan narxlarini buzmaydi.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, MeasureUnit, PriceItem

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

# (icon, name, [(pozitsiya nomi, unit code), ...])
_CategoryDef = tuple[str, str, list[tuple[str, str]]]

WORK_CATEGORIES: list[_CategoryDef] = [
    ("🏠", "Shift", [
        ("Gipsokarton yopishtirish", "m2"),
        ("Gulli gipsokarton", "m2"),
        ("Shift shpatlyovka", "m2"),
        ("Shift emulsiya", "m2"),
        ("Natyajnoy potolok", "m2"),
    ]),
    ("🧱", "Devor", [
        ("Shtukaturka", "m2"),
        ("Shpatlyovka", "m2"),
        ("Bo'yash", "m2"),
        ("Oboy yopishtirish", "m2"),
        ("Dekorativ pardoz", "m2"),
    ]),
    ("⬜", "Pol", [
        ("Quyma pol (styajka)", "m2"),
        ("Laminat yotqizish", "m2"),
        ("Plintus o'rnatish", "metr"),
    ]),
    ("◻️", "Kafel", [
        ("Devorga kafel", "m2"),
        ("Polga kafel", "m2"),
        ("Zatirka", "m2"),
    ]),
    ("⚡", "Elektrika", [
        ("Tochka (rozetka/vklyuchatel)", "tochka"),
        ("Shtroba ochish", "metr"),
        ("Sim tortish", "metr"),
        ("Karobka bog'lash", "dona"),
        ("Lyustra o'rnatish", "dona"),
        ("Shitok yig'ish", "dona"),
    ]),
    ("🚿", "Santexnika", [
        ("Unitaz o'rnatish", "dona"),
        ("Rakovina o'rnatish", "dona"),
        ("Dush kabina", "dona"),
        ("Quvur tortish", "metr"),
        ("Radiator o'rnatish", "dona"),
    ]),
    ("🔨", "Demontaj", [
        ("Devor buzish", "m2"),
        ("Eski kafel ko'chirish", "m2"),
        ("Chiqindi chiqarish", "kunlik"),
    ]),
    ("📋", "Umumiy", [
        ("Kunlik ish", "kunlik"),
        ("Yordamchi ishchi", "kunlik"),
    ]),
]

MATERIAL_CATEGORIES: list[_CategoryDef] = [
    ("🪣", "Aralashmalar", [
        ("Sement", "qop"),
        ("Gips", "qop"),
        ("Shpatlyovka", "qop"),
        ("Grunt", "litr"),
        ("Qum", "m3"),
    ]),
    ("◻️", "Kafel mollari", [
        ("Kafel", "m2"),
        ("Yopishtiruvchi", "qop"),
        ("Zatirka", "kg"),
        ("Krestik", "komplekt"),
    ]),
    ("⚡", "Elektr mollari", [
        ("Sim", "metr"),
        ("Rozetka", "dona"),
        ("Vklyuchatel", "dona"),
        ("Karobka", "dona"),
        ("Avtomat", "dona"),
    ]),
    ("🚿", "Santexnika mollari", [
        ("Quvur", "metr"),
        ("Kran", "dona"),
        ("Fitting", "dona"),
    ]),
    ("🎨", "Bo'yoq", [
        ("Emulsiya", "litr"),
        ("Bo'yoq", "litr"),
        ("Valik", "dona"),
    ]),
]


async def seed_catalog_for_user(session: AsyncSession, user_id: int) -> None:
    """Standart birliklar va katalogni qo'shadi. Idempotent."""
    await _seed_units(session, user_id)
    await _seed_categories(session, user_id, "work", WORK_CATEGORIES)
    await _seed_categories(session, user_id, "material", MATERIAL_CATEGORIES)
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


async def _seed_categories(
    session: AsyncSession,
    user_id: int,
    kind: str,
    groups: list[_CategoryDef],
) -> None:
    existing_cats = {
        c.name: c
        for c in (
            await session.execute(
                select(Category).where(
                    Category.user_id == user_id, Category.kind == kind
                )
            )
        ).scalars().all()
    }
    have_items = set(
        (
            await session.execute(
                select(PriceItem.name).where(
                    PriceItem.user_id == user_id, PriceItem.kind == kind
                )
            )
        ).scalars().all()
    )

    for cat_order, (icon, name, items) in enumerate(groups):
        category = existing_cats.get(name)
        if category is None:
            category = Category(
                user_id=user_id,
                name=name,
                kind=kind,
                icon=icon,
                sort_order=cat_order,
            )
            session.add(category)

        for item_name, unit_code in items:
            if item_name in have_items:
                continue
            session.add(
                PriceItem(
                    user_id=user_id,
                    category=category,
                    name=item_name,
                    kind=kind,
                    unit=unit_code,
                    default_price=Decimal("0"),
                )
            )
