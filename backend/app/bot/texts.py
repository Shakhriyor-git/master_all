"""Barcha foydalanuvchiga ko'rinadigan matnlar (o'zbekcha) va render funksiyalari.

Mini App bor — bot faqat: salomlashish, obyektlar ro'yxati (o'qish uchun),
yangi obyekt, yordam. parse_mode=HTML bo'lgani uchun foydalanuvchi kiritgan
matn (obyekt nomi, mijoz ismi) esc() bilan qochiriladi.
"""

import html
from decimal import Decimal

from app.bot.utils import fmt_money

# --- Reply tugma yozuvlari (handlerlar shu matn bo'yicha filtrlaydi) ---
BTN_MY_PROJECTS = "📋 Obyektlarim"
BTN_NEW_PROJECT = "➕ Yangi obyekt"
BTN_HELP = "❓ Yordam"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP = "⏭ O'tkazib yuborish"
BTN_SEND_PHONE = "📱 Raqamni yuborish"
BTN_LATER = "Keyinroq"

# --- Tanishuv ---
ASK_PHONE = (
    "Telefon raqamingizni yuboring — hisobotlarda va PDF da ko'rsatiladi.\n\n"
    "«📱 Raqamni yuborish» tugmasini bosing yoki «Keyinroq»."
)
PHONE_SAVED = "Rahmat! Raqam saqlandi."

# --- Umumiy ---
GREETING = (
    "Assalomu alaykum, <b>{name}</b>!\n\n"
    "Bu bot orqali obyektlaringizni ko'rasiz va yangisini ochasiz. "
    "Kundalik ish — ish, material, xarajat, to'lov — ilovada bo'ladi."
)
OPEN_APP_HINT = "Ishni boshlash uchun ilovani oching:"
HELP = (
    "<b>Qanday ishlaydi</b>\n\n"
    "• <b>Obyektlarim</b> — obyektlar ro'yxati va qisqa hisob\n"
    "• <b>Yangi obyekt</b> — obyekt (xonadon/uy) ochasiz\n"
    "• Qolgan hamma narsa — ish, material, xarajat, to'lov, narxlar, "
    "qaydlar — <b>ilovada</b>\n\n"
    "Har qanday bosqichda /bekor deb yozsangiz — bosh menyuga qaytadi."
)
CANCELLED = "Bekor qilindi. Bosh menyu."
ERROR = "Xatolik yuz berdi, qaytadan urinib ko'ring."
NOTHING_HERE = "Hozircha bo'sh. «➕ Yangi obyekt» orqali boshlang."

# --- Yangi obyekt ---
ASK_TITLE = (
    "Obyekt nomini yozing "
    "(masalan: <i>Chilonzor 12-uy, 45-xonadon</i>):"
)
ASK_CLIENT = "Mijoz ismi? (yoki «{skip}»)".format(skip=BTN_SKIP)
PROJECT_CREATED = "Obyekt yaratildi."


def esc(value: object) -> str:
    return html.escape(str(value)) if value is not None else ""


def render_owes_line(remaining: Decimal) -> str:
    """Ish haqi qoldig'i. Manfiy bo'lsa — mijoz avansi."""
    if remaining > 0:
        return f"Mijoz qarzi:   {fmt_money(remaining)}"
    if remaining < 0:
        return f"Mijoz avansi:  {fmt_money(-remaining)}"
    return "Hisob-kitob teng"


def render_project_card(project, summary) -> str:
    """Obyekt kartasi — faqat o'qish uchun. Tafsilotlar ilovada."""
    labor = summary.labor
    mat = summary.materials
    client = esc(project.client_name) if project.client_name else "—"
    lines = [
        f"🏠 <b>{esc(project.title)}</b>",
        f"Mijoz: {client}",
        "",
        "<b>Ish haqi</b>",
        f"Bajarilgan:    {fmt_money(labor.works_total)}",
        f"To'langan:     {fmt_money(labor.paid)}",
        "─────────────────────",
        render_owes_line(labor.remaining),
        "",
        "<b>Material va xarajat</b>",
        f"Sarflangan:    {fmt_money(mat.total_spent)}",
    ]
    return "\n".join(lines)
