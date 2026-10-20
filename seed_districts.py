import asyncio
import sys
import os

# Loyiha papkasini tanitish
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, select
from bot.database.database import async_session_maker
from bot.database.models import DriverGroup, Setting
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

groups_mapping = [
    ("Farg'ona shahri", "Farg'ona shahar", -1003934488953, 'https://t.me/+93WZQeSgcfkyNWYy'),
    ("Marg'ilon shahri", 'Margʻilon shahri', -1004390854715, 'https://t.me/+11lQlfW5uNY4MDAy'),
    ("Qo'qon shahri", "Qo'qon shafyorlari", -1004306080296, 'https://t.me/+sTMjgQrralk3MGU6'),
    ('Quvasoy shahri', 'Quvasoy shahri', -1003451950198, 'https://t.me/+Kxj1IFsl9YhiMmQy'),
    ('Oltiariq tumani', 'Oltariq shafyorlari', -1004304763844, 'https://t.me/+9WNaGHNRUZdjM2Ri'),
    ("Bag'dod tumani", "Bog'dod shafyorlari", -1003880567037, 'https://t.me/+FZp2iZeo99FiODBi'),
    ('Beshariq tumani', 'Beshariq shafyorlari', -1003912329772, 'https://t.me/+rWI3hPVBToFiZTIy'),
    ('Buvayda tumani', 'Buvayda tumani', -1003992049806, 'https://t.me/+XMtha-unff9iODQ6'),
    ("Dang'ara tumani", "Dang'ara shafyorlari", -1004468913392, 'https://t.me/+Wyn3KWEnrHc5ZjI6'),
    ("Farg'ona tumani", 'Fargʻona tumani', -1004343609238, 'https://t.me/+u6kMUBoC-OoyZTAy'),
    ("Qo'shtepa tumani", 'Qoʻshtepa tumani', -1003674485102, 'https://t.me/+K6EyLHBR1gE4NDYy'),
    ('Quva tumani', 'Quva tumani', -1004364212832, 'https://t.me/+5IGBrpkLShdmZjky'),
    ("So'x tumani", 'Soʻx tumani', -1003920235824, 'https://t.me/+YO6kl3GZyXk1N2Vi'),
    ('Toshloq tumani', 'Toshloq tumani', -1004305971230, 'https://t.me/+ZKRrG8Vx3rYwMjAy'),
    ("Uchko'prik tumani", 'Uchkoprik shafyorlari', -1004481291136, 'https://t.me/+q4Z5i67QMvw5MWYy'),
    ('Yozyovon tumani', 'Yozyovon tumani', -1004385365781, 'https://t.me/+CQWO9148t1JmYTli'),
    ("O'zbekiston tumani", 'Yaypan shafyorlari', -1003753262901, 'https://t.me/+ITMCH_Ch46Y4ZDli'),
]


async def seed_districts_data(session):
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
    await session.commit()
    return added_count


async def seed_groups_data(session):
    existing = await session.execute(select(DriverGroup))
    if existing.scalars().first():
        return 0
    
    all_districts = await AdminService.get_all_districts(session)
    district_map = {d.name: d.id for d in all_districts}
    
    added = 0
    for dist_name, grp_name, grp_id, inv_link in groups_mapping:
        d_id = district_map.get(dist_name)
        if d_id:
            await AdminService.add_group(
                session=session,
                district_id=d_id,
                group_name=grp_name,
                telegram_group_id=grp_id,
                invite_link=inv_link
            )
            added += 1
    await session.commit()
    return added


async def seed_settings_data(session):
    existing = await session.execute(select(Setting))
    if not existing.scalars().first():
        session.add(Setting(key="PAYMENT_CARD", value="9860554466552233"))
        session.add(Setting(key="PAYMENT_AMOUNT", value="300000"))
        session.add(Setting(key="PAYMENT_CARD_OWNER", value="Zokirov Sanjar"))
        await session.commit()


async def seed():
    async with async_session_maker() as session:
        d_count = await seed_districts_data(session)
        g_count = await seed_groups_data(session)
        await seed_settings_data(session)
        print(f"Baza to'ldirildi: {d_count} ta tuman, {g_count} ta guruh.")


if __name__ == "__main__":
    asyncio.run(seed())

