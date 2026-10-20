import asyncio
from bot.database.database import async_session_maker
from bot.database.models import DriverGroup
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(DriverGroup))
        groups = result.scalars().all()
        for g in groups:
            print(f"Group: {g.group_name}, telegram_id: {g.telegram_group_id}, link: {g.invite_link}")

if __name__ == "__main__":
    asyncio.run(main())
