"""Obyektlar — yaratish, ro'yxat, karta, yopish, katalogdan nusxa."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import repo, texts
from app.bot.keyboards import ImportCb, PageCb, ProjectCb
from app.bot.states import NewProject
from app.bot.utils import paginate
from app.bot.views import send_project_card
from app.models import Project, User
from app.models.enums import ProjectStatus

router = Router(name="projects")


# --------------------------------------------------------------------------
# Yangi obyekt
# --------------------------------------------------------------------------
@router.message(F.text == texts.BTN_NEW_PROJECT)
async def new_project_start(message: Message, state: FSMContext) -> None:
    await state.set_state(NewProject.title)
    await message.answer(texts.ASK_TITLE, reply_markup=kb.cancel_kb())


@router.message(NewProject.title, F.text)
async def new_project_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer(texts.ASK_TITLE)
        return
    await state.update_data(title=title[:200])
    await state.set_state(NewProject.client_name)
    await message.answer(texts.ASK_CLIENT, reply_markup=kb.skip_cancel_kb())


@router.message(NewProject.client_name, F.text)
async def new_project_client(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    client = None if message.text == texts.BTN_SKIP else message.text.strip()[:200]
    data = await state.get_data()
    await state.clear()

    project = Project(
        user_id=user.id, title=data["title"], client_name=client or None
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    await message.answer(texts.PROJECT_CREATED, reply_markup=kb.main_menu())

    if await repo.catalog_items(session, user.id):
        await message.answer(
            texts.IMPORT_OFFER, reply_markup=kb.import_offer_kb(project.id)
        )
    else:
        await send_project_card(message, session, project)


@router.callback_query(ImportCb.filter())
async def import_choice(
    callback: CallbackQuery,
    callback_data: ImportCb,
    session: AsyncSession,
    user: User,
) -> None:
    project = await repo.get_owned_project(
        session, user.id, callback_data.project_id
    )
    if project is None:
        await callback.answer(texts.ERROR, show_alert=True)
        return

    if callback_data.yes:
        n = await repo.copy_catalog_to_project(session, user.id, project.id)
        await callback.message.edit_text(texts.IMPORT_DONE.format(n=n))
    else:
        await callback.message.edit_text(texts.IMPORT_SKIPPED)

    await send_project_card(callback, session, project)
    await callback.answer()


# --------------------------------------------------------------------------
# Obyektlar ro'yxati va karta
# --------------------------------------------------------------------------
async def _show_list(
    target: Message | CallbackQuery,
    session: AsyncSession,
    user: User,
    page: int,
) -> None:
    projects = await repo.list_active_projects(session, user.id)
    if not projects:
        text = texts.NOTHING_HERE
        markup = None
    else:
        chunk, page, total = paginate(projects, page)
        text = texts.BTN_MY_PROJECTS
        markup = kb.projects_list_kb(chunk, page, total)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(F.text == texts.BTN_MY_PROJECTS)
async def my_projects(
    message: Message, session: AsyncSession, user: User
) -> None:
    await _show_list(message, session, user, 1)


@router.callback_query(PageCb.filter(F.scope == "projects"))
async def projects_page(
    callback: CallbackQuery,
    callback_data: PageCb,
    session: AsyncSession,
    user: User,
) -> None:
    await _show_list(callback, session, user, callback_data.page)


@router.callback_query(ProjectCb.filter(F.action == "open"))
async def open_project(
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
    await send_project_card(callback, session, project, edit=True)
    await callback.answer()


@router.callback_query(ProjectCb.filter(F.action == "list"))
async def back_to_list(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    await _show_list(callback, session, user, 1)


@router.callback_query(ProjectCb.filter(F.action == "close"))
async def close_project(
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
    project.status = ProjectStatus.COMPLETED
    await session.commit()
    await callback.answer(texts.PROJECT_CLOSED, show_alert=True)
    await send_project_card(callback, session, project, edit=True)
