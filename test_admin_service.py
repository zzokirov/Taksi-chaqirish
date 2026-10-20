import asyncio
from bot.database.database import async_session_maker
from bot.services.admin_service import AdminService

async def main():
    async with async_session_maker() as session:
        ps = await AdminService.get_payment_settings(session)
        print("Payment Settings returned by AdminService:")
        print(ps)

if __name__ == "__main__":
    asyncio.run(main())
