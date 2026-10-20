"""Buyurtmalar bilan bog'liq database operatsiyalari."""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import Order, Driver, User, District

logger = logging.getLogger(__name__)


class OrderService:
    """Buyurtma uchun service."""

    @staticmethod
    async def create_order(
        session: AsyncSession,
        customer_id: int,
        district_id: int,
        from_address: str,
        to_address: str,
        passengers: int,
        price: Optional[str] = None,
    ) -> Order:
        """Yangi buyurtma yaratish."""
        order = Order(
            customer_id=customer_id,
            district_id=district_id,
            from_address=from_address,
            to_address=to_address,
            passengers=passengers,
            price=price,
            status="NEW",
        )
        session.add(order)
        await session.flush()
        logger.info(f"Yangi buyurtma yaratildi: id={order.id}, customer_id={customer_id}")
        return order

    @staticmethod
    async def get_order(session: AsyncSession, order_id: int) -> Optional[Order]:
        """Buyurtmani id bo'yicha olish."""
        stmt = (
            select(Order)
            .options(
                joinedload(Order.customer),
                joinedload(Order.driver).joinedload(Driver.user),
                joinedload(Order.district)
            )
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_driver_active_order(session: AsyncSession, driver_id: int) -> Optional[Order]:
        """Haydovchining faol (tugallanmagan) buyurtmasini olish."""
        stmt = (
            select(Order)
            .options(joinedload(Order.customer), joinedload(Order.district))
            .where(
                Order.driver_id == driver_id,
                Order.status.in_(["DRIVER_ACCEPTED", "DRIVER_ON_WAY", "DRIVER_ARRIVED", "TRIP_STARTED"])
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def accept_order(
        session: AsyncSession,
        order_id: int,
        driver_id: int,
    ) -> bool:
        """Haydovchi buyurtmani qabul qilishi (Race condition oldini olish uchun lock ishlatiladi)."""
        # Select for update to lock the row
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return False

        if order.status != "SEARCHING_DRIVER" and order.status != "NEW":
            return False # Boshqa haydovchi olib bo'lgan yoki bekor qilingan

        order.driver_id = driver_id
        order.status = "DRIVER_ACCEPTED"
        order.accepted_at = datetime.utcnow()
        await session.flush()
        logger.info(f"Buyurtma {order_id} haydovchi {driver_id} tomonidan qabul qilindi.")
        return True

    @staticmethod
    async def update_status(
        session: AsyncSession,
        order_id: int,
        new_status: str,
    ) -> Optional[Order]:
        """Buyurtma statusini o'zgartirish."""
        order = await OrderService.get_order(session, order_id)
        if order:
            order.status = new_status
            if new_status == "COMPLETED":
                order.completed_at = datetime.utcnow()
            await session.flush()
            logger.info(f"Buyurtma {order_id} statusi {new_status} ga o'zgardi.")
        return order

    @staticmethod
    async def cancel_order(
        session: AsyncSession,
        order_id: int,
        reason: str,
    ) -> Optional[Order]:
        """Buyurtmani bekor qilish."""
        order = await OrderService.get_order(session, order_id)
        if order:
            order.status = "CANCELLED"
            order.cancel_reason = reason
            order.cancelled_at = datetime.utcnow()
            await session.flush()
            logger.info(f"Buyurtma {order_id} bekor qilindi. Sabab: {reason}")
        return order

    @staticmethod
    async def get_driver_orders_history(session: AsyncSession, driver_id: int, limit: int = 10) -> List[Order]:
        """Haydovchi buyurtmalar tarixini olish."""
        stmt = (
            select(Order)
            .options(joinedload(Order.customer), joinedload(Order.district))
            .where(Order.driver_id == driver_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_orders(session: AsyncSession, status: Optional[str] = None) -> int:
        """Buyurtmalar sonini olish."""
        stmt = select(func.count(Order.id))
        if status:
            stmt = stmt.where(Order.status == status)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_today_stats(session: AsyncSession) -> dict:
        """Bugungi statistika."""
        today = datetime.utcnow().date()
        
        # Jami buyurtmalar
        stmt_total = select(func.count(Order.id)).where(func.date(Order.created_at) == today)
        total_res = await session.execute(stmt_total)
        total = total_res.scalar() or 0
        
        # Tugallangan
        stmt_completed = select(func.count(Order.id)).where(
            func.date(Order.created_at) == today,
            Order.status == "COMPLETED"
        )
        comp_res = await session.execute(stmt_completed)
        completed = comp_res.scalar() or 0
        
        # Bekor qilingan
        stmt_cancelled = select(func.count(Order.id)).where(
            func.date(Order.created_at) == today,
            Order.status == "CANCELLED"
        )
        canc_res = await session.execute(stmt_cancelled)
        cancelled = canc_res.scalar() or 0
        
        return {
            "total": total,
            "completed": completed,
            "cancelled": cancelled
        }
