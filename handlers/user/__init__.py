from aiogram import Router
from . import start, menu, test

router = Router()
router.include_router(start.router)
router.include_router(menu.router)
router.include_router(test.router)
