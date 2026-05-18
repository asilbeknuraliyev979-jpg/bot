from aiogram import Router
from . import panel, test_manage, export

router = Router()
router.include_router(panel.router)
router.include_router(test_manage.router)
router.include_router(export.router)
