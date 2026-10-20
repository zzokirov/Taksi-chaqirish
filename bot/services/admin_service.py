"""Admin panel va sozlamalar bilan bog'liq database operatsiyalari."""
import logging
from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import Setting, District, DriverGroup, AdminLog

logger = logging.getLogger(__name__)


class AdminService:
    """Admin uchun service."""

    @staticmethod
    async def get_setting(session: AsyncSession, key: str, default: Optional[str] = None) -> Optional[str]:
        """Sozlamani olish."""
        stmt = select(Setting).where(Setting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    @staticmethod
    async def set_setting(session: AsyncSession, key: str, value: str) -> None:
        """Sozlamani saqlash."""
        stmt = select(Setting).where(Setting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            session.add(setting)
        await session.flush()
        logger.info(f"Sozlama saqlandi: {key} = {value}")

    @staticmethod
    async def get_payment_settings(session: AsyncSession) -> Dict[str, str]:
        """To'lov sozlamalarini DB dan (yoki configdan default qilib) olish."""
        from config import settings
        card = await AdminService.get_setting(session, "PAYMENT_CARD", settings.PAYMENT_CARD)
        owner = await AdminService.get_setting(session, "PAYMENT_CARD_OWNER", settings.PAYMENT_CARD_OWNER)
        amount = await AdminService.get_setting(session, "PAYMENT_AMOUNT", settings.PAYMENT_AMOUNT)
        
        return {
            "card": card,
            "owner": owner,
            "amount": amount,
        }

    @staticmethod
    async def update_payment_settings(
        session: AsyncSession, 
        card: Optional[str] = None, 
        owner: Optional[str] = None, 
        amount: Optional[str] = None
    ) -> None:
        """To'lov sozlamalarini yangilash."""
        if card is not None:
            await AdminService.set_setting(session, "PAYMENT_CARD", card)
        if owner is not None:
            await AdminService.set_setting(session, "PAYMENT_CARD_OWNER", owner)
        if amount is not None:
            await AdminService.set_setting(session, "PAYMENT_AMOUNT", amount)
            
    @staticmethod
    async def log_action(session: AsyncSession, admin_id: int, action: str, target_id: Optional[str] = None) -> None:
        """Admin qadamlarini log qilish."""
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_id=str(target_id) if target_id else None
        )
        session.add(log)
        await session.flush()

    # --- DISTRICTS ---
    @staticmethod
    async def get_all_districts(session: AsyncSession, include_inactive: bool = False) -> List[District]:
        """Tumanlar ro'yxatini olish."""
        stmt = select(District).order_by(District.name)
        if not include_inactive:
            stmt = stmt.where(District.status == "ACTIVE")
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def add_district(session: AsyncSession, name: str) -> Optional[District]:
        """Yangi tuman qo'shish."""
        stmt = select(District).where(District.name == name)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return None # Already exists
            
        district = District(name=name, status="ACTIVE")
        session.add(district)
        await session.flush()
        return district
        
    @staticmethod
    async def get_district(session: AsyncSession, district_id: int) -> Optional[District]:
        """Tuman topish."""
        stmt = select(District).where(District.id == district_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_district_status(session: AsyncSession, district_id: int, status: str) -> bool:
        """Tuman statusini o'zgartirish."""
        district = await AdminService.get_district(session, district_id)
        if district:
            district.status = status
            await session.flush()
            return True
        return False

    @staticmethod
    async def delete_district(session: AsyncSession, district_id: int) -> bool:
        """Tumanni o'chirish."""
        district = await AdminService.get_district(session, district_id)
        if district:
            await session.delete(district)
            await session.flush()
            return True
        return False

    # --- DRIVER GROUPS ---
    @staticmethod
    async def get_all_groups(session: AsyncSession) -> List[DriverGroup]:
        """Guruhlar ro'yxati."""
        stmt = select(DriverGroup).options(joinedload(DriverGroup.district)).order_by(DriverGroup.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def add_group(
        session: AsyncSession, 
        district_id: int, 
        group_name: str, 
        telegram_group_id: Optional[int], 
        invite_link: Optional[str]
    ) -> DriverGroup:
        """Yangi guruh qo'shish."""
        group = DriverGroup(
            district_id=district_id,
            group_name=group_name,
            telegram_group_id=telegram_group_id,
            invite_link=invite_link,
            status="ACTIVE"
        )
        session.add(group)
        await session.flush()
        return group
        
    @staticmethod
    async def get_group(session: AsyncSession, group_id: int) -> Optional[DriverGroup]:
        """Guruhni topish."""
        stmt = select(DriverGroup).options(joinedload(DriverGroup.district)).where(DriverGroup.id == group_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_group(
        session: AsyncSession,
        group_id: int,
        group_name: Optional[str] = None,
        telegram_group_id: Optional[int] = None,
        invite_link: Optional[str] = None,
    ) -> bool:
        """Guruhni tahrirlash."""
        group = await AdminService.get_group(session, group_id)
        if not group:
            return False
            
        if group_name:
            group.group_name = group_name
        if telegram_group_id is not None:
            group.telegram_group_id = telegram_group_id
        if invite_link:
            group.invite_link = invite_link
            
        await session.flush()
        return True

    @staticmethod
    async def delete_group(session: AsyncSession, group_id: int) -> bool:
        """Guruhni o'chirish."""
        group = await AdminService.get_group(session, group_id)
        if group:
            await session.delete(group)
            await session.flush()
            return True
        return False
