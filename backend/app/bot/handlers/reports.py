"""Hisobot — summary + oxirgi yozuvlar."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import repo, texts
from app.bot.keyboards import ProjectCb
from app.bot.views import send_project_card
from app.models import User
from app.services.summary import build_project_summary

router = Router(name="reports")


@router.callback_query(ProjectCb.filter(F.action == "report"))
async def show_report(
    callback: CallbackQuery,
    callback_data: ProjectCb,
    session: AsyncSession,
    user: User,
) -> None:
    project = await repo.get_owned_project(
        session, user.id, callback_data.project_id
    )
    if project is None:
        await callback.answer(texts.ERROR, show_alert=True)
        return

    summary = await build_project_summary(session, project.id)
    recent = await repo.recent_entries(session, project.id, limit=10)
    await callback.message.answer(texts.render_report(project, summary, recent))
    await send_project_card(callback.message, session, project)
    await callback.answer()
