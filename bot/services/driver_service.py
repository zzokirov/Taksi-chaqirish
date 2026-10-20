"""Haydovchi bilan bog'liq database operatsiyalari."""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import Driver, User, District, DriverGroup

logger = logging.getLogger(__name__)


class DriverService:
    """Haydovchi uchun service."""

    @staticmethod
    async def create_driver(
        session: AsyncSession,
        user_id: int,
        full_name: str,
        phone: str,
        car_model: str,
        car_number: str,
        district_id: int,
    ) -> Driver:
        """Yangi haydovchi yaratish."""
        driver = Driver(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            car_model=car_model,
            car_number=car_number,
            district_id=district_id,
            status="PENDING",
            online_status="OFFLINE",
            payment_status="NONE",
        )
        session.add(driver)
        await session.flush()
        logger.info(f"Yangi haydovchi yaratildi: {full_name} (user_id={user_id})")
        return driver

    @staticmethod
    async def get_driver_by_user_id(session: AsyncSession, user_id: int) -> Optional[Driver]:
        """Haydovchini user_id bo'yicha topish."""
        stmt = (
            select(Driver)
            .options(joinedload(Driver.district))
            .where(Driver.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_driver_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[Driver]:
        """Haydovchini telegram_id bo'yicha topish."""
        stmt = (
            select(Driver)
            .join(User)
            .options(joinedload(Driver.district), joinedload(Driver.user))
            .where(User.telegram_id == telegram_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_driver_by_id(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini ID bo'yicha topish."""
        stmt = (
            select(Driver)
            .options(joinedload(Driver.district), joinedload(Driver.user))
            .where(Driver.id == driver_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def approve_driver(
        session: AsyncSession,
        driver_id: int,
        admin_id: int,
    ) -> Optional[Driver]:
        """Haydovchini tasdiqlash va obunani uzaytirish."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            from datetime import timedelta
            driver.status = "APPROVED"
            driver.payment_status = "APPROVED"
            driver.approved_at = datetime.utcnow()
            driver.approved_by = admin_id
            
            if not driver.subscription_end or driver.subscription_end < datetime.utcnow():
                driver.subscription_end = datetime.utcnow() + timedelta(days=30)
            else:
                driver.subscription_end += timedelta(days=30)
                
            from bot.database.models import Payment
            from sqlalchemy import select
            pending_payments = await session.execute(
                select(Payment).where(Payment.driver_id == driver_id, Payment.status.in_(["PENDING", "PENDING_RENEWAL"]))
            )
            for p in pending_payments.scalars().all():
                p.status = "APPROVED"
                
            await session.flush()
            logger.info(f"Haydovchi tasdiqlandi: id={driver_id}, admin={admin_id}")
        return driver

    @staticmethod
    async def reject_driver(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini rad etish."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            driver.status = "REJECTED"
            driver.payment_status = "REJECTED"
            
            from bot.database.models import Payment
            from sqlalchemy import select
            pending_payments = await session.execute(
                select(Payment).where(Payment.driver_id == driver_id, Payment.status.in_(["PENDING", "PENDING_RENEWAL"]))
            )
            for p in pending_payments.scalars().all():
                p.status = "REJECTED"
                
            await session.flush()
            logger.info(f"Haydovchi rad etildi: id={driver_id}")
        return driver

    @staticmethod
    async def block_driver(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini bloklash."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            driver.status = "BLOCKED"
            driver.online_status = "OFFLINE"
            await session.flush()
            logger.info(f"Haydovchi bloklandi: id={driver_id}")
        return driver

    @staticmethod
    async def unblock_driver(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini blokdan chiqarish."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            driver.status = "APPROVED"
            await session.flush()
            logger.info(f"Haydovchi blokdan chiqarildi: id={driver_id}")
        return driver

    @staticmethod
    async def set_online(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini onlayn qilish."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver and driver.status == "APPROVED":
            driver.online_status = "ONLINE"
            await session.flush()
        return driver

    @staticmethod
    async def set_offline(session: AsyncSession, driver_id: int) -> Optional[Driver]:
        """Haydovchini oflayn qilish."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            driver.online_status = "OFFLINE"
            await session.flush()
        return driver

    @staticmethod
    async def get_online_drivers_by_district(
        session: AsyncSession,
        district_id: int,
    ) -> List[Driver]:
        """Berilgan tumandagi ONLINE va APPROVED haydovchilarni topish."""
        stmt = (
            select(Driver)
            .options(joinedload(Driver.user))
            .where(
                Driver.district_id == district_id,
                Driver.status == "APPROVED",
                Driver.payment_status == "APPROVED",
                Driver.online_status == "ONLINE",
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_drivers_by_status(
        session: AsyncSession,
        status: str,
    ) -> List[Driver]:
        """Status bo'yicha haydovchilar."""
        if status == "PENDING" or status == "PAYMENT_PENDING":
            stmt = (
                select(Driver)
                .options(joinedload(Driver.district))
                .where(Driver.payment_status.in_(["PENDING", "PENDING_RENEWAL"]))
            )
        else:
            stmt = (
                select(Driver)
                .options(joinedload(Driver.district))
                .where(Driver.status == status)
            )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_group_for_driver(session: AsyncSession, district_id: int) -> Optional[DriverGroup]:
        """Haydovchi tumani uchun guruhni topish."""
        stmt = select(DriverGroup).where(
            DriverGroup.district_id == district_id,
            DriverGroup.status == "ACTIVE",
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_districts(session: AsyncSession) -> List[District]:
        """Barcha faol tumanlarni olish."""
        stmt = select(District).where(District.status == "ACTIVE").order_by(District.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_district_by_id(session: AsyncSession, district_id: int) -> Optional[District]:
        """Tumanni ID bo'yicha topish."""
        stmt = select(District).where(District.id == district_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def count_drivers(session: AsyncSession, status: Optional[str] = None) -> int:
        """Haydovchilar sonini olish."""
        stmt = select(func.count(Driver.id))
        if status:
            stmt = stmt.where(Driver.status == status)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_all_driver_telegram_ids(
        session: AsyncSession,
        status: Optional[str] = None,
        district_id: Optional[int] = None,
    ) -> List[int]:
        """Haydovchilar telegram_id larini olish."""
        stmt = select(User.telegram_id).join(Driver, Driver.user_id == User.id)
        if status:
            stmt = stmt.where(Driver.status == status)
        if district_id:
            stmt = stmt.where(Driver.district_id == district_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    async def get_expired_subscriptions(session: AsyncSession) -> List[Driver]:
        """Obuna muddati tugagan haydovchilarni topish."""
        stmt = (
            select(Driver)
            .options(joinedload(Driver.district), joinedload(Driver.user))
            .where(
                Driver.payment_status == "APPROVED",
                Driver.subscription_end != None,
                Driver.subscription_end < datetime.utcnow()
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_driver(session: AsyncSession, driver_id: int) -> bool:
        """Haydovchini o'chirish (registration qayta qilish uchun)."""
        driver = await DriverService.get_driver_by_id(session, driver_id)
        if driver:
            await session.delete(driver)
            await session.flush()
            return True
        return False
