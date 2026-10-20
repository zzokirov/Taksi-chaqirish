import asyncio
import sys
import os

# Loyiha papkasini tanitish
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from bot.database.database import async_session_maker
from bot.services.admin_service import AdminService

fergana_districts = [
    "Farg'ona shahri", "Marg'ilon shahri", "Qo'qon shahri", "Quvasoy shahri",
    "Oltiariq tumani", "Bag'dod tumani", "Beshariq tumani", "Buvayda tumani",
    "Dang'ara tumani", "Farg'ona tumani", "Furqat tumani", "Qo'shtepa tumani",
    "Quva tumani", "Rishton tumani", "So'x tumani", "Toshloq tumani",
    "Uchko'prik tumani", "Yozyovon tumani", "O'zbekiston tumani"
]

tashkent_districts = [
    "Bektemir tumani", "Chilonzor tumani", "Mirobod tumani", "Mirzo Ulug'bek tumani",
    "Olmazor tumani", "Sergeli tumani", "Shayxontohur tumani", "Uchtepa tumani",
    "Yakkasaroy tumani", "Yashnobod tumani", "Yunusobod tumani", "Yangihayot tumani"
]

async def seed():
    async with async_session_maker() as session:
        await session.execute(
            text("UPDATE districts SET name = :new_name WHERE name = :old_name"),
            {"new_name": "O'zbekiston tumani", "old_name": "Mirzo Ulug\u2018bek tumani"}
        )
        await session.commit()
        added_count = 0
        for d in fergana_districts + tashkent_districts:
            success = await AdminService.add_district(session, d)
            if success:
                added_count += 1
                print(f"+ Qoshildi: {d}")
            else:
                print(f"- Mavjud: {d}")
        await session.commit()
        print(f"\nJami {added_count} ta tuman bazaga muvaffaqiyatli qo'shildi va SAQLANDI!")

if __name__ == "__main__":
    asyncio.run(seed())
