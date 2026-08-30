"""Narxlarim — katalog (price_items) va obyekt narxlari ko'rinishi."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot import repo, texts
from app.bot.keyboards import CatalogCb, KindCb, PageCb, ProjectCb, UnitCb
from app.bot.states import NewPriceItem
from app.bot.utils import fmt_money, fmt_unit, paginate, parse_quantity
from app.models import PriceItem, ProjectPrice, User

router = Router(name="prices")


async def _show_catalog(
    target: Message | CallbackQuery,
    session: AsyncSession,
    user: User,
    page: int,
) -> None:
    items = await repo.catalog_items(session, user.id)
    if not items:
        text = f"{texts.PRICES_TITLE}\n\n{texts.PRICES_EMPTY}"
        chunk, page, total = [], 1, 1
    else:
        chunk, page, total = paginate(items, page)
        lines = [texts.PRICES_TITLE, ""]
        for it in chunk:
            lines.append(
                texts.PRICE_ITEM_LINE.format(
                    name=texts.esc(it.name),
                    price=fmt_money(it.default_price),
                    unit=fmt_unit(it.unit),
                    kind=texts.KIND_UZ.get(it.kind, it.kind),
                )
            )
        text = "\n".join(lines)
    markup = kb.catalog_kb(chunk, page, total)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(F.text == texts.BTN_MY_PRICES)
async def my_prices(
    message: Message, session: AsyncSession, user: User
) -> None:
    await _show_catalog(message, session, user, 1)


@router.callback_query(PageCb.filter(F.scope == "catalog"))
async def catalog_page(
    callback: CallbackQuery,
    callback_data: PageCb,
    session: AsyncSession,
    user: User,
) -> None:
    await _show_catalog(callback, session, user, callback_data.page)


@router.callback_query(CatalogCb.filter(F.action == "del"))
async def catalog_delete(
    callback: CallbackQuery,
    callback_data: CatalogCb,
    session: AsyncSession,
    user: User,
) -> None:
    item = (
        await session.execute(
            select(PriceItem).where(
                PriceItem.id == callback_data.item_id,
                PriceItem.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if item is not None:
        item.is_active = False
        await session.commit()
        await callback.answer(texts.PRICE_REMOVED)
    else:
        await callback.answer(texts.ERROR, show_alert=True)
    await _show_catalog(callback, session, user, 1)


# --------------------------------------------------------------------------
# Yangi katalog pozitsiyasi
# --------------------------------------------------------------------------
@router.callback_query(CatalogCb.filter(F.action == "add"))
async def catalog_add_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await state.set_state(NewPriceItem.name)
    await callback.message.answer(
        texts.ASK_PI_NAME, reply_markup=kb.cancel_kb()
    )
    await callback.answer()


@router.message(NewPriceItem.name, F.text)
async def pi_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer(texts.ASK_PI_NAME)
        return
    await state.update_data(name=name[:200])
    await state.set_state(NewPriceItem.kind)
    await message.answer(texts.ASK_PI_KIND, reply_markup=kb.kind_kb())


@router.callback_query(NewPriceItem.kind, KindCb.filter())
async def pi_kind(
    callback: CallbackQuery, callback_data: KindCb, state: FSMContext
) -> None:
    await state.update_data(kind=callback_data.value)
    await state.set_state(NewPriceItem.unit)
    await callback.message.answer(texts.ASK_PI_UNIT, reply_markup=kb.unit_kb())
    await callback.answer()


@router.callback_query(NewPriceItem.unit, UnitCb.filter())
async def pi_unit(
    callback: CallbackQuery, callback_data: UnitCb, state: FSMContext
) -> None:
    await state.update_data(unit=callback_data.value)
    await state.set_state(NewPriceItem.price)
    await callback.message.answer(
        texts.ASK_PI_PRICE, reply_markup=kb.cancel_kb()
    )
    await callback.answer()


@router.message(NewPriceItem.price, F.text)
async def pi_price(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    price = parse_quantity(message.text)
    if price is None:
        await message.answer(texts.BAD_PRICE)
        return
    data = await state.get_data()
    await state.clear()

    item = PriceItem(
        user_id=user.id,
        name=data["name"],
        kind=data["kind"],
        unit=data["unit"],
        default_price=price,
    )
    session.add(item)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        await message.answer(
            "Bu nom va tur bo'yicha pozitsiya allaqachon bor.",
            reply_markup=kb.main_menu(),
        )
        await _show_catalog(message, session, user, 1)
        return

    await message.answer(texts.PRICE_ADDED, reply_markup=kb.main_menu())
    await _show_catalog(message, session, user, 1)


# --------------------------------------------------------------------------
# Obyekt kartasidagi "⚙️ Narxlar"
# --------------------------------------------------------------------------
@router.callback_query(ProjectCb.filter(F.action == "prices"))
async def project_prices(
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

    rows = (
        await session.execute(
            select(ProjectPrice)
            .where(
                ProjectPrice.project_id == project.id,
                ProjectPrice.is_active.is_(True),
            )
            .order_by(ProjectPrice.kind, ProjectPrice.name)
        )
    ).scalars().all()

    if rows:
        lines = ["<b>Obyekt narxlari</b>", ""]
        for r in rows:
            lines.append(
                texts.PRICE_ITEM_LINE.format(
                    name=texts.esc(r.name),
                    price=fmt_money(r.price),
                    unit=fmt_unit(r.unit),
                    kind=texts.KIND_UZ.get(r.kind, r.kind),
                )
            )
        text = "\n".join(lines)
    else:
        text = "Obyektda hali narx yo'q."

    await callback.message.answer(
        text, reply_markup=kb.import_offer_kb(project.id)
    )
    await callback.answer()
