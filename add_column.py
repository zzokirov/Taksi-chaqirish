import asyncio
from bot.database.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE drivers ADD COLUMN subscription_end TIMESTAMP"))
            print("Column added.")
        except Exception as e:
            print("Error or already exists:", e)

if __name__ == "__main__":
    asyncio.run(main())
