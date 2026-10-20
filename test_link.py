import asyncio
from config import settings
from aiogram import Bot

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        link = await bot.export_chat_invite_link(-1003912329772)
        print("Success:", link)
    except Exception as e:
        print("Error:", repr(e))
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
