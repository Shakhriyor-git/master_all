"""Ish va material qo'shish — bitta FSM oqimi (kind state data'da)."""

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import repo, texts
from app.bot.keyboards import PageCb, PaidByCb, PickPriceCb, ProjectCb, UnitCb
from app.bot.states import EntryForm
from app.bot.utils import fmt_unit, paginate, parse_quantity
from app.bot.views import send_project_card
from app.models import Entry, ProjectPrice, User

router = Router(name="entries")


async def _render_pick(
    callback: CallbackQuery,
    session: AsyncSession,
    project_id: int,
    kind: str,
    page: int,
    *,
    edit: bool,
) -> None:
    prices = await repo.project_prices_by_kind(session, project_id, kind)
    chunk, page, total = paginate(prices, page)
    text = texts.ASK_PICK_WORK if kind == "work" else texts.ASK_PICK_MATERIAL
    markup = kb.price_pick_kb(chunk, project_id, kind, page, total)
    if edit:
        await callback.message.edit_text(text, reply_markup=markup)
    else:
        await callback.message.answer(text, reply_markup=markup)


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
    await state.set_state(EntryForm.pick_price)
    await state.update_data(project_id=project.id, kind=callback_data.action)
    await _render_pick(
        callback, session, project.id, callback_data.action, 1, edit=True
    )
    await callback.answer()


@router.callback_query(EntryForm.pick_price, PageCb.filter(F.scope == "pick"))
async def entry_pick_page(
    callback: CallbackQuery,
    callback_data: PageCb,
    session: AsyncSession,
) -> None:
    await _render_pick(
        callback,
        session,
        callback_data.project_id,
        callback_data.kind,
        callback_data.page,
        edit=True,
    )
    await callback.answer()


@router.callback_query(EntryForm.pick_price, PickPriceCb.filter())
async def entry_pick(
    callback: CallbackQuery,
    callback_data: PickPriceCb,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    if callback_data.price_id == 0:
        # "Boshqa" — katalogda yo'q pozitsiya
        await state.set_state(EntryForm.new_name)
        await callback.message.answer(
            texts.ASK_NEW_NAME, reply_markup=kb.cancel_kb()
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
    await state.set_state(EntryForm.quantity)
    await callback.message.answer(
        texts.ASK_QUANTITY.format(unit=fmt_unit(price.unit)),
        reply_markup=kb.cancel_kb(),
    )
    await callback.answer()


# ---- "Boshqa" pozitsiya kichik oqimi ----
@router.message(EntryForm.new_name, F.text)
async def entry_new_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer(texts.ASK_NEW_NAME)
        return
    await state.update_data(source="other", name=name[:200])
    await state.set_state(EntryForm.new_unit)
    await message.answer(texts.ASK_NEW_UNIT, reply_markup=kb.unit_kb())


@router.callback_query(EntryForm.new_unit, UnitCb.filter())
async def entry_new_unit(
    callback: CallbackQuery, callback_data: UnitCb, state: FSMContext
) -> None:
    await state.update_data(unit=callback_data.value)
    await state.set_state(EntryForm.new_price)
    await callback.message.answer(
        texts.ASK_NEW_PRICE, reply_markup=kb.cancel_kb()
    )
    await callback.answer()


@router.message(EntryForm.new_price, F.text)
async def entry_new_price(message: Message, state: FSMContext) -> None:
    price = parse_quantity(message.text)
    if price is None:
        await message.answer(texts.BAD_PRICE)
        return
    data = await state.get_data()
    await state.update_data(unit_price=str(price))
    await state.set_state(EntryForm.quantity)
    await message.answer(
        texts.ASK_QUANTITY.format(unit=fmt_unit(data["unit"])),
        reply_markup=kb.cancel_kb(),
    )


# ---- Miqdor -> (material: kim to'ladi) -> tasdiq ----
@router.message(EntryForm.quantity, F.text)
async def entry_quantity(message: Message, state: FSMContext) -> None:
    qty = parse_quantity(message.text)
    if qty is None:
        await message.answer(texts.BAD_QUANTITY)
        return
    await state.update_data(quantity=str(qty))
    data = await state.get_data()
    if data["kind"] == "material":
        await state.set_state(EntryForm.paid_by)
        await message.answer(texts.ASK_PAID_BY, reply_markup=kb.paid_by_kb())
    else:
        await _show_confirm(message, state)


@router.callback_query(EntryForm.paid_by, PaidByCb.filter())
async def entry_paid_by(
    callback: CallbackQuery, callback_data: PaidByCb, state: FSMContext
) -> None:
    await state.update_data(paid_by=callback_data.value)
    await _show_confirm(callback.message, state)
    await callback.answer()


async def _show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(EntryForm.confirm)
    text = texts.render_confirm_entry(
        data["name"],
        Decimal(data["quantity"]),
        data["unit"],
        Decimal(data["unit_price"]),
    )
    await message.answer(text, reply_markup=kb.confirm_kb())


@router.callback_query(EntryForm.confirm, kb.ConfirmCb.filter())
async def entry_confirm(
    callback: CallbackQuery,
    callback_data: kb.ConfirmCb,
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

    if not callback_data.ok:
        await callback.message.answer(
            texts.CANCELLED, reply_markup=kb.main_menu()
        )
        await send_project_card(callback.message, session, project)
        await callback.answer()
        return

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
            source="manual",
        )
    )
    await session.commit()

    await callback.message.answer(
        texts.ENTRY_SAVED, reply_markup=kb.main_menu()
    )
    await send_project_card(callback.message, session, project)
    await callback.answer()
