"""To'lov qo'shish — summa -> usul -> saqlash."""

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import repo, texts
from app.bot.keyboards import MethodCb, ProjectCb
from app.bot.states import PaymentForm
from app.bot.utils import parse_quantity
from app.bot.views import send_project_card
from app.models import Payment, User

router = Router(name="payments")


@router.callback_query(ProjectCb.filter(F.action == "payment"))
async def payment_start(
    callback: CallbackQuery,
    callback_data: ProjectCb,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    project = await repo.get_owned_project(
        session, user.id, callback_data.project_id
    )
    if project is None:
        await callback.answer(texts.ERROR, show_alert=True)
        return
    await state.set_state(PaymentForm.amount)
    await state.update_data(project_id=project.id)
    await callback.message.answer(
        texts.ASK_PAYMENT_AMOUNT, reply_markup=kb.cancel_kb()
    )
    await callback.answer()


@router.message(PaymentForm.amount, F.text)
async def payment_amount(message: Message, state: FSMContext) -> None:
    amount = parse_quantity(message.text)
    if amount is None:
        await message.answer(texts.BAD_PRICE)
        return
    await state.update_data(amount=str(amount))
    await state.set_state(PaymentForm.method)
    await message.answer(texts.ASK_PAYMENT_METHOD, reply_markup=kb.method_kb())


@router.callback_query(PaymentForm.method, MethodCb.filter())
async def payment_method(
    callback: CallbackQuery,
    callback_data: MethodCb,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    data = await state.get_data()
    await state.clear()

    project = await repo.get_owned_project(
        session, user.id, data["project_id"]
    )
    if project is None:
        await callback.answer(texts.ERROR, show_alert=True)
        return

    session.add(
        Payment(
            project_id=project.id,
            created_by_user_id=user.id,
            amount=Decimal(data["amount"]),
            method=callback_data.value,
        )
    )
    await session.commit()

    await callback.message.answer(
        texts.PAYMENT_SAVED, reply_markup=kb.main_menu()
    )
    await send_project_card(callback.message, session, project)
    await callback.answer()
