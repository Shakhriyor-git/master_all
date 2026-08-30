"""Barcha handler router'larini bitta router ostida yig'adi."""

from aiogram import Router

from app.bot.handlers import (
    entries,
    payments,
    prices,
    projects,
    reports,
    start,
)

router = Router(name="root")
# start avval — /bekor va bosh menyu tugmalari eng yuqori ustuvorlikda
router.include_router(start.router)
router.include_router(projects.router)
router.include_router(entries.router)
router.include_router(payments.router)
router.include_router(reports.router)
router.include_router(prices.router)
