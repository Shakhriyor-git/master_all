"""Klaviatura yasovchilar va callback_data factory'lari."""

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.bot import texts
from app.models.enums import Unit


# --------------------------------------------------------------------------
# callback_data
# --------------------------------------------------------------------------
class ProjectCb(CallbackData, prefix="prj"):
    action: str  # open | work | material | payment | report | prices | close | list
    project_id: int


class PageCb(CallbackData, prefix="pg"):
    scope: str  # projects | catalog | pick
    page: int
    project_id: int = 0
    kind: str = ""


class PickPriceCb(CallbackData, prefix="pp"):
    project_id: int
    price_id: int  # 0 => "boshqa"
    kind: str


class UnitCb(CallbackData, prefix="unit"):
    value: str


class KindCb(CallbackData, prefix="kind"):
    value: str  # work | material


class PaidByCb(CallbackData, prefix="pb"):
    value: str


class MethodCb(CallbackData, prefix="pm"):
    value: str


class ConfirmCb(CallbackData, prefix="cf"):
    ok: int


class CatalogCb(CallbackData, prefix="cat"):
    action: str  # add | del
    item_id: int = 0


class ImportCb(CallbackData, prefix="imp"):
    project_id: int
    yes: int


# --------------------------------------------------------------------------
# Reply klaviaturalar
# --------------------------------------------------------------------------
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=texts.BTN_MY_PROJECTS)
    kb.button(text=texts.BTN_NEW_PROJECT)
    kb.button(text=texts.BTN_MY_PRICES)
    kb.button(text=texts.BTN_HELP)
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=texts.BTN_CANCEL)
    return kb.as_markup(resize_keyboard=True)


def skip_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=texts.BTN_SKIP)
    kb.button(text=texts.BTN_CANCEL)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# --------------------------------------------------------------------------
# Inline klaviaturalar
# --------------------------------------------------------------------------
def _nav_row(kb: InlineKeyboardBuilder, scope: str, page: int, total: int, **extra) -> None:
    if total <= 1:
        return
    kb.row(
        InlineKeyboardButton(
            text="◀️" if page > 1 else "·",
            callback_data=PageCb(
                scope=scope, page=max(1, page - 1), **extra
            ).pack(),
        ),
        InlineKeyboardButton(text=f"{page}/{total}", callback_data="noop"),
        InlineKeyboardButton(
            text="▶️" if page < total else "·",
            callback_data=PageCb(
                scope=scope, page=min(total, page + 1), **extra
            ).pack(),
        ),
    )


def projects_list_kb(projects: Sequence, page: int, total: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in projects:
        kb.row(
            InlineKeyboardButton(
                text=f"🏠 {p.title}"[:60],
                callback_data=ProjectCb(action="open", project_id=p.id).pack(),
            )
        )
    _nav_row(kb, "projects", page, total)
    return kb.as_markup()


def project_card_kb(project_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    a = {"project_id": project_id}
    kb.button(text="🔨 Ish qo'shish", callback_data=ProjectCb(action="work", **a))
    kb.button(text="🧱 Material", callback_data=ProjectCb(action="material", **a))
    kb.button(text="💵 To'lov", callback_data=ProjectCb(action="payment", **a))
    kb.button(text="📊 Hisobot", callback_data=ProjectCb(action="report", **a))
    kb.button(text="⚙️ Narxlar", callback_data=ProjectCb(action="prices", **a))
    kb.button(text="✅ Yopish", callback_data=ProjectCb(action="close", **a))
    kb.button(text="⬅️ Ro'yxatga", callback_data=ProjectCb(action="list", **a))
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def price_pick_kb(
    prices: Sequence, project_id: int, kind: str, page: int, total: int
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for pr in prices:
        kb.row(
            InlineKeyboardButton(
                text=f"{pr.name} · {pr.price:g}"[:60],
                callback_data=PickPriceCb(
                    project_id=project_id, price_id=pr.id, kind=kind
                ).pack(),
            )
        )
    label = "➕ Boshqa ish" if kind == "work" else "➕ Boshqa material"
    kb.row(
        InlineKeyboardButton(
            text=label,
            callback_data=PickPriceCb(
                project_id=project_id, price_id=0, kind=kind
            ).pack(),
        )
    )
    _nav_row(kb, "pick", page, total, project_id=project_id, kind=kind)
    return kb.as_markup()


def unit_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in Unit:
        kb.button(text=u.value, callback_data=UnitCb(value=u.value))
    kb.adjust(4)
    return kb.as_markup()


def paid_by_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Men to'ladim", callback_data=PaidByCb(value="master"))
    kb.button(text="Mijoz to'ladi", callback_data=PaidByCb(value="client"))
    kb.adjust(2)
    return kb.as_markup()


def method_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Naqd", callback_data=MethodCb(value="cash"))
    kb.button(text="Karta", callback_data=MethodCb(value="card"))
    kb.button(text="O'tkazma", callback_data=MethodCb(value="transfer"))
    kb.adjust(3)
    return kb.as_markup()


def kind_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Ish", callback_data=KindCb(value="work"))
    kb.button(text="Material", callback_data=KindCb(value="material"))
    kb.adjust(2)
    return kb.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Saqlash", callback_data=ConfirmCb(ok=1))
    kb.button(text="❌ Bekor", callback_data=ConfirmCb(ok=0))
    kb.adjust(2)
    return kb.as_markup()


def catalog_kb(items: Sequence, page: int, total: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for it in items:
        kb.row(
            InlineKeyboardButton(
                text=f"🗑 {it.name} ({it.kind})"[:60],
                callback_data=CatalogCb(action="del", item_id=it.id).pack(),
            )
        )
    kb.row(
        InlineKeyboardButton(
            text="➕ Qo'shish", callback_data=CatalogCb(action="add").pack()
        )
    )
    _nav_row(kb, "catalog", page, total)
    return kb.as_markup()


def import_offer_kb(project_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📋 Katalogdan nusxalash",
        callback_data=ImportCb(project_id=project_id, yes=1),
    )
    kb.button(
        text="Keyinroq",
        callback_data=ImportCb(project_id=project_id, yes=0),
    )
    kb.adjust(1, 1)
    return kb.as_markup()
