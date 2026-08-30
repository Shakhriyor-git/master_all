"""Bot va Dispatcher — yagona nusxa."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings

# Token bo'sh bo'lsa import paytida xato bo'lmasin uchun to'ldiruvchi
# qiymat — polling.py haqiqiy token yo'qligini tekshirib ogohlantiradi.
_PLACEHOLDER_TOKEN = "1:" + "a" * 35  # noqa: S105

bot = Bot(
    token=settings.bot_token or _PLACEHOLDER_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# MVP uchun MemoryStorage yetadi — qayta ishga tushganda FSM holati
# yo'qoladi, bu maqbul.
dp = Dispatcher(storage=MemoryStorage())
