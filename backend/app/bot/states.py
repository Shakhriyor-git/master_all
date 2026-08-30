"""FSM holatlari."""

from aiogram.fsm.state import State, StatesGroup


class NewProject(StatesGroup):
    title = State()
    client_name = State()


class EntryForm(StatesGroup):
    """Ish / material / xarajat qo'shish — bitta oqim, `kind` state data'da.

    Har qadamda "◀️ Orqaga" bor: adashgan usta boshidan boshlamaydi.
    """

    pick_category = State()
    pick_price = State()
    quantity = State()
    paid_by = State()  # material va expense uchun
    method = State()  # material va expense uchun
    confirm = State()

    # "Boshqa" — katalogda yo'q pozitsiya (va expense uchun nom/summa)
    new_name = State()
    new_unit = State()
    new_price = State()
    new_price_confirm = State()  # narx/summa formatlangan holda tasdiqlanadi


class PaymentForm(StatesGroup):
    purpose = State()
    amount = State()
    amount_confirm = State()
    method = State()


class NewPriceItem(StatesGroup):
    name = State()
    kind = State()
    unit = State()
    price = State()
    price_confirm = State()
