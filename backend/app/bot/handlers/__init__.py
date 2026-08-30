"""Barcha handler router'larini bitta router ostida yig'adi.

Mini App bor — bot faqat: salomlashish, obyektlar ro'yxati (o'qish uchun),
yangi obyekt, yordam. Qolgan hamma narsa ilovada.
"""

from aiogram import Router

from app.bot.handlers import projects, start

router = Router(name="root")
# start avval — /bekor va bosh menyu tugmalari eng yuqori ustuvorlikda
router.include_router(start.router)
router.include_router(projects.router)
