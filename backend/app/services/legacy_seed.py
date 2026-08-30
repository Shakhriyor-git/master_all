"""Eski standart katalog — FAQAT bir martalik tozalash uchun.

09-vazifa: yangi foydalanuvchi bo'sh katalog bilan boshlaydi (`catalog_seed.py`
endi faqat birliklarni seed qiladi). Bu modul eski seed nomlarini saqlaydi,
`DELETE /api/price-items/seeded` va `DELETE /api/categories/seeded` shu nomlar
bo'yicha ishlatilmagan seed yozuvlarini topib o'chiradi.
"""

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

_ALL = WORK_CATEGORIES + MATERIAL_CATEGORIES

SEED_CATEGORY_NAMES: frozenset[str] = frozenset(name for _, name, _ in _ALL)
SEED_ITEM_NAMES: frozenset[str] = frozenset(
    item_name for _, _, items in _ALL for item_name, _ in items
)
