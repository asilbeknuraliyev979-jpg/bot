import asyncio
import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from loader import bot, dp, db
from handlers import router as master_router
from config.config import Config

logger = logging.getLogger("EduMasterBot.main")

async def setup_commands(bot: Bot):
    """
    Sets up basic commands in the Telegram interface.
    """
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish / qayta yuklash"),
        BotCommand(command="admin", description="Admin panelga kirish (faqat adminlar)")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    logger.info("🚀 Edu Master Bot starting...")
    
    # Ensure config storage folders exist
    Config.ensure_dirs()
    
    # Register master router which includes admin and user routers
    dp.include_router(master_router)
    
    # Register bot commands
    await setup_commands(bot)
    
    # Pre-populate default admin from .env in DB if not already exists
    if Config.ADMIN_ID:
        db.add_admin(Config.ADMIN_ID)
        logger.info(f"Added default admin ID: {Config.ADMIN_ID} to DB.")
        
    logger.info("✅ Bot is running. Polling...")
    
    # Start polling
    # Close any existing webhook (to prevent conflict errors)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot stopped.")
