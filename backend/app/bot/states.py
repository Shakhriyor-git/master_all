"""FSM holatlari — Mini App bor, faqat yangi obyekt oqimi qoldi."""

from aiogram.fsm.state import State, StatesGroup


class NewProject(StatesGroup):
    title = State()
    client_name = State()
