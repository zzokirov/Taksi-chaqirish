import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from bot.database.database import create_db, close_db
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.handlers import get_handlers_router

# Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

import os
from aiohttp import web
from aiogram.client.default import DefaultBotProperties

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", health_check)
        app.router.add_get("/health", health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Health check web server running on port {port}")
    except Exception as e:
        logger.warning(f"Could not start web server: {e}")

async def main():
    logger.info("Bot is starting...")
    asyncio.create_task(start_web_server())
    
    if not settings.BOT_TOKEN:
        logger.error("XATOLIK: BOT_TOKEN o'rnatilmagan! Render Dashboard -> Environment bo'limida BOT_TOKEN ni kiriting.")
        return
    
    # Initialize DB
    logger.info(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}")
    try:
        await create_db()
    except Exception as e:
        logger.error(f"XATOLIK: Ma'lumotlar bazasiga ulanib bo'lmadi! DATABASE_URL sozlamasini tekshiring: {e}")
        raise
    
    # Auto-seed districts, groups and settings if empty
    try:
        from bot.database.database import async_session_maker
        from seed_districts import seed_districts_data, seed_groups_data, seed_settings_data
        async with async_session_maker() as session:
            await seed_districts_data(session)
            g_added = await seed_groups_data(session)
            await seed_settings_data(session)
            if g_added > 0:
                logger.info(f"Yangi bazaga {g_added} ta guruh va sozlamalar muvaffaqiyatli yuklandi.")
    except Exception as e:
        logger.warning(f"Error auto-seeding initial data: {e}")
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Middlewares
    dp.update.middleware(DatabaseMiddleware())
    
    # Routers
    router = get_handlers_router()
    dp.include_router(router)
    
    try:
        from aiogram.types import (
            BotCommand,
            BotCommandScopeAllPrivateChats,
            BotCommandScopeAllGroupChats,
            BotCommandScopeAllChatAdministrators,
            BotCommandScopeDefault,
            MenuButtonDefault,
        )
        try:
            await bot.delete_my_commands(scope=BotCommandScopeDefault())
            await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())
            await bot.delete_my_commands(scope=BotCommandScopeAllChatAdministrators())
            
            private_commands = [
                BotCommand(command="start", description="Botni ishga tushirish"),
                BotCommand(command="buyurtma", description="Taksi yoki pochta buyurtma qilish"),
                BotCommand(command="haydovchi", description="Haydovchi rejimiga o'tish"),
                BotCommand(command="buyurtmalarim", description="Faol buyurtmalarni ko'rish"),
                BotCommand(command="yordam", description="Qo'llab-quvvatlash xizmati"),
            ]
            await bot.set_my_commands(commands=private_commands, scope=BotCommandScopeAllPrivateChats())
            await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
        except Exception as e:
            logger.warning(f"Error setting bot commands: {e}")

        from bot.cron import subscription_checker
        asyncio.create_task(subscription_checker(bot))
        
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
