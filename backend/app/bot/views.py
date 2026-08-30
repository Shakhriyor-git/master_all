"""Umumiy ko'rinishlar — bir nechta handler ishlatadi."""

from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import texts
from app.models import Project
from app.services.summary import build_project_summary


async def send_project_card(
    target: Message | CallbackQuery,
    session: AsyncSession,
    project: Project,
    *,
    edit: bool = False,
) -> None:
    """Obyekt kartasini yuboradi yoki mavjud xabarni yangilaydi."""
    summary = await build_project_summary(session, project.id)
    text = texts.render_project_card(project, summary)
    markup = kb.project_card_kb(project.id)

    message = target.message if isinstance(target, CallbackQuery) else target
    if edit and isinstance(target, CallbackQuery) and message is not None:
        await message.edit_text(text, reply_markup=markup)
    elif message is not None:
        await message.answer(text, reply_markup=markup)
