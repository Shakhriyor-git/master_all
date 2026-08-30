"""Barcha foydalanuvchiga ko'rinadigan matnlar (o'zbekcha) va render funksiyalari.

parse_mode=HTML — foydalanuvchi kiritgan har qanday matn (obyekt nomi, mijoz
ismi, izoh, "boshqa" pozitsiya nomi) xabarga qo'yilishdan oldin html.escape()
qilinadi, aks holda "Uy <45>" kabi nom xabarni buzadi.
"""

import html
from collections.abc import Iterable
from decimal import Decimal

from app.bot.utils import fmt_date, fmt_money, fmt_qty, fmt_unit

# --- Reply tugma yozuvlari (handlerlar shu matn bo'yicha filtrlaydi) ---
BTN_MY_PROJECTS = "📋 Obyektlarim"
BTN_NEW_PROJECT = "➕ Yangi obyekt"
BTN_MY_PRICES = "💰 Narxlarim"
BTN_HELP = "❓ Yordam"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP = "⏭ O'tkazib yuborish"

# --- Umumiy ---
GREETING = (
    "Assalomu alaykum, <b>{name}</b>!\n\n"
    "Bu bot qurilish obyektlaringiz bo'yicha ish, material va to'lovlarni "
    "yuritishga yordam beradi.\n\n"
    "Quyidagi menyudan boshlang."
)
HELP = (
    "<b>Qanday ishlaydi</b>\n\n"
    "• <b>Yangi obyect</b> — obyekt (xonadon/uy) ochasiz\n"
    "• Obyekt kartasida <b>ish</b> va <b>material</b> qo'shasiz\n"
    "• <b>To'lov</b> — mijozdan olingan pulni qayd qilasiz\n"
    "• <b>Hisobot</b> — jami ishlar, material va mijoz qarzi\n"
    "• <b>Narxlarim</b> — shaxsiy narx katalogingiz\n\n"
    "Har qanday bosqichda /bekor deb yozsangiz — bosh menyuga qaytadi."
)
MENU_HINT = "Bosh menyu."
CANCELLED = "Bekor qilindi. Bosh menyu."
ERROR = "Xatolik yuz berdi, qaytadan urinib ko'ring."
NOTHING_HERE = "Hozircha bo'sh."

# --- Yangi obyekt ---
ASK_TITLE = "Obyekt nomini yozing (masalan: <i>Chilonzor 12-uy, 45-xonadon</i>):"
ASK_CLIENT = "Mijoz ismi? (yoki «{skip}»)".format(skip=BTN_SKIP)
PROJECT_CREATED = "Obyekt yaratildi."
IMPORT_OFFER = (
    "Narx katalogingizdan pozitsiyalarni shu obyektga nusxalaymizmi?\n"
    "Keyin obyektdagi narx katalogdan alohida bo'ladi — katalogni "
    "o'zgartirsangiz, bu obyekt hisobi o'zgarmaydi."
)
IMPORT_DONE = "{n} ta pozitsiya nusxalandi."
IMPORT_SKIPPED = "Yaxshi, keyinroq obyekt ichidan qo'shishingiz mumkin."

# --- Ish / material ---
ASK_PICK_WORK = "Qaysi ish? Ro'yxatdan tanlang yoki «➕ Boshqa ish»:"
ASK_PICK_MATERIAL = "Qaysi material? Ro'yxatdan tanlang yoki «➕ Boshqa material»:"
ASK_QUANTITY = "Miqdorini yozing ({unit}). Masalan: <code>11.5</code> yoki <code>11,5</code>"
BAD_QUANTITY = "Faqat raqam kiriting, masalan: 11.5"
ASK_NEW_NAME = "Yangi pozitsiya nomi?"
ASK_NEW_UNIT = "O'lchov birligi?"
ASK_NEW_PRICE = "Bir birlik narxi (so'm)? Masalan: <code>25000</code>"
BAD_PRICE = "Faqat raqam kiriting, masalan: 25000"
ASK_PAID_BY = "Bu materialni kim to'ladi?"
ENTRY_SAVED = "Saqlandi."

# --- To'lov ---
ASK_PAYMENT_AMOUNT = "To'lov summasi (so'm)? Masalan: <code>2000000</code>"
ASK_PAYMENT_METHOD = "To'lov usuli?"
PAYMENT_SAVED = "To'lov qayd qilindi."

# --- Narxlar ---
PRICES_TITLE = "<b>Narx katalogi</b>"
PRICES_EMPTY = "Katalog bo'sh. «➕ Qo'shish» orqali pozitsiya qo'shing."
PRICE_ADDED = "Qo'shildi."
PRICE_REMOVED = "O'chirildi."
PRICE_ITEM_LINE = "• {name} — {price} / {unit} ({kind})"
ASK_PI_NAME = "Pozitsiya nomi? (masalan: <i>Shpatlyovka</i>)"
ASK_PI_KIND = "Bu ish (work) mi yoki material?"
ASK_PI_UNIT = "O'lchov birligi?"
ASK_PI_PRICE = "Bir birlik narxi (so'm)?"

# --- Obyekt yopish ---
PROJECT_CLOSED = "Obyekt yopildi (bajarilgan)."

KIND_UZ = {"work": "ish", "material": "material"}


def esc(value: object) -> str:
    return html.escape(str(value)) if value is not None else ""


def render_project_card(project, summary) -> str:
    """Obyekt kartasi — summary xizmati natijasi bilan."""
    materials_total = (
        summary.materials_by_master + summary.materials_by_client
    )
    client = esc(project.client_name) if project.client_name else "—"
    return (
        f"🏠 <b>{esc(project.title)}</b>\n"
        f"Mijoz: {client}\n\n"
        f"Ishlar:      {fmt_money(summary.works_total)}\n"
        f"Material:    {fmt_money(materials_total)}\n"
        f"To'langan:   {fmt_money(summary.paid_total)}\n"
        f"─────────────────────\n"
        f"Qarz:        {fmt_money(summary.client_owes)}"
    )


def render_confirm_entry(name: str, qty: Decimal, unit: str, price: Decimal) -> str:
    total = (qty * price).quantize(Decimal("1"))
    return (
        f"{esc(name)} — {fmt_qty(qty)} {fmt_unit(unit)} × "
        f"{fmt_money(price)} = <b>{fmt_money(total)}</b>"
    )


def render_report(project, summary, recent: Iterable) -> str:
    lines = [
        f"📊 <b>{esc(project.title)}</b> — hisobot\n",
        f"Ishlar:             {fmt_money(summary.works_total)}",
        f"Material (meniki):   {fmt_money(summary.materials_by_master)}",
        f"Material (mijoz):    {fmt_money(summary.materials_by_client)}",
        f"To'langan:           {fmt_money(summary.paid_total)}",
        "─────────────────────",
        f"Mijoz qarzi:         {fmt_money(summary.client_owes)}\n",
        f"Yozuvlar: {summary.entries_count} ta",
        f"Oxirgi yozuv: {fmt_date(summary.last_entry_date)}",
    ]
    recent = list(recent)
    if recent:
        lines.append("\n<b>Oxirgi yozuvlar:</b>")
        for e in recent:
            lines.append(
                f"• {fmt_date(e.entry_date)} — {esc(e.name)} "
                f"{fmt_qty(e.quantity)} {fmt_unit(e.unit)} = {fmt_money(e.amount)}"
            )
    return "\n".join(lines)
