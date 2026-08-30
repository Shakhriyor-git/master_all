"""Ish / material / xarajat qo'shish — kategoriya → xizmat → ... oqimi.

Har qadamda "◀️ Orqaga": ish steplarda inline tugma, matn kiritish
steplarida reply tugma (BTN_BACK).
"""

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
    CategoryCb,
    ConfirmCb,
    MethodCb,
    PaidByCb,
    PickPriceCb,
    ProjectCb,
    UnitCb,
)
from app.bot.states import EntryForm
from app.bot.utils import fmt_unit, paginate, parse_money, parse_quantity
from app.bot.views import send_project_card
from app.models import Entry, ProjectPrice, User

router = Router(name="entries")

_NEEDS_PAYMENT = {"material", "expense"}


# ==========================================================================
# Kirish nuqtalari
# ==========================================================================
@router.callback_query(ProjectCb.filter(F.action.in_({"work", "material"})))
async def entry_start(
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
    await state.set_state(EntryForm.pick_category)
    await state.update_data(
        project_id=project.id, kind=callback_data.action, source="catalog"
    )
    await _go_category(callback.message, state, session)
    await callback.answer()


@router.callback_query(ProjectCb.filter(F.action == "expense"))
async def expense_start(
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
    await state.set_state(EntryForm.new_name)
    await state.update_data(
        project_id=project.id, kind="expense", source="expense"
    )
    await callback.message.answer(
        texts.ASK_EXPENSE_NAME, reply_markup=kb.cancel_kb()
    )
    await callback.answer()


# ==========================================================================
# Qadam funksiyalari
# ==========================================================================
async def _go_category(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    buckets = await repo.project_price_categories(
        session, data["project_id"], data["kind"]
    )
    if len(buckets) <= 1:
        # bitta (yoki nol) bo'lim — qadam o'tkazib yuboriladi
        cat_id = buckets[0].id if buckets else 0
        await state.update_data(category_id=cat_id, has_categories=False)
        await _go_price(message, state, session)
        return
    await state.set_state(EntryForm.pick_category)
    await state.update_data(has_categories=True)
    await message.answer(
        texts.ASK_CATEGORY, reply_markup=kb.category_pick_kb(buckets)
    )


async def _go_price(
    message: Message, state: FSMContext, session: AsyncSession, page: int = 1
) -> None:
    data = await state.get_data()
    prices = await repo.project_prices_in_category(
        session, data["project_id"], data["kind"], data.get("category_id", 0)
    )
    chunk, page, total = paginate(prices, page)
    ask = (
        texts.ASK_PICK_WORK
        if data["kind"] == "work"
        else texts.ASK_PICK_MATERIAL
    )
    await state.set_state(EntryForm.pick_price)
    await message.answer(
        ask,
        reply_markup=kb.price_pick_kb(
            chunk, data["project_id"], data["kind"], page, total
        ),
    )


async def _go_quantity(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(EntryForm.quantity)
    await message.answer(
        texts.ASK_QUANTITY.format(unit=fmt_unit(data["unit"])),
        reply_markup=kb.back_cancel_kb(),
    )


async def _go_paid_by(message: Message, state: FSMContext) -> None:
    await state.set_state(EntryForm.paid_by)
    await message.answer(texts.ASK_PAID_BY, reply_markup=kb.paid_by_kb())


async def _go_method(message: Message, state: FSMContext) -> None:
    await state.set_state(EntryForm.method)
    await message.answer(texts.ASK_METHOD, reply_markup=kb.method_kb())


async def _go_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(EntryForm.confirm)
    text = texts.render_confirm_entry(
        data["name"],
        Decimal(data["quantity"]),
        data["unit"],
        Decimal(data["unit_price"]),
    )
    await message.answer(text, reply_markup=kb.confirm_kb())


async def _after_quantity(message: Message, state: FSMContext) -> None:
    """Miqdordan keyin: material/expense -> kim to'ladi, ish -> tasdiq."""
    data = await state.get_data()
    if data["kind"] in _NEEDS_PAYMENT:
        await _go_paid_by(message, state)
    else:
        await _go_confirm(message, state)


# ==========================================================================
# pick_category
# ==========================================================================
@router.callback_query(EntryForm.pick_category, CategoryCb.filter())
async def on_category(
    callback: CallbackQuery,
    callback_data: CategoryCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.update_data(category_id=callback_data.category_id)
    await _go_price(callback.message, state, session)
    await callback.answer()


# ==========================================================================
# pick_price
# ==========================================================================
@router.callback_query(EntryForm.pick_price, kb.PageCb.filter(F.scope == "pick"))
async def price_page(
    callback: CallbackQuery,
    callback_data: kb.PageCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await _go_price(callback.message, state, session, callback_data.page)
    await callback.answer()


@router.callback_query(EntryForm.pick_price, PickPriceCb.filter())
async def on_price(
    callback: CallbackQuery,
    callback_data: PickPriceCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if callback_data.price_id == 0:
        await state.update_data(source="other")
        await state.set_state(EntryForm.new_name)
        await callback.message.answer(
            texts.ASK_NEW_NAME, reply_markup=kb.back_cancel_kb()
        )
        await callback.answer()
        return

    price = await session.get(ProjectPrice, callback_data.price_id)
    data = await state.get_data()
    if price is None or price.project_id != data.get("project_id"):
        await callback.answer(texts.ERROR, show_alert=True)
        return
    await state.update_data(
        source="catalog",
        project_price_id=price.id,
        name=price.name,
        unit=price.unit,
        kind=price.kind,
        unit_price=str(price.price),
    )
    await _go_quantity(callback.message, state)
    await callback.answer()


@router.callback_query(EntryForm.pick_price, BackCb.filter())
async def price_back(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    data = await state.get_data()
    if data.get("has_categories"):
        await _go_category(callback.message, state, session)
    else:
        await _cancel_to_card(
            callback.message, state, session, user, data["project_id"]
        )
    await callback.answer()


# ==========================================================================
# "Boshqa" / xarajat: new_name -> new_unit -> new_price
# ==========================================================================
@router.message(EntryForm.new_name, F.text)
async def on_new_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    if message.text == texts.BTN_BACK:
        data = await state.get_data()
        if data["kind"] == "expense":
            await _cancel_to_card(
                message, state, session, user, data["project_id"]
            )
        else:
            await _go_price(message, state, session)
        return
    name = message.text.strip()
    if not name:
        await message.answer(texts.ASK_NEW_NAME)
        return
    data = await state.get_data()
    await state.update_data(name=name[:200])
    if data["kind"] == "expense":
        await state.update_data(unit="summa", quantity="1")
        await state.set_state(EntryForm.new_price)
        await message.answer(
            texts.ASK_EXPENSE_AMOUNT, reply_markup=kb.back_cancel_kb()
        )
    else:
        await state.set_state(EntryForm.new_unit)
        await message.answer(
            texts.ASK_NEW_UNIT, reply_markup=kb.unit_kb(back=True)
        )


@router.callback_query(EntryForm.new_unit, UnitCb.filter())
async def on_new_unit(
    callback: CallbackQuery, callback_data: UnitCb, state: FSMContext
) -> None:
    await state.update_data(unit=callback_data.value)
    await state.set_state(EntryForm.new_price)
    await callback.message.answer(
        texts.ASK_NEW_PRICE, reply_markup=kb.back_cancel_kb()
    )
    await callback.answer()


@router.callback_query(EntryForm.new_unit, BackCb.filter())
async def new_unit_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EntryForm.new_name)
    await callback.message.answer(
        texts.ASK_NEW_NAME, reply_markup=kb.back_cancel_kb()
    )
    await callback.answer()


@router.message(EntryForm.new_price, F.text)
async def on_new_price(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    if message.text == texts.BTN_BACK:
        if data["kind"] == "expense":
            await state.set_state(EntryForm.new_name)
            await message.answer(
                texts.ASK_EXPENSE_NAME, reply_markup=kb.back_cancel_kb()
            )
        else:
            await state.set_state(EntryForm.new_unit)
            await message.answer(
                texts.ASK_NEW_UNIT, reply_markup=kb.unit_kb(back=True)
            )
        return
    price = parse_money(message.text)
    if price is None:
        await message.answer(texts.BAD_PRICE)
        return
    await state.update_data(unit_price=str(price))
    await _ask_price_confirm(message, state)


async def _ask_price_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(EntryForm.new_price_confirm)
    price = Decimal(data["unit_price"])
    if data["kind"] == "expense":
        text = texts.render_amount_confirm(price)
    else:
        text = texts.render_price_confirm(data["name"], price, data["unit"])
    await message.answer(text, reply_markup=kb.amount_ok_kb())


@router.callback_query(EntryForm.new_price_confirm, AmountOkCb.filter())
async def on_price_confirm(
    callback: CallbackQuery, callback_data: AmountOkCb, state: FSMContext
) -> None:
    data = await state.get_data()
    if not callback_data.ok:
        # "✏️ Qayta yozish"
        await state.set_state(EntryForm.new_price)
        ask = (
            texts.ASK_EXPENSE_AMOUNT
            if data["kind"] == "expense"
            else texts.ASK_NEW_PRICE
        )
        await callback.message.answer(ask, reply_markup=kb.back_cancel_kb())
        await callback.answer()
        return
    if data["kind"] == "expense":
        await _go_paid_by(callback.message, state)
    else:
        await _go_quantity(callback.message, state)
    await callback.answer()


# ==========================================================================
# quantity
# ==========================================================================
@router.message(EntryForm.quantity, F.text)
async def on_quantity(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    if message.text == texts.BTN_BACK:
        if data.get("source") == "other":
            await state.set_state(EntryForm.new_price)
            await message.answer(
                texts.ASK_NEW_PRICE, reply_markup=kb.back_cancel_kb()
            )
        else:
            await _go_price(message, state, session)
        return
    qty = parse_quantity(message.text)
    if qty is None:
        await message.answer(texts.BAD_QUANTITY)
        return
    await state.update_data(quantity=str(qty))
    await _after_quantity(message, state)


# ==========================================================================
# paid_by
# ==========================================================================
@router.callback_query(EntryForm.paid_by, PaidByCb.filter())
async def on_paid_by(
    callback: CallbackQuery, callback_data: PaidByCb, state: FSMContext
) -> None:
    await state.update_data(paid_by=callback_data.value)
    await _go_method(callback.message, state)
    await callback.answer()


@router.callback_query(EntryForm.paid_by, BackCb.filter())
async def paid_by_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if data["kind"] == "expense":
        await state.set_state(EntryForm.new_price)
        await callback.message.answer(
            texts.ASK_EXPENSE_AMOUNT, reply_markup=kb.back_cancel_kb()
        )
    else:
        await _go_quantity(callback.message, state)
    await callback.answer()


# ==========================================================================
# method
# ==========================================================================
@router.callback_query(EntryForm.method, MethodCb.filter())
async def on_method(
    callback: CallbackQuery, callback_data: MethodCb, state: FSMContext
) -> None:
    await state.update_data(payment_method=callback_data.value)
    await _go_confirm(callback.message, state)
    await callback.answer()


@router.callback_query(EntryForm.method, BackCb.filter())
async def method_back(callback: CallbackQuery, state: FSMContext) -> None:
    await _go_paid_by(callback.message, state)
    await callback.answer()


# ==========================================================================
# confirm
# ==========================================================================
@router.callback_query(EntryForm.confirm, BackCb.filter())
async def confirm_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if data["kind"] in _NEEDS_PAYMENT:
        await _go_method(callback.message, state)
    else:
        await _go_quantity(callback.message, state)
    await callback.answer()


@router.callback_query(EntryForm.confirm, ConfirmCb.filter())
async def on_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCb,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    data = await state.get_data()
    project = await repo.get_owned_project(
        session, user.id, data["project_id"]
    )
    if project is None:
        await state.clear()
        await callback.answer(texts.ERROR, show_alert=True)
        return

    if not callback_data.ok:
        await _cancel_to_card(
            callback.message, state, session, user, data["project_id"]
        )
        await callback.answer()
        return

    await state.clear()

    project_price_id = data.get("project_price_id")
    if data.get("source") == "other":
        new_price = ProjectPrice(
            project_id=project.id,
            price_item_id=None,
            name=data["name"],
            kind=data["kind"],
            unit=data["unit"],
            price=Decimal(data["unit_price"]),
        )
        session.add(new_price)
        await session.flush()
        project_price_id = new_price.id

    session.add(
        Entry(
            project_id=project.id,
            project_price_id=project_price_id,
            created_by_user_id=user.id,
            kind=data["kind"],
            name=data["name"],
            unit=data["unit"],
            quantity=Decimal(data["quantity"]),
            unit_price=Decimal(data["unit_price"]),
            paid_by=data.get("paid_by", "master"),
            payment_method=data.get("payment_method"),
            source="manual",
        )
    )
    await session.commit()

    await callback.message.answer(
        texts.ENTRY_SAVED, reply_markup=kb.main_menu()
    )
    await send_project_card(callback.message, session, project)
    await callback.answer()


async def _cancel_to_card(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    project_id: int,
) -> None:
    await state.clear()
    await message.answer(texts.CANCELLED, reply_markup=kb.main_menu())
    project = await repo.get_owned_project(session, user.id, project_id)
    if project is not None:
        await send_project_card(message, session, project)
