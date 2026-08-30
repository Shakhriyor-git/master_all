"""/start, /bekor, Yordam, bosh menyu."""

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import keyboards as kb
from app.bot import texts
from app.models import User

router = Router(name="start")


@router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext, user: User) -> None:
    await state.clear()
    await message.answer(
        texts.GREETING.format(name=texts.esc(user.full_name)),
        reply_markup=kb.main_menu(),
    )


@router.message(Command("bekor"), StateFilter("*"))
@router.message(F.text == texts.BTN_CANCEL, StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.CANCELLED, reply_markup=kb.main_menu())


@router.message(F.text == texts.BTN_HELP)
async def show_help(message: Message) -> None:
    await message.answer(texts.HELP, reply_markup=kb.main_menu())


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
