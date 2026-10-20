import asyncio
from config import settings
from aiogram import Bot
from bot.database.database import async_session_maker
from bot.database.models import DriverGroup
from sqlalchemy import select

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(DriverGroup))
            groups = result.scalars().all()
            for g in groups:
                if g.telegram_group_id and not g.invite_link:
                    try:
                        print(f"Exporting link for {g.group_name} ({g.telegram_group_id})")
                        link = await bot.export_chat_invite_link(g.telegram_group_id)
                        g.invite_link = link
                        print(f"Generated: {link}")
                    except Exception as e:
                        print(f"Failed to generate link for {g.group_name}: {e}")
            await session.commit()
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
