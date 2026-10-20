"""To'lovlar bilan bog'liq database operatsiyalari."""
import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import Payment, Driver, User

logger = logging.getLogger(__name__)


class PaymentService:
    """To'lov uchun service."""

    @staticmethod
    async def create_payment(
        session: AsyncSession,
        driver_id: int,
        amount: str,
        card_number: str,
        receipt_file_id: str,
        receipt_type: str,
    ) -> Payment:
        """Yangi to'lov chekini saqlash."""
        payment = Payment(
            driver_id=driver_id,
            amount=Decimal(amount),
            card_number=card_number,
            receipt_file_id=receipt_file_id,
            receipt_type=receipt_type,
            status="PENDING",
        )
        session.add(payment)
        await session.flush()
        
        # Update driver payment status to PENDING as well
        stmt = select(Driver).where(Driver.id == driver_id)
        res = await session.execute(stmt)
        driver = res.scalar_one_or_none()
        if driver:
            driver.payment_status = "PENDING"
            
        logger.info(f"Yangi to'lov yozildi: driver_id={driver_id}, amount={amount}")
        return payment

    @staticmethod
    async def get_payment(session: AsyncSession, payment_id: int) -> Optional[Payment]:
        """To'lovni id bo'yicha topish."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.driver).joinedload(Driver.user))
            .where(Payment.id == payment_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def approve_payment(
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
    ) -> Optional[Payment]:
        """To'lovni tasdiqlash."""
        payment = await PaymentService.get_payment(session, payment_id)
        if payment:
            payment.status = "APPROVED"
            payment.approved_at = datetime.utcnow()
            payment.approved_by = admin_id
            
            # Haydovchi payment_status ni ham o'zgartiramiz
            if payment.driver:
                payment.driver.payment_status = "APPROVED"
                
            await session.flush()
            logger.info(f"To'lov tasdiqlandi: id={payment_id}, admin={admin_id}")
        return payment

    @staticmethod
    async def reject_payment(
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
    ) -> Optional[Payment]:
        """To'lovni rad etish."""
        payment = await PaymentService.get_payment(session, payment_id)
        if payment:
            payment.status = "REJECTED"
            payment.approved_at = datetime.utcnow()
            payment.approved_by = admin_id
            
            # Haydovchi payment_status ni ham o'zgartiramiz
            if payment.driver:
                payment.driver.payment_status = "REJECTED"
                
            await session.flush()
            logger.info(f"To'lov rad etildi: id={payment_id}, admin={admin_id}")
        return payment

    @staticmethod
    async def get_payments_by_status(session: AsyncSession, status: str) -> List[Payment]:
        """Status bo'yicha to'lovlarni olish."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.driver).joinedload(Driver.user))
            .where(Payment.status == status)
            .order_by(Payment.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_driver_payments(session: AsyncSession, driver_id: int, limit: int = 5) -> List[Payment]:
        """Haydovchining to'lovlari tarixini olish."""
        stmt = (
            select(Payment)
            .where(Payment.driver_id == driver_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_total_payments_amount(session: AsyncSession) -> float:
        """Barcha tasdiqlangan to'lovlar summasi."""
        stmt = select(func.sum(Payment.amount)).where(Payment.status == "APPROVED")
        result = await session.execute(stmt)
        val = result.scalar()
        return float(val) if val else 0.0
