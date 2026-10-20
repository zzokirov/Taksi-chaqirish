import asyncio
from bot.database.database import create_db, engine

async def run():
    print("Creating DB tables...")
    await create_db()
    print("Done!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
