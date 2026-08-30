"""Klaviatura yasovchilar va callback_data factory'lari.

Mini App bor — bot faqat: obyektlar ro'yxati (o'qish), yangi obyekt, yordam.
Har bir obyekt kartasida `web_app` tugmasi ilovaga olib boradi.
"""

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.bot import texts
from app.core.config import settings


# --------------------------------------------------------------------------
# callback_data
# --------------------------------------------------------------------------
class ProjectCb(CallbackData, prefix="prj"):
    # open | list
    action: str
    project_id: int


class PageCb(CallbackData, prefix="pg"):
    scope: str  # projects
    page: int
    project_id: int = 0
    kind: str = ""


# --------------------------------------------------------------------------
# Reply klaviaturalar
# --------------------------------------------------------------------------
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=texts.BTN_MY_PROJECTS)
    kb.button(text=texts.BTN_NEW_PROJECT)
    kb.button(text=texts.BTN_HELP)
    kb.adjust(2, 1)
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
def _nav_row(
    kb: InlineKeyboardBuilder, scope: str, page: int, total: int, **extra
) -> None:
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


def projects_list_kb(
    projects: Sequence, page: int, total: int
) -> InlineKeyboardMarkup:
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


def _open_app_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="📱 Ilovada ochish",
        web_app=WebAppInfo(url=settings.webapp_url),
    )


def project_card_kb(project_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_open_app_button())
    kb.row(
        InlineKeyboardButton(
            text="📄 Hisobot (PDF)",
            callback_data=ProjectCb(
                action="report", project_id=project_id
            ).pack(),
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="⬅️ Ro'yxatga",
            callback_data=ProjectCb(action="list", project_id=project_id).pack(),
        )
    )
    return kb.as_markup()


def open_app_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_open_app_button())
    return kb.as_markup()
