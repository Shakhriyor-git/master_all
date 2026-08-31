"""/start, /bekor, Yordam, bosh menyu, telefon tanishuvi."""

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import texts
from app.models import User

router = Router(name="start")


async def _after_start(message: Message, user: User) -> None:
    if not user.phone:
        # Har /start da qayta so'raydi, lekin majburlamaydi
        await message.answer(texts.ASK_PHONE, reply_markup=kb.contact_kb())
    else:
        await message.answer(
            texts.OPEN_APP_HINT, reply_markup=kb.open_app_kb()
        )


@router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext, user: User) -> None:
    await state.clear()
    await message.answer(
        texts.GREETING.format(name=texts.esc(user.full_name)),
        reply_markup=kb.main_menu(),
    )
    await _after_start(message, user)


@router.message(F.contact)
async def got_contact(
    message: Message, session: AsyncSession, user: User
) -> None:
    contact = message.contact
    own_id = message.from_user.id if message.from_user else None
    if contact is None or (
        contact.user_id is not None and contact.user_id != own_id
    ):
        await message.answer(texts.ASK_PHONE, reply_markup=kb.contact_kb())
        return
    user.phone = (contact.phone_number or "")[:32] or None
    user.onboarded = True
    await session.commit()
    await message.answer(texts.PHONE_SAVED, reply_markup=kb.main_menu())
    await message.answer(texts.OPEN_APP_HINT, reply_markup=kb.open_app_kb())


@router.message(F.text == texts.BTN_LATER)
async def later(message: Message) -> None:
    await message.answer(
        texts.OPEN_APP_HINT, reply_markup=kb.main_menu()
    )
    await message.answer(texts.OPEN_APP_HINT, reply_markup=kb.open_app_kb())


@router.message(Command("bekor"), StateFilter("*"))
@router.message(F.text == texts.BTN_CANCEL, StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.CANCELLED, reply_markup=kb.main_menu())


@router.message(Command("yordam"))
@router.message(F.text == texts.BTN_HELP)
async def show_help(message: Message) -> None:
    await message.answer(texts.HELP, reply_markup=kb.open_app_kb())


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
