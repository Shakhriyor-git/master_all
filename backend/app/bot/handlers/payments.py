"""To'lov qo'shish — maqsad → summa → usul → saqlash."""

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import repo, texts
from app.bot.keyboards import (
    AmountOkCb,
    BackCb,
    MethodCb,
    ProjectCb,
    PurposeCb,
)
from app.bot.states import PaymentForm
from app.bot.utils import parse_money
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
    await state.set_state(PaymentForm.purpose)
    await state.update_data(project_id=project.id)
    await callback.message.answer(
        texts.ASK_PAYMENT_PURPOSE, reply_markup=kb.purpose_kb()
    )
    await callback.answer()


@router.callback_query(PaymentForm.purpose, PurposeCb.filter())
async def payment_purpose(
    callback: CallbackQuery, callback_data: PurposeCb, state: FSMContext
) -> None:
    await state.update_data(purpose=callback_data.value)
    await state.set_state(PaymentForm.amount)
    await callback.message.answer(
        texts.ASK_PAYMENT_AMOUNT, reply_markup=kb.back_cancel_kb()
    )
    await callback.answer()


@router.message(PaymentForm.amount, F.text)
async def payment_amount(message: Message, state: FSMContext) -> None:
    if message.text == texts.BTN_BACK:
        await state.set_state(PaymentForm.purpose)
        await message.answer(
            texts.ASK_PAYMENT_PURPOSE, reply_markup=kb.purpose_kb()
        )
        return
    amount = parse_money(message.text)
    if amount is None:
        await message.answer(texts.BAD_PRICE)
        return
    await state.update_data(amount=str(amount))
    await state.set_state(PaymentForm.amount_confirm)
    await message.answer(
        texts.render_amount_confirm(amount), reply_markup=kb.amount_ok_kb()
    )


@router.callback_query(PaymentForm.amount_confirm, AmountOkCb.filter())
async def payment_amount_confirm(
    callback: CallbackQuery, callback_data: AmountOkCb, state: FSMContext
) -> None:
    if not callback_data.ok:
        await state.set_state(PaymentForm.amount)
        await callback.message.answer(
            texts.ASK_PAYMENT_AMOUNT, reply_markup=kb.back_cancel_kb()
        )
        await callback.answer()
        return
    await state.set_state(PaymentForm.method)
    await callback.message.answer(
        texts.ASK_PAYMENT_METHOD, reply_markup=kb.method_kb()
    )
    await callback.answer()


@router.callback_query(PaymentForm.method, BackCb.filter())
async def payment_method_back(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await state.set_state(PaymentForm.amount)
    await callback.message.answer(
        texts.ASK_PAYMENT_AMOUNT, reply_markup=kb.back_cancel_kb()
    )
    await callback.answer()


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
            purpose=data.get("purpose", "labor"),
        )
    )
    await session.commit()

    await callback.message.answer(
        texts.PAYMENT_SAVED, reply_markup=kb.main_menu()
    )
    await send_project_card(callback.message, session, project)
    await callback.answer()
