"""FSM holatlari."""

from aiogram.fsm.state import State, StatesGroup


class NewProject(StatesGroup):
    title = State()
    client_name = State()


class EntryForm(StatesGroup):
    """Ish va material qo'shish — bitta oqim, `kind` state data'da."""

    pick_price = State()
    quantity = State()
    paid_by = State()  # faqat material uchun
    confirm = State()

    # "Boshqa" — katalogda yo'q pozitsiya
    new_name = State()
    new_unit = State()
    new_price = State()


class PaymentForm(StatesGroup):
    amount = State()
    method = State()


class NewPriceItem(StatesGroup):
    name = State()
    kind = State()
    unit = State()
    price = State()
