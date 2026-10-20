import asyncio
import asyncpg

async def main():
    # Standart postgres bazasiga ulanib yangi baza yaratamiz
    try:
        conn = await asyncpg.connect(user='postgres', password='1', database='postgres', host='localhost')
        await conn.execute('CREATE DATABASE taxi_bot')
        print("Database 'taxi_bot' created successfully!")
        await conn.close()
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database already exists.")
    except Exception as e:
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(main())
