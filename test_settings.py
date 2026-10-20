import asyncio
from bot.database.database import async_session_maker
from bot.database.models import Setting
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(Setting))
        settings = result.scalars().all()
        for s in settings:
            print(f"{s.key}: {s.value}")

if __name__ == "__main__":
    asyncio.run(main())
