import asyncio
import logging
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeDefault,
    MenuButtonDefault,
)
from config import settings

async def setup_commands():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        print("1. Guruhlardan va defaultdan buyruqlarni o'chirish...")
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())
        await bot.delete_my_commands(scope=BotCommandScopeAllChatAdministrators())
        print("Guruhlardan buyruqlar o'chirildi.")

        print("2. Faqat shaxsiy (private) chatlar uchun buyruqlarni o'rnatish...")
        private_commands = [
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="buyurtma", description="Taksi yoki pochta buyurtma qilish"),
            BotCommand(command="haydovchi", description="Haydovchi rejimiga o'tish"),
            BotCommand(command="buyurtmalarim", description="Faol buyurtmalarni ko'rish"),
            BotCommand(command="yordam", description="Qo'llab-quvvatlash xizmati"),
        ]
        await bot.set_my_commands(commands=private_commands, scope=BotCommandScopeAllPrivateChats())
        print("Shaxsiy chatlar uchun buyruqlar o'rnatildi.")

        print("3. Guruhlar uchun menyu tugmasini tozalash...")
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
        print("Bajarildi!")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(setup_commands())
