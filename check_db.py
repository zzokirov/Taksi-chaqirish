import asyncio
import sys
import os
sys.path.append(os.path.abspath('.'))

from bot.database.database import async_session_maker
from bot.services.admin_service import AdminService
from bot.database.models import District
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        query = select(District)
        res = await session.execute(query)
        dists = res.scalars().all()
        print(f"Total districts in DB: {len(dists)}")
        for d in dists:
            print(f"- {d.name} (Active: {d.is_active})")
        
        # Test the filter logic
        TASHKENT_DISTRICTS = [
            "Bektemir tumani", "Chilonzor tumani", "Mirobod tumani", "Mirzo Ulug'bek tumani",
            "Olmazor tumani", "Sergeli tumani", "Shayxontohur tumani", "Uchtepa tumani",
            "Yakkasaroy tumani", "Yashnobod tumani", "Yunusobod tumani", "Yangihayot tumani"
        ]
        active = [d for d in dists if d.is_active]
        tosh = [d for d in active if d.name in TASHKENT_DISTRICTS]
        far = [d for d in active if d.name not in TASHKENT_DISTRICTS]
        
        print(f"Tashkent found: {len(tosh)}")
        print(f"Fergana found: {len(far)}")

if __name__ == '__main__':
    asyncio.run(main())
